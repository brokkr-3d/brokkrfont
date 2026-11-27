"""Build BrokkrSans3D-Light / -Regular / -Bold .ttf from the glyph drawings.

python -I tools/build_ttf.py <family> [outdir]      (default: fonts/<PS family name>/)

- Outlines: the engine's cubic curves -> quadratic (cu2qu, max error 0.5 unit), contours reversed to TrueType's
  clockwise-outer convention, coordinates rounded to whole units.
- Kerning from kerning.json, written twice: GPOS 'kern' feature (modern apps) and a legacy 'kern' table
  (older Windows apps and some CAD tools only read that one).
- Family: "Brokkr Sans 3D" with Regular + Bold as one style-linked family; Light is its own family "Brokkr Sans 3D Light"
  (so Windows menus show it), all three grouped under the typographic family "Brokkr Sans 3D".
"""
import importlib.util, os, site, sys

sys.path.append(site.getusersitepackages())       # fontTools lives in the user site (isolated mode skips it)
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.cu2quPen import Cu2QuPen
from fontTools.pens.roundingPen import RoundingPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont, newTable
from fontTools.ttLib.tables._k_e_r_n import KernTable_format_0

HERE = os.path.dirname(os.path.abspath(__file__))
if "b3d_fontlib" not in sys.modules:               # shared loader: family from the first argument, paths
    _s = importlib.util.spec_from_file_location("b3d_fontlib", os.path.join(HERE, "fontlib.py"))
    _m = importlib.util.module_from_spec(_s); sys.modules["b3d_fontlib"] = _m; _s.loader.exec_module(_m)
FL = sys.modules["b3d_fontlib"]
G = FL.family()

VERSION, COPYRIGHT = G.VERSION, G.COPYRIGHT
VENDOR = "NONE"
WEIGHT_CLASS = {"Light": 300, "Regular": 400, "Bold": 700}


def ps_name(c):
    """Standard (AGL) glyph names for the font file."""
    if c == " ":
        return "space"
    if c in G.NAMES:
        return G.NAMES[c]
    return c                                           # A-Z, a-z


def draw(contours):
    pen = TTGlyphPen(None)
    cu = Cu2QuPen(RoundingPen(pen), max_err=0.5, reverse_direction=True)
    for start, segs in contours:
        cu.moveTo(start)
        for i, s in enumerate(segs):
            if s[0] == "L":
                if i == len(segs) - 1 and abs(s[1][0] - start[0]) < 1e-6 and abs(s[1][1] - start[1]) < 1e-6:
                    continue                           # closing segment: closePath() draws it
                cu.lineTo(s[1])
            else:
                cu.curveTo(s[1], s[2], s[3])
        cu.closePath()
    return pen.glyph()


def notdef():
    pen = TTGlyphPen(None)
    for pts in ([(50, 0), (50, 700), (450, 700), (450, 0)], [(100, 50), (400, 50), (400, 650), (100, 650)]):
        pen.moveTo(pts[0])
        for p in pts[1:]:
            pen.lineTo(p)
        pen.closePath()
    return pen.glyph()


def extents():
    """Vertical extents over every weight, so all three fonts share the same line spacing."""
    ymin, ymax = 0, 0
    for w in G.WEIGHTS.values():
        for gl in G.build(w).values():
            for c in gl["contours"]:
                for x, y in G.geo.flatten(c, 6):
                    ymin, ymax = min(ymin, y), max(ymax, y)
    return int(-(-ymax // 1)), int(ymin // 1)


def build(wname, outdir, ymax, ymin):
    w = G.WEIGHTS[wname]
    font = G.build(w)
    chars = [c for c in font]
    names = {c: ps_name(c) for c in chars}
    order = [".notdef"] + [names[c] for c in chars]
    glyphs = {".notdef": notdef()}
    for c in chars:
        glyphs[names[c]] = draw(font[c]["contours"])
    fb = FontBuilder(G.UPM, isTTF=True)
    fb.setupGlyphOrder(order)
    fb.setupCharacterMap({ord(c): names[c] for c in chars})
    fb.setupGlyf(glyphs)
    glyf = fb.font["glyf"]
    adv = {".notdef": 500}
    adv.update({names[c]: int(round(font[c]["adv"])) for c in chars})
    fb.setupHorizontalMetrics({n: (adv[n], getattr(glyf[n], "xMin", 0)) for n in order})
    asc, desc = ymax + 10, ymin - 10
    fb.setupHorizontalHeader(ascent=asc, descent=desc, lineGap=0)
    light = wname == "Light"
    family = f"{G.FAMILY} Light" if light else G.FAMILY
    style = "Regular" if light else wname
    fb.setupNameTable({
        "copyright": COPYRIGHT, "familyName": family, "styleName": style,
        "uniqueFontIdentifier": f"{VERSION};{VENDOR};{G.PS_FAMILY}-{wname}", "fullName": f"{G.FAMILY} {wname}",
        "version": f"Version {VERSION}", "psName": f"{G.PS_FAMILY}-{wname}",
        "typographicFamily": G.FAMILY, "typographicSubfamily": wname,
        "description": "Monoline font for multi-colour first-layer text in 3D printing. "
                       "Stroke = 0.4/0.8/1.2 mm at 8 mm cap height."})
    fs = 0x20 if wname == "Bold" else 0x40
    fb.setupOS2(usWeightClass=WEIGHT_CLASS[wname], usWidthClass=5, fsType=0, achVendID=VENDOR, fsSelection=fs,
                sTypoAscender=780, sTypoDescender=-220, sTypoLineGap=max(0, asc - desc - 1000),
                usWinAscent=asc, usWinDescent=-desc, sxHeight=G.XH, sCapHeight=G.CAP,
                usDefaultChar=0, usBreakChar=32, usFirstCharIndex=min(ord(c) for c in chars),
                usLastCharIndex=max(ord(c) for c in chars))
    fb.setupPost(keepGlyphNames=True, underlinePosition=-120, underlineThickness=w)
    fb.font["head"].macStyle = 1 if wname == "Bold" else 0
    fb.font["head"].fontRevision = float(VERSION)
    fb.font["OS/2"].recalcUnicodeRanges(fb.font)
    fb.font["OS/2"].recalcCodePageRanges(fb.font)
    # kerning
    pairs = {}
    for p, v in G.KERNING.get(wname, {}).items():
        a, b = p[0], p[1]
        if a in names and b in names and v:
            pairs[(names[a], names[b])] = int(v)
    if pairs:
        fea = "languagesystem DFLT dflt;\nlanguagesystem latn dflt;\nfeature kern {\n" + \
              "".join(f"  pos {a} {b} {v};\n" for (a, b), v in sorted(pairs.items())) + "} kern;\n"
        fb.addOpenTypeFeatures(fea)
        kern = newTable("kern"); kern.version = 0
        st = KernTable_format_0(); st.version = 0; st.coverage = 1; st.format = 0
        st.kernTable = dict(pairs); kern.kernTables = [st]
        fb.font["kern"] = kern
    path = os.path.join(outdir, f"{G.PS_FAMILY}-{wname}.ttf")
    fb.save(path)
    return path, len(order), len(pairs)


if __name__ == "__main__":
    outdir = sys.argv[1] if len(sys.argv) > 1 else FL.out("fonts", G.PS_FAMILY)
    os.makedirs(outdir, exist_ok=True)
    ymax, ymin = extents()
    print(f"vertical extents over all weights: {ymin} .. {ymax}")
    for wname in G.WEIGHTS:
        path, n, k = build(wname, outdir, ymax, ymin)
        f = TTFont(path)                                # round-trip check
        print(f"{os.path.basename(path)}: {n} glyphs, {k} kern pairs, {os.path.getsize(path) // 1024} KB, "
              f"cmap {len(f.getBestCmap())} chars, tables {' '.join(sorted(f.keys()))}")
