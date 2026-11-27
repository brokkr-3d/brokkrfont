"""Slice every Brokkr Sans 3D glyph in PrusaSlicer and score the first layer.

For each weight two one-layer plates are sliced (Arachne, 0.4 mm first-layer width, 8 mm caps):
  text plate        - every glyph as a solid (the second colour)
  background plate  - a tile around every glyph with the glyph cut out (the first colour)
Toolpaths are painted into a raster per glyph and scored:
  text void   glyph area no text line covers        text spill  text lines outside the outline
  bg void     background near the glyph left empty  (narrow gaps / counters the slicer skips)
  paths       separate extrusions (fewer = fewer blobs); short = paths under 0.6 mm
usage: python -I tools/slice_test.py <family> <outdir> [Light,Regular,Bold] [chars | words:AV|To] [key=value,...]
"""
import importlib.util, json, math, os, struct, subprocess, sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
if "b3d_fontlib" not in sys.modules:               # shared loader: family from the first argument, paths
    _s = importlib.util.spec_from_file_location("b3d_fontlib", os.path.join(HERE, "fontlib.py"))
    _m = importlib.util.module_from_spec(_s); sys.modules["b3d_fontlib"] = _m; _s.loader.exec_module(_m)
FL = sys.modules["b3d_fontlib"]


G = FL.family(); RND = FL.tool("render"); geo = G.geo
PRUSA = r"C:\Program Files\Prusa3D\PrusaSlicer\prusa-slicer-console.exe"
S = G.CAP_MM / G.CAP            # mm per font unit
LAYER, MARGIN, BAND = 0.2, 2.0, 0.8   # tile margin around the ink; outer band of the tile not scored
PX = 0.03                        # analysis raster (mm per pixel)
NEAR, MIN_CLUSTER = 0.8, 0.01    # background voids counted within 0.8 mm of a glyph; clusters >= 0.01 mm2
CFG = dict(printer_technology="FFF", nozzle_diameter=0.4, filament_diameter=1.75, layer_height=LAYER,
           first_layer_height=LAYER, perimeters=2, perimeter_generator="arachne", first_layer_extrusion_width=0.4,
           extrusion_width=0.45, top_solid_layers=0, bottom_solid_layers=1, fill_density="0%", skirts=0,
           brim_width=0, temperature=215, first_layer_temperature=215, bed_temperature=60,
           first_layer_bed_temperature=60, start_gcode="M83", end_gcode="", use_relative_e_distances=1,
           bed_shape="0x0,250x0,250x250,0x250")


# ---------- geometry ----------
def cross(a, b, c):
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def clean(pts):
    out = []
    for p in pts:
        q = (round(p[0], 5), round(p[1], 5))
        if not out or q != out[-1]:
            out.append(q)
    if len(out) > 1 and out[0] == out[-1]:
        out.pop()
    i = 0
    while len(out) > 3 and i < len(out):
        if abs(cross(out[i - 1], out[i], out[(i + 1) % len(out)])) < 1e-10:
            out.pop(i); i = max(i - 1, 0)
        else:
            i += 1
    return out


def in_tri(p, a, b, c):
    return cross(a, b, p) >= -1e-12 and cross(b, c, p) >= -1e-12 and cross(c, a, p) >= -1e-12


def inside(p, poly):
    c, n = False, len(poly)
    for i in range(n):
        (x0, y0), (x1, y1) = poly[i], poly[i - 1]
        if (y0 > p[1]) != (y1 > p[1]) and p[0] < x0 + (p[1] - y0) * (x1 - x0) / (y1 - y0):
            c = not c
    return c


def bridge(outer, hole):
    mi = max(range(len(hole)), key=lambda i: hole[i][0]); mx, my = hole[mi]
    best, n = None, len(outer)
    for i in range(n):
        a, b = outer[i], outer[(i + 1) % n]
        if a[1] == b[1] or not (min(a[1], b[1]) <= my <= max(a[1], b[1])):
            continue
        t = (my - a[1]) / (b[1] - a[1]); x = a[0] + t * (b[0] - a[0])
        if x <= mx or (best and x >= best[0]):
            continue
        best = (x, i if t == 0 else (i + 1) % n if t == 1 else (i if a[0] > b[0] else (i + 1) % n), t in (0, 1))
    x, pi, exact = best
    if not exact:
        M, I, P = (mx, my), (x, my), outer[pi]; cand = []
        for j in range(n):
            p = outer[j]
            if j != pi and cross(outer[j - 1], p, outer[(j + 1) % n]) <= 0 and \
                    (in_tri(p, M, I, P) if cross(M, I, P) > 0 else in_tri(p, M, P, I)):
                cand.append((abs(math.atan2(p[1] - my, p[0] - mx)), (p[0] - mx) ** 2 + (p[1] - my) ** 2, j))
        if cand:
            pi = min(cand)[2]
    return outer[:pi + 1] + hole[mi:] + hole[:mi + 1] + [outer[pi]] + outer[pi + 1:]


def earclip(poly):
    n = len(poly)
    prv = [(i - 1) % n for i in range(n)]; nxt = [(i + 1) % n for i in range(n)]
    cv = lambda i: cross(poly[prv[i]], poly[i], poly[nxt[i]]) > 1e-12
    reflex = {i for i in range(n) if not cv(i)}
    tris, left, i, miss = [], n, 0, 0
    while left > 3:
        p, q = prv[i], nxt[i]
        ok = i not in reflex
        if ok:
            a, b, c = poly[p], poly[i], poly[q]
            for j in reflex:
                if j not in (p, i, q) and poly[j] not in (a, b, c) and in_tri(poly[j], a, b, c):
                    ok = False; break
        if ok or miss > left:                      # clip an ear (or, if stuck, a degenerate corner)
            if ok:
                tris.append((poly[p], poly[i], poly[q]))
            nxt[p], prv[q] = q, p; left -= 1; reflex.discard(i)
            for k in (p, q):
                if k in reflex and cv(k):
                    reflex.discard(k)
            i, miss = q, 0
        else:
            i, miss = nxt[i], miss + 1
    tris.append((poly[prv[i]], poly[i], poly[nxt[i]]))
    return tris


def regions(contours):
    """Group contours (material on the left) into (outer, [holes]) by nesting."""
    outs = [c for c in contours if geo.area(c) > 0]; holes = [c for c in contours if geo.area(c) <= 0]
    res = []
    for o in outs:
        mine = [h for h in holes if inside(h[0], o) and not any(o2 is not o and inside(h[0], o2) and inside(o2[0], o) for o2 in outs)]
        res.append((o, mine))
    return res


def solid_tris(outer, holes):
    tris = []
    poly = outer
    for h in sorted(holes, key=lambda h: -max(p[0] for p in h)):
        poly = bridge(poly, h)
    for a, b, c in earclip(poly):
        tris += [((*a, LAYER), (*b, LAYER), (*c, LAYER)), ((*a, 0.0), (*c, 0.0), (*b, 0.0))]
    for cont in [outer] + holes:
        for k in range(len(cont)):
            a, b = cont[k], cont[(k + 1) % len(cont)]
            tris += [((*a, 0.0), (*b, 0.0), (*b, LAYER)), ((*a, 0.0), (*b, LAYER), (*a, LAYER))]
    return tris


def write_stl(path, tris):
    with open(path, "wb") as f:
        f.write(b"\0" * 80 + struct.pack("<I", len(tris)))
        for a, b, c in tris:
            f.write(struct.pack("<12fH", 0, 0, 0, *a, *b, *c, 0))


# ---------- layout ----------
def plate(font, chars):
    """Place glyph tiles on a grid. Returns list of cells: char, ox, oy (glyph origin, mm), tile box, contours (mm)."""
    cells, inks = [], []
    for c in chars:
        gl = font[c]
        cs = [clean([(x * S, y * S) for x, y in geo.flatten(ct, 6)]) for ct in gl["contours"]]
        xs = [p[0] for ct in cs for p in ct]; ys = [p[1] for ct in cs for p in ct]
        inks.append((c, cs, min(xs), max(xs), min(ys), max(ys)))
    CW = max(i[3] - i[2] for i in inks) + 2 * MARGIN + 1.5
    CH = max(i[5] - i[4] for i in inks) + 2 * MARGIN + 1.5
    cols = max(1, int(230 // CW))
    for k, (c, cs, x0, x1, y0, y1) in enumerate(inks):
        cx, cy = 10 + (k % cols) * CW, 240 - (k // cols + 1) * CH
        ox, oy = cx + (CW - (x1 - x0)) / 2 - x0, cy + (CH - (y1 - y0)) / 2 - y0
        mm = [[(x + ox, y + oy) for x, y in ct] for ct in cs]
        tile = (x0 + ox - MARGIN, y0 + oy - MARGIN, x1 + ox + MARGIN, y1 + oy + MARGIN)
        cells.append(dict(char=c, contours=mm, tile=tile))
    return cells


# ---------- slicing ----------
def slice_stl(stl, gcode, ini):
    r = subprocess.run([PRUSA, "--export-gcode", "--load", ini, "--dont-arrange", "--output", gcode, stl],
                       capture_output=True, text=True)
    if r.returncode != 0 or not os.path.exists(gcode):
        raise RuntimeError(f"slicing failed: {r.stdout[-600:]} {r.stderr[-600:]}")


def parse_gcode(path):
    x = y = 0.0; typ = wid = None; segs = []; pid = 0; extr = False
    for line in open(path):
        if line.startswith(";TYPE:"): typ = line[6:].strip(); continue
        if line.startswith(";WIDTH:"): wid = float(line[7:]); continue
        code = line.split(";")[0].split()
        if not code or code[0] not in ("G0", "G1"):
            continue
        d = {t[0]: float(t[1:]) for t in code[1:] if t[0] in "XYZE"}
        nx, ny = d.get("X", x), d.get("Y", y)
        if (nx, ny) != (x, y) and d.get("E", 0) > 0:
            if not extr: pid += 1
            segs.append((x, y, nx, ny, typ, wid, pid)); extr = True
        elif (nx, ny) != (x, y):
            extr = False
        x, y = nx, ny
    return segs


# ---------- raster scoring ----------
class Grid:
    def __init__(self, box):
        self.x0, self.y0 = box[0], box[1]
        self.W, self.H = int((box[2] - box[0]) / PX) + 1, int((box[3] - box[1]) / PX) + 1

    def fill(self, polys):
        m = bytearray(self.W * self.H)
        for r in range(self.H):
            y = self.y0 + (r + 0.5) * PX; xs = []
            for poly in polys:
                n = len(poly)
                for i in range(n):
                    (xa, ya), (xb, yb) = poly[i], poly[i - 1]
                    if (ya > y) != (yb > y):
                        xs.append(xa + (y - ya) * (xb - xa) / (yb - ya))
            xs.sort()
            for a, b in zip(xs[0::2], xs[1::2]):
                i0 = max(0, int(math.ceil((a - self.x0) / PX - 0.5))); i1 = min(self.W - 1, int(math.floor((b - self.x0) / PX - 0.5)))
                if i1 >= i0:
                    m[r * self.W + i0:r * self.W + i1 + 1] = b"\x01" * (i1 - i0 + 1)
        return m

    def paint(self, segs, m):
        for s in segs:
            r = s[5] / 2; ax, ay, bx, by = s[0], s[1], s[2], s[3]
            dx, dy = bx - ax, by - ay; L2 = dx * dx + dy * dy
            c0 = max(0, int((min(ax, bx) - r - self.x0) / PX)); c1 = min(self.W - 1, int((max(ax, bx) + r - self.x0) / PX) + 1)
            r0 = max(0, int((min(ay, by) - r - self.y0) / PX)); r1 = min(self.H - 1, int((max(ay, by) + r - self.y0) / PX) + 1)
            for row in range(r0, r1 + 1):
                py = self.y0 + (row + 0.5) * PX; base = row * self.W
                for col in range(c0, c1 + 1):
                    px = self.x0 + (col + 0.5) * PX
                    t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / L2))
                    ex, ey = px - ax - t * dx, py - ay - t * dy
                    if ex * ex + ey * ey <= r * r:
                        m[base + col] = 1

    def erode(self, m):
        W, out = self.W, bytearray(m)
        for i in range(W, len(m) - W):
            if m[i] and not (m[i - 1] and m[i + 1] and m[i - W] and m[i + W]):
                out[i] = 0
        return out


def score(cell, tsegs, bsegs):
    tb = cell["tile"]; g = Grid(tb)
    glyph = g.fill(cell["contours"])
    inner = Grid((tb[0] + BAND, tb[1] + BAND, tb[2] - BAND, tb[3] - BAND))   # region scored for the background
    tcov = bytearray(len(glyph)); bcov = bytearray(len(glyph))
    g.paint(tsegs, tcov); g.paint(bsegs, bcov)
    ge, be = g.erode(glyph), g.erode(bytearray(1 - v for v in glyph))
    a = PX * PX
    ci0, ci1 = int(BAND / PX), g.W - int(BAND / PX)
    ri0, ri1 = int(BAND / PX), g.H - int(BAND / PX)
    tvoid = tspill = bvoid = bspill = 0; tv_pts, bv_pts = [], []
    for row in range(g.H):
        for col in range(g.W):
            i = row * g.W + col
            if ge[i] and not tcov[i]:
                tvoid += 1; tv_pts.append(i)
            if tcov[i] and be[i]:
                tspill += 1
            if ri0 <= row < ri1 and ci0 <= col < ci1:
                if be[i] and not bcov[i]:
                    bvoid += 1; bv_pts.append(i)
                if ge[i] and bcov[i]:
                    bspill += 1
    # keep only void clusters that matter: >= MIN_CLUSTER, and (background) within NEAR mm of the glyph
    edge = defaultdict(list)
    for ct in cell["contours"]:
        for x, y in ct:
            edge[(int(x / NEAR), int(y / NEAR))].append((x, y))

    def near(i):
        row, col = divmod(i, g.W); x, y = g.x0 + (col + 0.5) * PX, g.y0 + (row + 0.5) * PX
        kx, ky = int(x / NEAR), int(y / NEAR)
        return any(math.hypot(x - ex, y - ey) <= NEAR for dx in (-1, 0, 1) for dy in (-1, 0, 1)
                   for ex, ey in edge.get((kx + dx, ky + dy), ()))

    def clusters(pts):
        left, out = set(pts), []
        while left:
            stack = [left.pop()]; comp = []
            while stack:
                i = stack.pop(); comp.append(i)
                for j in (i - 1, i + 1, i - g.W, i + g.W, i - g.W - 1, i - g.W + 1, i + g.W - 1, i + g.W + 1):
                    if j in left:
                        left.discard(j); stack.append(j)
            if len(comp) * a >= MIN_CLUSTER:
                out.append(comp)
        return out
    tcl = clusters(tv_pts)
    bcl = clusters([i for i in bv_pts if near(i)])
    tvoid = sum(len(c) for c in tcl); bvoid = sum(len(c) for c in bcl)
    tv_pts = [i for c in tcl for i in c]; bv_pts = [i for c in bcl for i in c]
    paths = {s[6] for s in tsegs}
    plen = defaultdict(float)
    for s in tsegs:
        plen[s[6]] += math.dist(s[:2], s[2:4])
    widths = sorted(s[5] for s in tsegs) or [0]
    comps = regions(cell["contours"])
    dropped = sum(1 for o, hs in comps if not any(inside(((s[0] + s[2]) / 2, (s[1] + s[3]) / 2), o) for s in tsegs))
    return dict(text_void=round(tvoid * a, 3), text_spill=round(tspill * a, 3), bg_void=round(bvoid * a, 3),
                bg_spill=round(bspill * a, 3), tv_n=len(tcl), bv_n=len(bcl),
                paths=len(paths), short=sum(1 for v in plen.values() if v < 0.6),
                gapfill=round(sum(math.dist(s[:2], s[2:4]) for s in tsegs if s[4] == "Gap fill"), 2),
                wmin=widths[0], wmax=widths[-1], dropped=dropped,
                _g=g, _glyph=glyph, _tcov=tcov, _bcov=bcov, _tv=tv_pts, _bv=bv_pts)


def cell_png(res, tsegs):
    """RGB tile at analysis resolution: grey text area, orange text lines, blue background lines, red/magenta voids."""
    g = res["_g"]; cv = RND.Canvas(g.W, g.H)
    gl, tc, bc = res["_glyph"], res["_tcov"], res["_bcov"]
    for row in range(g.H):
        for col in range(g.W):
            i = row * g.W + col; j = (g.H - 1 - row) * g.W + col
            if gl[i]:
                col_ = (235, 150, 60) if tc[i] else (230, 0, 0)
            else:
                col_ = (250, 200, 90) if tc[i] else (170, 205, 245) if bc[i] else (255, 255, 255)
            cv.px[j * 3:j * 3 + 3] = bytes(col_)
    for i in res["_bv"]:
        row, col = divmod(i, g.W); j = (g.H - 1 - row) * g.W + col
        cv.px[j * 3:j * 3 + 3] = bytes((210, 0, 210))
    for s in tsegs:                                    # nozzle centrelines
        n = max(2, int(math.dist(s[:2], s[2:4]) / PX))
        for k in range(n + 1):
            x = s[0] + (s[2] - s[0]) * k / n; y = s[1] + (s[3] - s[1]) * k / n
            col, row = int((x - g.x0) / PX), int((y - g.y0) / PX)
            if 0 <= col < g.W and 0 <= row < g.H:
                j = (g.H - 1 - row) * g.W + col; cv.px[j * 3:j * 3 + 3] = b"\x40\x20\x00"
    return cv


def word_font(wname, words):
    """Pseudo-font where each 'glyph' is a whole kerned word (to test the gaps between letters)."""
    font = G.build(G.WEIGHTS[wname])
    out = {}
    for wd in words:
        placed, adv = G.layout(font, wd)
        cs = []
        for x, gl in placed:
            for start, segs in gl["contours"]:
                sh = lambda p: (p[0] + x, p[1])
                cs.append((sh(start), [(sg[0],) + tuple(sh(p) for p in sg[1:]) for sg in segs]))
        out[wd] = dict(contours=cs, adv=adv)
    return out


def run(out, wname, chars):
    os.makedirs(out, exist_ok=True)
    if isinstance(chars, list):                         # kerned words
        font = word_font(wname, chars)
    else:
        font = G.build(G.WEIGHTS[wname], set(chars))
    cells = plate(font, chars)
    ttris, btris = [], []
    for cell in cells:
        regs = regions(cell["contours"])
        for o, hs in regs:
            ttris += solid_tris(o, hs)
        x0, y0, x1, y1 = cell["tile"]
        tile = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
        outers = [o for o, hs in regs]
        btris += solid_tris(tile, [o[::-1] for o in outers])
        for o, hs in regs:
            for h in hs:
                inner_outs = [o2 for o2 in outers if o2 is not o and inside(o2[0], h)]
                btris += solid_tris(h[::-1], [o2[::-1] for o2 in inner_outs])
    ini = os.path.join(out, "arachne_0.40.ini")
    with open(ini, "w") as fh:
        fh.writelines(f"{k} = {v}\n" for k, v in CFG.items())
    res = {}
    for kind, tris in (("text", ttris), ("bg", btris)):
        # analysis-only G-code: bare profile with no homing or heating - never send it to a printer
        stl = os.path.join(out, f"{wname}-{kind}.stl")
        gc = os.path.join(out, f"{wname}-{kind}.ANALYSIS-ONLY-do-not-print.gcode")
        write_stl(stl, tris); slice_stl(stl, gc, ini)
        res[kind] = parse_gcode(gc)
    per_t, per_b = defaultdict(list), defaultdict(list)
    for kind, per in (("text", per_t), ("bg", per_b)):
        for s in res[kind]:
            mx, my = (s[0] + s[2]) / 2, (s[1] + s[3]) / 2
            for k, cell in enumerate(cells):
                x0, y0, x1, y1 = cell["tile"]
                if x0 <= mx <= x1 and y0 <= my <= y1:
                    per[k].append(s); break
    report, tiles = {}, []
    for k, cell in enumerate(cells):
        r = score(cell, per_t[k], per_b[k])
        tiles.append((cell["char"], cell_png(r, per_t[k])))
        report[cell["char"]] = {kk: v for kk, v in r.items() if not kk.startswith("_")}
    # contact sheet
    cw = max(t.W for _, t in tiles); ch = max(t.H for _, t in tiles); cols = 10
    sheet = RND.Canvas(cols * cw, ((len(tiles) + cols - 1) // cols) * ch)
    for k, (c, t) in enumerate(tiles):
        ox, oy = (k % cols) * cw, (k // cols) * ch
        for row in range(t.H):
            j = ((oy + row) * sheet.W + ox) * 3
            sheet.px[j:j + t.W * 3] = t.px[row * t.W * 3:(row + 1) * t.W * 3]
    sheet.save(os.path.join(out, f"toolpaths-{wname}.png"))
    json.dump(report, open(os.path.join(out, f"report-{wname}.json"), "w"), indent=1)
    return report


if __name__ == "__main__":
    out = sys.argv[1]
    weights = sys.argv[2].split(",") if len(sys.argv) > 2 and sys.argv[2] else list(G.WEIGHTS)
    chars = sys.argv[3] if len(sys.argv) > 3 and sys.argv[3] else "".join(c for c in G.REGISTRY)
    if chars.startswith("words:"):                         # words:AVATAR|Today|P.F.
        chars = chars[6:].split("|")
    if len(sys.argv) > 4:                                  # slicer overrides: key=value,key=value
        CFG.update(kv.split("=", 1) for kv in sys.argv[4].split(","))
    for wname in weights:
        rep = run(out, wname, chars)
        tot = {k: round(sum(r[k] for r in rep.values()), 2) for k in ("text_void", "text_spill", "bg_void", "bg_spill", "paths", "short", "gapfill", "dropped")}
        print(f"== {wname}: {tot}")
        worst = sorted(rep.items(), key=lambda kv: -(kv[1]["text_void"] + kv[1]["bg_void"] + kv[1]["text_spill"]))[:12]
        for c, r in worst:
            print(f"   {c!r:5} tv {r['text_void']:.3f} ts {r['text_spill']:.3f} bv {r['bg_void']:.3f} bs {r['bg_spill']:.3f} "
                  f"paths {r['paths']} short {r['short']} gap {r['gapfill']} w {r['wmin']}-{r['wmax']} dropped {r['dropped']}")
