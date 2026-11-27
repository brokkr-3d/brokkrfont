"""Pure-Python PNG renderer for Brokkr Sans 3D specimens (no external packages).

python -I tools/render.py <family> [Light|Regular|Bold|kern]   -> specimens/<family>/*.png
"""
import importlib.util, math, os, struct, sys, zlib

HERE = os.path.dirname(os.path.abspath(__file__))
if "b3d_fontlib" not in sys.modules:               # shared loader: family from the first argument, paths
    _s = importlib.util.spec_from_file_location("b3d_fontlib", os.path.join(HERE, "fontlib.py"))
    _m = importlib.util.module_from_spec(_s); sys.modules["b3d_fontlib"] = _m; _s.loader.exec_module(_m)
FL = sys.modules["b3d_fontlib"]


class Canvas:
    def __init__(self, W, H, bg=(255, 255, 255)):
        self.W, self.H = W, H
        self.px = bytearray(bytes(bg) * (W * H))

    def fill(self, polys, color, alpha=1.0, S=4):
        """Even-odd anti-aliased fill of polygons given in pixel coordinates."""
        edges, rows = [], {}
        for poly in polys:
            n = len(poly)
            for i in range(n):
                (x0, y0), (x1, y1) = poly[i], poly[(i + 1) % n]
                if y0 == y1:
                    continue
                k = len(edges); edges.append((x0, y0, x1, y1))
                for r in range(max(0, int(min(y0, y1))), min(self.H - 1, int(max(y0, y1))) + 1):
                    rows.setdefault(r, []).append(k)
        for r, eidx in rows.items():
            cov = {}
            for s in range(S):
                y = r + (s + 0.5) / S
                xs = []
                for k in eidx:
                    x0, y0, x1, y1 = edges[k]
                    if (y0 <= y < y1) or (y1 <= y < y0):
                        xs.append(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
                xs.sort()
                for a, b in zip(xs[0::2], xs[1::2]):
                    a, b = max(a, 0.0), min(b, self.W - 1e-6)
                    if b <= a:
                        continue
                    ia, ib = int(a), int(b)
                    if ia == ib:
                        cov[ia] = cov.get(ia, 0) + (b - a) / S
                    else:
                        cov[ia] = cov.get(ia, 0) + (ia + 1 - a) / S
                        for i in range(ia + 1, ib):
                            cov[i] = cov.get(i, 0) + 1 / S
                        cov[ib] = cov.get(ib, 0) + (b - ib) / S
            base = r * self.W
            for i, c in cov.items():
                self._blend(base + i, color, min(1.0, c) * alpha)

    def _blend(self, i, color, a):
        j = i * 3; p = self.px
        p[j] = int(p[j] + (color[0] - p[j]) * a)
        p[j + 1] = int(p[j + 1] + (color[1] - p[j + 1]) * a)
        p[j + 2] = int(p[j + 2] + (color[2] - p[j + 2]) * a)

    def capsule(self, x0, y0, x1, y1, rad, color, alpha=1.0):
        """Thick line with round caps (used for toolpaths)."""
        dx, dy = x1 - x0, y1 - y0; L2 = dx * dx + dy * dy
        for py in range(max(0, int(min(y0, y1) - rad)), min(self.H, int(max(y0, y1) + rad) + 2)):
            for px in range(max(0, int(min(x0, x1) - rad)), min(self.W, int(max(x0, x1) + rad) + 2)):
                cx, cy = px + 0.5, py + 0.5
                t = 0 if L2 == 0 else max(0.0, min(1.0, ((cx - x0) * dx + (cy - y0) * dy) / L2))
                d = math.hypot(cx - x0 - t * dx, cy - y0 - t * dy)
                if d <= rad + 0.5:
                    self._blend(py * self.W + px, color, alpha * min(1.0, rad + 0.5 - d))

    def hline(self, x0, x1, y, color, alpha=1.0):
        y = int(y)
        if 0 <= y < self.H:
            for x in range(max(0, int(x0)), min(self.W, int(x1))):
                self._blend(y * self.W + x, color, alpha)

    def save(self, path):
        raw = b"".join(b"\x00" + bytes(self.px[r * self.W * 3:(r + 1) * self.W * 3]) for r in range(self.H))
        def chunk(t, d):
            c = struct.pack(">I", len(d)) + t + d
            return c + struct.pack(">I", zlib.crc32(t + d) & 0xffffffff)
        with open(path, "wb") as f:
            f.write(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", self.W, self.H, 8, 2, 0, 0, 0))
                    + chunk(b"IDAT", zlib.compress(raw, 6)) + chunk(b"IEND", b""))


def glyph_polys(geo, gl, ox, base, s):
    """Flattened glyph contours in pixel space (font units * s, y down)."""
    return [[(ox + x * s, base - y * s) for x, y in geo.flatten(c, 10)] for c in gl["contours"]]


def draw_text(cv, G, font, text, ox, base, s, color=(20, 20, 20), kerning=True):
    placed, adv = G.layout(font, text, kerning)
    polys = []
    for x, gl in placed:
        polys += glyph_polys(G.geo, gl, ox + x * s, base, s)
    if polys:
        cv.fill(polys, color)
    return adv * s


def glyph_grid(G, font, wname, path, per_row=12, cap_px=110):
    s = cap_px / G.CAP
    cell_w, cell_h = int(950 * s), int((G.ASC - G.DESC + 260) * s)
    chars = [c for c in font if c != " "]
    rows = (len(chars) + per_row - 1) // per_row
    cv = Canvas(per_row * cell_w + 40, rows * cell_h + 90)
    lab = Canvas  # noqa
    small = G.build(G.WEIGHTS["Regular"])
    draw_text(cv, G, small, f"{G.FAMILY} {wname}", 20, 50, 34 / G.CAP)
    for i, c in enumerate(chars):
        gl = font[c]
        cx, top = 20 + (i % per_row) * cell_w, 90 + (i // per_row) * cell_h
        base = top + (G.ASC + 80) * s
        for y, col in ((0, (74, 144, 217)), (G.CAP, (215, 215, 215)), (G.XH, (215, 215, 215)),
                       (G.DESC, (230, 230, 230)), (G.ASC, (235, 235, 235))):
            cv.hline(cx + 6, cx + cell_w - 6, base - y * s, col)
        ox = cx + (cell_w - gl["adv"] * s) / 2
        for xx in (ox, ox + gl["adv"] * s):   # advance box
            for yy in range(int(base - G.ASC * s), int(base - G.DESC * s), 4):
                if 0 <= int(xx) < cv.W:
                    cv._blend(yy * cv.W + int(xx), (255, 80, 200), 0.6)
        cv.fill(glyph_polys(G.geo, gl, ox, base, s), (17, 17, 17))
    cv.save(path)


SAMPLES = ["HAMBURGEFONTSIV  Hamburgefontsiv",
           "The quick brown fox jumps over the lazy dog",
           "SPHINX OF BLACK QUARTZ, JUDGE MY VOW",
           "0123456789  12:30  3.14  -42%  #7  (a+b)=c",
           "Hello, world! What? \"quote\" 'it's' a/b & c@d",
           "nnonnoonnn HHOHHOOHH  lIl1|  O0 S5 Z2 B8",
           "minimum illumination  AVAWATAYLTVT  [x] {y} <z> ~^`*_\\$",
           "Blåbærsyltetøy  ÆRLIG ØL PÅ BRYGGA  Øystein Åse Ærø"]


def text_sheet(G, path, cap_px=46):
    s = cap_px / G.CAP
    lh = int((G.ASC - G.DESC + 120) * s)
    cv = Canvas(int(52 * cap_px * 1.0) + 60, 3 * (len(SAMPLES) * lh + 70) + 40)
    y = 30
    for wname, w in G.WEIGHTS.items():
        font = G.build(w)
        draw_text(cv, G, font, wname, 20, y + 34, 30 / G.CAP, (200, 60, 60))
        y += 50
        for line in SAMPLES:
            draw_text(cv, G, font, line, 20, y + G.ASC * s, s)
            y += lh
        y += 20
    cv.save(path)


KERN_SAMPLES = ["AVATAR WAVE TYPE LT. AWAY VAULT",
                 "Today Victory Yearly Tower Fly Lotto",
                 "P. F. T. V, Y. r. y, 'A' \"V\" L' T-",
                 "Typography: Wave, Yacht, Kayak, Fjord"]


def kern_sheet(G, path, cap_px=44):
    """Each sample twice: grey = no kerning, black = kerned."""
    s = cap_px / G.CAP
    lh = int((G.ASC - G.DESC + 60) * s)
    cv = Canvas(int(40 * cap_px) + 60, 3 * (len(KERN_SAMPLES) * 2 * lh + 70) + 20)
    y = 20
    for wname, w in G.WEIGHTS.items():
        font = G.build(w)
        draw_text(cv, G, font, f"{wname}: grey unkerned, black kerned", 20, y + 30, 26 / G.CAP, (200, 60, 60))
        y += 46
        for line in KERN_SAMPLES:
            draw_text(cv, G, font, line, 20, y + G.ASC * s, s, (175, 175, 175), kerning=False)
            y += lh
            draw_text(cv, G, font, line, 20, y + G.ASC * s, s)
            y += lh
        y += 24
    cv.save(path)


if __name__ == "__main__":
    G = FL.family(); out = FL.out("specimens", FL.SLUG)
    only = sys.argv[1] if len(sys.argv) > 1 else None
    if only == "kern":
        kern_sheet(G, os.path.join(out, "specimen-kerning.png")); print("done"); sys.exit()
    for wname, w in G.WEIGHTS.items():
        if only and only != wname:
            continue
        glyph_grid(G, G.build(w), wname, os.path.join(out, f"specimen-glyphs-{wname}.png"))
    if not only:
        text_sheet(G, os.path.join(out, "specimen-text.png"))
    print("done")
