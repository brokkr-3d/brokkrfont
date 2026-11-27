# Copyright 2026 Brokkr 3D AS (https://brokkr.design).
# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. If a copy of the MPL
# was not distributed with this file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Brokkr Sans 3D test plate for a two-colour first-layer print.

python -I tools/make_testprint.py <family> [outdir] [--verify]     (default: testprint/<family>/)

Writes
  brokkr_sans_3d_test_base.stl   plate, colour 1 (rounded rectangle, PLATE_T thick)
  brokkr_sans_3d_test_text.stl   text, colour 2, 0.2 mm thick at the bottom (overlaps the plate's first layer)
  brokkr_sans_3d_test.3mf        PrusaSlicer project: one object, base = extruder 1, text = extruder 2
  testplate-preview.png    what the face of the print should look like
Print it face down: the text is in the layer that touches the bed.
"""
import importlib.util, math, os, sys, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
if "b3d_fontlib" not in sys.modules:               # shared loader: family from the first argument, paths
    _s = importlib.util.spec_from_file_location("b3d_fontlib", os.path.join(HERE, "fontlib.py"))
    _m = importlib.util.module_from_spec(_s); sys.modules["b3d_fontlib"] = _m; _s.loader.exec_module(_m)
FL = sys.modules["b3d_fontlib"]


ST = FL.tool("slice_test"); G = ST.G; RND = ST.RND
TEST = f"brokkr_{G.SLUG}_3d_test"                      # file name stem
TEXT_T, PLATE_T, MARGIN, GAP, CORNER = 0.2, 1.2, 7.0, 2.6, 4.0
LINES = [  # weight, cap height (mm), text
    ("Regular", 8, f"{G.FAMILY} Regular"),
    ("Light", 8, "Light 8 mm ÆØÅ æøå"),
    ("Bold", 8, "Bold 8 mm AVATAR P.F.T."),
    ("Regular", 8, "0123456789 #+ (a=b)"),
    ("Regular", 8, "lIl1| O0 S5 B8 &@%"),
    ("Regular", 6, "6 mm: Blåbærsyltetøy ft4 i.j:;!?"),
    ("Bold", 5, "Bold 5 mm: The quick brown fox"),
    ("Regular", 4, "Regular 4 mm (0.4 mm lines) Hamburgefontsiv"),
    ("Bold", 3, "Bold 3 mm (0.45 mm lines) 0123456789 Hamburgefontsiv"),
]


def layout_plate():
    """Returns plate size and glyph outlines in mm: [(line_no, char, [contour polylines])]."""
    fonts = {wn: G.build(w) for wn, w in G.WEIGHTS.items()}
    rows, widths = [], []
    for wn, cap, text in LINES:
        s = cap / G.CAP
        placed, adv = G.layout(fonts[wn], text)
        glyphs = []
        for x, gl in placed:
            if gl["contours"]:
                cs = [ST.clean([((px + x) * s, py * s) for px, py in G.geo.flatten(c, 6)]) for c in gl["contours"]]
                glyphs.append(cs)
        ys = [p[1] for g in glyphs for c in g for p in c]
        rows.append((glyphs, min(ys), max(ys)))
        widths.append(adv * s)
    W = max(widths) + 2 * MARGIN
    y, placed = MARGIN, []
    for (glyphs, y0, y1), (wn, cap, text) in zip(reversed(rows), reversed(LINES)):
        base = y - y0                                   # bottom line first
        for g in glyphs:
            placed.append([[(px + MARGIN, py + base) for px, py in c] for c in g])
        y = base + y1 + GAP
    H = y - GAP + MARGIN
    return W, H, placed


def rounded_rect(W, H, r, n=8):
    pts = []
    for cx, cy, a0 in ((W - r, r, -90), (W - r, H - r, 0), (r, H - r, 90), (r, r, 180)):
        for i in range(n + 1):
            a = math.radians(a0 + 90 * i / n)
            pts.append((round(cx + r * math.cos(a), 5), round(cy + r * math.sin(a), 5)))
    return pts


def prism(outer, holes, z0, z1):
    """Triangles of a straight prism (outer + holes) from z0 to z1."""
    tris = []
    for (a, b, c) in ST.solid_tris(outer, holes):                 # ST builds 0..LAYER; rescale z
        tris.append(tuple((p[0], p[1], z0 if p[2] == 0 else z1) for p in (a, b, c)))
    return tris


def write_3mf(path, volumes, offset):
    """PrusaSlicer 3MF: one object, one volume per (name, extruder, triangles)."""
    verts, vidx, tris, ranges = [], {}, [], []
    for name, ext, ts in volumes:
        first = len(tris)
        for t in ts:
            ids = []
            for p in t:
                k = (name, round(p[0], 5), round(p[1], 5), round(p[2], 5))
                if k not in vidx:
                    vidx[k] = len(verts); verts.append(k[1:])
                ids.append(vidx[k])
            tris.append(ids)
        ranges.append((name, ext, first, len(tris) - 1))
    model = ['<?xml version="1.0" encoding="UTF-8"?>\n<model unit="millimeter" xml:lang="en-US" '
             'xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02" '
             'xmlns:slic3rpe="http://schemas.slic3r.org/3mf/2017/06">\n'
             '<metadata name="slic3rpe:Version3mf">1</metadata>\n<resources>\n<object id="1" type="model">\n<mesh>\n<vertices>\n']
    model += [f'<vertex x="{x:.5f}" y="{y:.5f}" z="{z:.5f}"/>\n' for x, y, z in verts]
    model.append("</vertices>\n<triangles>\n")
    model += [f'<triangle v1="{a}" v2="{b}" v3="{c}"/>\n' for a, b, c in tris]
    model.append(f'</triangles>\n</mesh>\n</object>\n</resources>\n<build>\n<item objectid="1" '
                 f'transform="1 0 0 0 1 0 0 0 1 {offset[0]:.3f} {offset[1]:.3f} 0" printable="1"/>\n</build>\n</model>\n')
    cfg = ['<?xml version="1.0" encoding="UTF-8"?>\n<config>\n<object id="1" instances_count="1">\n'
           f'<metadata type="object" key="name" value="{G.FAMILY} test plate"/>\n']
    for name, ext, a, b in ranges:
        cfg.append(f'<volume firstid="{a}" lastid="{b}">\n<metadata type="volume" key="name" value="{name}"/>\n'
                   f'<metadata type="volume" key="volume_type" value="ModelPart"/>\n'
                   f'<metadata type="volume" key="extruder" value="{ext}"/>\n</volume>\n')
    cfg.append("</object>\n</config>\n")
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", '<?xml version="1.0" encoding="UTF-8"?>\n<Types xmlns="http://schemas.'
                   'openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/'
                   'vnd.openxmlformats-package.relationships+xml"/><Default Extension="model" ContentType="application/'
                   'vnd.ms-package.3dmanufacturing-3dmodel+xml"/><Default Extension="config" ContentType="text/plain"/></Types>')
        z.writestr("_rels/.rels", '<?xml version="1.0" encoding="UTF-8"?>\n<Relationships xmlns="http://schemas.'
                   'openxmlformats.org/package/2006/relationships"><Relationship Target="/3D/3dmodel.model" Id="rel-1" '
                   'Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>')
        z.writestr("3D/3dmodel.model", "".join(model))
        z.writestr("Metadata/Slic3r_PE_model.config", "".join(cfg))


def preview(path, W, H, glyphs, px_mm=8):
    cv = RND.Canvas(int(W * px_mm) + 20, int(H * px_mm) + 20, bg=(255, 255, 255))
    t = lambda p: (10 + p[0] * px_mm, 10 + (H - p[1]) * px_mm)
    cv.fill([[t(p) for p in rounded_rect(W, H, CORNER)]], (236, 232, 222))
    cv.fill([[t(p) for p in c] for g in glyphs for c in g], (25, 25, 25))
    cv.save(path)


def main(out):
    os.makedirs(out, exist_ok=True)
    W, H, glyphs = layout_plate()
    base = prism(rounded_rect(W, H, CORNER), [], 0.0, PLATE_T)
    text = []
    for g in glyphs:
        for o, hs in ST.regions(g):
            text += prism(o, hs, 0.0, TEXT_T)
    ST.write_stl(os.path.join(out, TEST + "_base.stl"), base)
    ST.write_stl(os.path.join(out, TEST + "_text.stl"), text)
    write_3mf(os.path.join(out, TEST + ".3mf"), [("base", 1, base), ("text", 2, text)], (20, 20))
    preview(os.path.join(out, "testplate-preview.png"), W, H, glyphs)
    print(f"plate {W:.1f} x {H:.1f} x {PLATE_T} mm, {len(glyphs)} glyphs, {len(text)} text triangles")
    return W, H, glyphs


MM_CFG = dict(ST.CFG, nozzle_diameter="0.4,0.4", filament_diameter="1.75,1.75", temperature="215,215",
              first_layer_temperature="215,215", extruder_offset="0x0,0x0", retract_length="0.8,0.8",
              wipe_tower=0, single_extruder_multi_material=0, top_solid_layers=3, bottom_solid_layers=3,
              fill_density="15%", min_bead_width="50%", wall_transition_angle=40, wall_transition_length="40%")


def verify(out, glyphs):
    """Slice the 3MF as a two-extruder print; check the first layer: extruder 2 stays in the text, extruder 1
    stays out of it, and every part of every glyph gets extruder-2 plastic."""
    # analysis files go to out/testprint-verify, never next to the printable files: the G-code is made with a
    # bare generic two-extruder profile (no homing, no heating) and must not be sent to a printer
    vdir = FL.out("out", FL.SLUG, "testprint-verify"); os.makedirs(vdir, exist_ok=True)
    ini = os.path.join(vdir, "generic_2extruders.ini")
    with open(ini, "w") as fh:
        fh.writelines(f"{k} = {v}\n" for k, v in MM_CFG.items())
    gc = os.path.join(vdir, "ANALYSIS-ONLY-do-not-print.gcode")
    ST.slice_stl(os.path.join(out, TEST + ".3mf"), gc, ini)
    tool, z, x, y, segs = 0, 0.0, 0.0, 0.0, []
    for line in open(gc):
        code = line.split(";")[0].split()
        if not code:
            continue
        if code[0] in ("T0", "T1"):
            tool = int(code[0][1]); continue
        if code[0] in ("G0", "G1"):
            d = {t[0]: float(t[1:]) for t in code[1:] if t[0] in "XYZE"}
            z = d.get("Z", z); nx, ny = d.get("X", x), d.get("Y", y)
            if abs(z - 0.2) < 1e-3 and d.get("E", 0) > 0 and (nx, ny) != (x, y):
                segs.append((tool, x, y, nx, ny))
            x, y = nx, ny
    comps = [(o, hs) for g in glyphs for o, hs in ST.regions(g)]
    boxes = [(min(p[0] for p in o), min(p[1] for p in o), max(p[0] for p in o), max(p[1] for p in o)) for o, _ in comps]
    # where the slicer put the plate: shift that best lines extruder-1 perimeters up with the plate's outline
    e1 = [s for s in segs if s[0] == 0]
    dx = min(min(s[1], s[3]) for s in e1) - 0.2; dy = min(min(s[2], s[4]) for s in e1) - 0.2
    print(f"plate placed at x+{dx:.2f} y+{dy:.2f} mm")
    hits = [0] * len(comps); stats = {0: [0, 0], 1: [0, 0]}          # tool: [inside text, outside text] (samples)
    for tool_, ax, ay, bx, by in segs:
        n = max(1, int(math.dist((ax, ay), (bx, by)) / 0.1))
        for k in range(n):
            px, py = ax + (bx - ax) * (k + 0.5) / n - dx, ay + (by - ay) * (k + 0.5) / n - dy
            inside = None
            for i, (b, (o, hs)) in enumerate(zip(boxes, comps)):
                if b[0] - 0.05 <= px <= b[2] + 0.05 and b[1] - 0.05 <= py <= b[3] + 0.05:
                    if ST.inside((px, py), o) and not any(ST.inside((px, py), h) for h in hs):
                        inside = i; break
            stats[tool_][0 if inside is not None else 1] += 1
            if inside is not None and tool_ == 1:
                hits[inside] += 1
    dropped = [i for i, h in enumerate(hits) if h == 0]
    print(f"first layer: extruder 1 {sum(stats[0]) / 10:.0f} mm of line, {stats[0][0] / 10:.1f} mm of it inside text; "
          f"extruder 2 {sum(stats[1]) / 10:.0f} mm, {stats[1][1] / 10:.1f} mm outside text; "
          f"text parts with no extruder-2 plastic: {len(dropped)} of {len(comps)}")
    for i in dropped[:20]:
        b = boxes[i]; print(f"   no plastic: part at x {b[0]:.1f}..{b[2]:.1f} y {b[1]:.1f}..{b[3]:.1f} mm "
                            f"({b[2] - b[0]:.2f} x {b[3] - b[1]:.2f} mm)")
    return stats, dropped


if __name__ == "__main__":
    out = next((a for a in sys.argv[1:] if not a.startswith("--")), None) or FL.out("testprint", FL.SLUG)
    W, H, glyphs = main(out)
    if "--verify" in sys.argv:
        verify(out, glyphs)
