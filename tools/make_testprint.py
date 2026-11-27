# Copyright 2026 Brokkr 3D AS (https://brokkr.design).
# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. If a copy of the MPL
# was not distributed with this file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Brokkr Sans 3D test plate for a two-colour print with the text on the face that touches the bed.

python -I tools/make_testprint.py <family> [outdir] [--text=MM] [--plate=MM] [--verify]
    default: testprint/<family>/, text 0.6 mm deep (3 layers of 0.2 mm), plate 2.0 mm thick in total

Writes
  brokkr_sans_3d_test_base.stl   plate, colour 1 (rounded rectangle, the full plate thickness)
  brokkr_sans_3d_test_text.stl   text, colour 2, from the bed up to the text depth (overlaps the plate there)
  brokkr_sans_3d_test.3mf        PrusaSlicer project: one object, base = extruder 1, text = extruder 2
  testplate-preview.png          what the face of the print looks like
Print it as it lies: the text is in the bottom layers. The face is seen from below, so the text is mirrored in the
files (in the slicer, seen from above, it reads backwards) and reads the right way round on the finished face.
"""
import importlib.util, math, os, sys, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
if "b3d_fontlib" not in sys.modules:               # shared loader: family from the first argument, paths
    _s = importlib.util.spec_from_file_location("b3d_fontlib", os.path.join(HERE, "fontlib.py"))
    _m = importlib.util.module_from_spec(_s); sys.modules["b3d_fontlib"] = _m; _s.loader.exec_module(_m)
FL = sys.modules["b3d_fontlib"]


ST = FL.tool("slice_test"); G = ST.G; RND = ST.RND
TEST = f"brokkr_{G.SLUG}_3d_test"                      # file name stem
TEXT_T, PLATE_T = 0.6, 2.0                             # defaults (mm): text depth from the bed, total plate thickness
MARGIN, GAP, CORNER = 7.0, 2.6, 4.0
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


def bed_side(glyphs, W):
    """Mirror the text left-right for the model. The face is the side that touches the bed and is seen from
    below, so text drawn as read from above comes out backwards; mirrored in the model, it reads the right way
    round on the face. Contours are reversed too, so outer contours stay counter-clockwise."""
    return [[[(W - x, y) for x, y in reversed(c)] for c in g] for g in glyphs]


def mirror_mesh(tris, W):
    """The same mirror for triangles; vertex order reversed so the faces still point outwards."""
    return [tuple((W - p[0], p[1], p[2]) for p in reversed(t)) for t in tris]


def open_edges(tris):
    """Edges not matched by exactly one edge running the other way: 0 for a closed, consistently oriented mesh."""
    edges = {}
    for t in tris:
        for a, b in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])):
            k = (tuple(round(v, 5) for v in a), tuple(round(v, 5) for v in b))
            edges[k] = edges.get(k, 0) + 1
    return sum(1 for (a, b), n in edges.items() if n != 1 or edges.get((b, a)) != 1)


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


def main(out, text_t=TEXT_T, plate_t=PLATE_T):
    if not 0 < text_t < plate_t:
        raise SystemExit(f"the text depth ({text_t} mm) must be more than 0 and less than the plate ({plate_t} mm)")
    layers = text_t / ST.LAYER
    if abs(layers - round(layers)) > 1e-6:
        print(f"note: a text depth of {text_t} mm is not a whole number of {ST.LAYER} mm layers")
    os.makedirs(out, exist_ok=True)
    W, H, face = layout_plate()                         # as the finished face reads
    glyphs = bed_side(face, W)                          # outlines as the model carries them (for --verify)
    base = prism(rounded_rect(W, H, CORNER), [], 0.0, plate_t)
    # triangulate the text as it reads, then mirror the mesh: the hole-bridging triangulation can fail on mirrored
    # outlines (a mirrored B has two counters with the same right edge, and its faces came out with gaps)
    text = []
    for g in face:
        for o, hs in ST.regions(g):
            text += prism(o, hs, 0.0, text_t)
    text = mirror_mesh(text, W)
    for name, tris in (("base", base), ("text", text)):
        n = open_edges(tris)
        if n:
            print(f"WARNING: the {name} mesh is not closed ({n} open edges)")
    ST.write_stl(os.path.join(out, TEST + "_base.stl"), base)
    ST.write_stl(os.path.join(out, TEST + "_text.stl"), text)
    write_3mf(os.path.join(out, TEST + ".3mf"), [("base", 1, base), ("text", 2, text)], (20, 20))
    preview(os.path.join(out, "testplate-preview.png"), W, H, face)
    print(f"plate {W:.1f} x {H:.1f} x {plate_t:g} mm, text {text_t:g} mm deep ({layers:g} layers) on the bed side, "
          f"mirrored in the files; {len(glyphs)} glyphs, {len(text)} text triangles")
    return W, H, glyphs


# a generic two-extruder printer with the recommended text settings: Arachne 50 % / 40° / 40 %, and 0.4 mm lines
# for the first layer and the perimeters, so every text layer is drawn in 0.4 mm lines (other lines stay 0.45 mm)
MM_CFG = dict(ST.CFG, nozzle_diameter="0.4,0.4", filament_diameter="1.75,1.75", temperature="215,215",
              first_layer_temperature="215,215", extruder_offset="0x0,0x0", retract_length="0.8,0.8",
              wipe_tower=0, single_extruder_multi_material=0, top_solid_layers=3, bottom_solid_layers=3,
              fill_density="15%", min_bead_width="50%", wall_transition_angle=40, wall_transition_length="40%",
              perimeter_extrusion_width=0.4, external_perimeter_extrusion_width=0.4)


def verify(out, glyphs, text_t=TEXT_T, cfg=None):
    """Slice the 3MF as a two-extruder print and check every layer the text is in: extruder 2 stays in the
    text, extruder 1 stays out of it, and every part of every glyph gets extruder-2 plastic. Also checks that
    the layer above the text has no extruder-2 plastic. `glyphs` are the outlines as the model carries them."""
    # analysis files go to out/testprint-verify, never next to the printable files: the G-code is made with a
    # bare generic two-extruder profile (no homing, no heating) and must not be sent to a printer
    vdir = FL.out("out", FL.SLUG, "testprint-verify"); os.makedirs(vdir, exist_ok=True)
    ini = os.path.join(vdir, "generic_2extruders.ini")
    with open(ini, "w") as fh:
        fh.writelines(f"{k} = {v}\n" for k, v in (cfg or MM_CFG).items())
    gc = os.path.join(vdir, "ANALYSIS-ONLY-do-not-print.gcode")
    ST.slice_stl(os.path.join(out, TEST + ".3mf"), gc, ini)
    top = text_t + ST.LAYER + 1e-3                      # text layers + the first layer above them
    tool, z, x, y, layers = 0, 0.0, 0.0, 0.0, {}
    for line in open(gc):
        code = line.split(";")[0].split()
        if not code:
            continue
        if code[0] in ("T0", "T1"):
            tool = int(code[0][1]); continue
        if code[0] in ("G0", "G1"):
            d = {t[0]: float(t[1:]) for t in code[1:] if t[0] in "XYZE"}
            z = d.get("Z", z); nx, ny = d.get("X", x), d.get("Y", y)
            if z < top and d.get("E", 0) > 0 and (nx, ny) != (x, y):
                layers.setdefault(round(z, 3), []).append((tool, x, y, nx, ny))
            x, y = nx, ny
    comps = [(o, hs) for g in glyphs for o, hs in ST.regions(g)]
    boxes = [(min(p[0] for p in o), min(p[1] for p in o), max(p[0] for p in o), max(p[1] for p in o)) for o, _ in comps]
    CELL = 2.0                                          # grid of text parts, so each sample tests only its neighbours
    grid = {}
    for i, b in enumerate(boxes):
        for gx in range(int((b[0] - 0.05) // CELL), int((b[2] + 0.05) // CELL) + 1):
            for gy in range(int((b[1] - 0.05) // CELL), int((b[3] + 0.05) // CELL) + 1):
                grid.setdefault((gx, gy), []).append(i)
    # where the slicer put the plate: the first layer's outer perimeter runs half a line (0.2 mm) inside the outline
    e1 = [s for s in layers[min(layers)] if s[0] == 0]
    dx = min(min(s[1], s[3]) for s in e1) - 0.2; dy = min(min(s[2], s[4]) for s in e1) - 0.2
    print(f"plate placed at x+{dx:.2f} y+{dy:.2f} mm")
    results = []
    for zl in sorted(layers):
        hits = [0] * len(comps); stats = {0: [0, 0], 1: [0, 0]}      # tool: [inside text, outside text] (samples)
        for tool_, ax, ay, bx, by in layers[zl]:
            n = max(1, int(math.dist((ax, ay), (bx, by)) / 0.1))
            for k in range(n):
                px, py = ax + (bx - ax) * (k + 0.5) / n - dx, ay + (by - ay) * (k + 0.5) / n - dy
                inside = None
                for i in grid.get((int(px // CELL), int(py // CELL)), ()):
                    b = boxes[i]; o, hs = comps[i]
                    if b[0] - 0.05 <= px <= b[2] + 0.05 and b[1] - 0.05 <= py <= b[3] + 0.05:
                        if ST.inside((px, py), o) and not any(ST.inside((px, py), h) for h in hs):
                            inside = i; break
                stats[tool_][0 if inside is not None else 1] += 1
                if inside is not None and tool_ == 1:
                    hits[inside] += 1
        if zl > text_t + 1e-3:
            print(f"z {zl:.2f} (above the text): extruder 2 {sum(stats[1]) / 10:.1f} mm of line (should be 0)")
            results.append((zl, stats, []))
            continue
        dropped = [i for i, h in enumerate(hits) if h == 0]
        print(f"z {zl:.2f}: extruder 1 {sum(stats[0]) / 10:.0f} mm of line, {stats[0][0] / 10:.1f} mm of it inside text; "
              f"extruder 2 {sum(stats[1]) / 10:.0f} mm, {stats[1][1] / 10:.1f} mm outside text; "
              f"text parts with no extruder-2 plastic: {len(dropped)} of {len(comps)}")
        for i in dropped[:20]:
            b = boxes[i]; print(f"   no plastic: part at x {b[0]:.1f}..{b[2]:.1f} y {b[1]:.1f}..{b[3]:.1f} mm "
                                f"({b[2] - b[0]:.2f} x {b[3] - b[1]:.2f} mm)")
        results.append((zl, stats, dropped))
    return results


if __name__ == "__main__":
    opts = dict(a[2:].split("=", 1) for a in sys.argv[1:] if a.startswith("--") and "=" in a)
    bad = [a for a in sys.argv[1:] if a.startswith("--") and a != "--verify" and a.split("=")[0] not in ("--text", "--plate")]
    if bad:
        raise SystemExit(f"unknown option {bad[0]}; use --text=MM, --plate=MM, --verify")
    text_t, plate_t = float(opts.get("text", TEXT_T)), float(opts.get("plate", PLATE_T))
    out = next((a for a in sys.argv[1:] if not a.startswith("--")), None) or FL.out("testprint", FL.SLUG)
    W, H, glyphs = main(out, text_t, plate_t)
    if "--verify" in sys.argv:
        verify(out, glyphs, text_t)
