# Copyright 2026 Brokkr 3D AS (https://brokkr.design), with Reserved Font Name "Brokkr".
# Part of the Font Software licensed under the SIL Open Font License 1.1 - see OFL.txt in the repository root.
"""Brokkr Sans 3D - monoline font for first-layer 3D-print text.

Units: UPM 1000, baseline 0, y up. Cap height 700 = 8 mm at the base size.
Stroke w: Light 35, Regular 70, Bold 105  (0.4 / 0.8 / 1.2 mm at 8 mm caps).
Rules: every stroke is exactly w; stroke ends get radius rr = w/4; junctions get ri = w/4;
a counter corner is only rounded (outer R - w) where the outside corner is a concentric R;
gaps between separate strokes are at least w.

Glyph drawings live in glyphs_upper.py, glyphs_lower.py and glyphs_figures.py.
Each drawing is a function f(K) -> (ink_width, (left_space, right_space), [primitives]).
Run:  python -I families/sans/glyphs.py   (SVG sheets -> specimens/sans, per-glyph SVGs -> out/sans/svg)
"""
import importlib.util, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))


def _load(name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(HERE, name + ".py"))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m


ROOT = os.path.dirname(os.path.dirname(HERE))           # repo root (families/<slug>/ -> ..)
if "b3d_geom" not in sys.modules:                         # shared geometry engine in tools/
    _gs = importlib.util.spec_from_file_location("b3d_geom", os.path.join(ROOT, "tools", "b3d_geom.py"))
    _gm = importlib.util.module_from_spec(_gs); sys.modules["b3d_geom"] = _gm; _gs.loader.exec_module(_gm)
geo = sys.modules["b3d_geom"]

UPM, CAP, XH, ASC, DESC = 1000, 700, 550, 760, -220
# identity of this family (used by build_ttf, specimens, test plate)
SLUG, FAMILY, PS_FAMILY = "sans", "Brokkr Sans 3D", "BrokkrSans3D"
VERSION = "0.9"
# ownership and licence: written into every font file (name table) by tools/build_ttf.py
COPYRIGHT = 'Copyright 2026 Brokkr 3D AS (https://brokkr.design), with Reserved Font Name "Brokkr".'
MANUFACTURER, VENDOR_URL = "Brokkr 3D AS", "https://brokkr.design"
LICENSE = ("This Font Software is licensed under the SIL Open Font License, Version 1.1. "
           "This license is available with a FAQ at: https://openfontlicense.org")
LICENSE_URL = "https://openfontlicense.org"
KERN_MANUAL = {}                                          # manual kerning overrides, e.g. {"Regular": {"LT": -60}}

WEIGHTS = {"Light": 35, "Regular": 70, "Bold": 105}
CAP_MM = 8.0                     # base size: cap height in mm
R_UC, R_LC = 180, 160            # outer corner radius of round capitals / lowercase bowls
SPACE = {"uc": 80, "lc": 65}     # side bearing of a straight stem


class K:
    """Drawing context for one weight: metrics plus geometry helpers with w bound in."""

    def __init__(self, w):
        self.w, self.rr, self.ri = w, w / 4, w / 4
        self.CAP, self.XH, self.ASC, self.DESC, self.R_UC, self.R_LC = CAP, XH, ASC, DESC, R_UC, R_LC
        # punctuation dot size, a whole number of 0.4 mm lines at 8 mm caps: Light 2, Regular 3, Bold 4.
        # PrusaSlicer drops square dots of 0.63 mm entirely (slicer test 2); odd sizes leave a hollow centre.
        self.D = max(70, w + 35)
        self.Di = min(self.D, ASC - XH - w)          # i/j dot size (keeps the gap >= w)
        self.g = geo

    # primitives
    def rect(self, *a, **k): return geo.rect(*a, **k)
    def poly(self, *p): return geo.poly(*p)
    def ring(self, x0, y0, x1, y1, bl=None, br=None, tr=None, tl=None):
        return geo.ring(x0, y0, x1, y1, self.w, bl, br, tr, tl)
    def stem(self, x, y0, y1): return geo.rect(x, y0, x + self.w, y1)
    def bar(self, x0, x1, y): return geo.rect(x0, y, x1, y + self.w)          # bottom edge at y
    def stroke(self, p0, p1, cut0=None, cut1=None): return geo.stroke(p0, p1, self.w, cut0, cut1)
    def edge(self, a, b, side, cut_a=None, cut_b=None): return geo.edge_stroke(a, b, self.w, side, cut_a, cut_b)
    def tan(self, a, b, cut_a, cut_b, a_side="L"): return geo.tangent_stroke(a, b, self.w, cut_a, cut_b, a_side)
    def clip(self, p, xmin=-1e9, xmax=1e9, ymin=-1e9, ymax=1e9): return geo.clip(p, xmin, xmax, ymin, ymax)
    def cshape(self, x0, y0, x1, y1, R_bl=None, R_tl=None, top_to=None, bot_to=None):
        return geo.cshape(x0, y0, x1, y1, self.w, R_bl, R_tl, top_to, bot_to)
    def mirror(self, p, W): return geo.mirror_x(p, W)
    def flip(self, p, H): return geo.flip_y(p, H)
    def rot(self, p, W, H): return geo.rot180(p, W, H)
    def dot(self, x, y, d=None):
        d = self.D if d is None else d
        return geo.rect(x, y, x + d, y + d)


SETS = ("glyphs_upper", "glyphs_lower", "glyphs_figures", "glyphs_nordic")
REGISTRY = {}
for _s in SETS:
    if os.path.exists(os.path.join(HERE, _s + ".py")):
        REGISTRY.update(_load(_s).GLYPHS)          # char -> (case, function)

NAMES = {" ": "space", ".": "period", ",": "comma", ":": "colon", ";": "semicolon", "!": "exclam",
         "?": "question", "'": "quotesingle", '"': "quotedbl", "-": "hyphen", "(": "parenleft",
         ")": "parenright", "[": "bracketleft", "]": "bracketright", "{": "braceleft", "}": "braceright",
         "/": "slash", "\\": "backslash", "&": "ampersand", "@": "at", "#": "numbersign", "+": "plus",
         "=": "equal", "_": "underscore", "*": "asterisk", "%": "percent", "<": "less", ">": "greater",
         "|": "bar", "$": "dollar", "~": "asciitilde", "^": "asciicircum", "`": "grave",
         "0": "zero", "1": "one", "2": "two", "3": "three", "4": "four", "5": "five", "6": "six",
         "7": "seven", "8": "eight", "9": "nine",
         "Æ": "AE", "Ø": "Oslash", "Å": "Aring", "æ": "ae", "ø": "oslash", "å": "aring"}


def glyph_name(c):
    if c in NAMES:
        return NAMES[c]
    return c if c.isupper() else c + "_lc" if c.islower() else f"uni{ord(c):04X}"


def side_bearing(cls, case, w):
    base = SPACE[case]
    if isinstance(cls, tuple) and cls[0] == "stem":
        # space like a straight stem that sits cls[1] units in from the ink edge (may go negative: j's hook
        # tucks under the previous glyph; kerning.py pushes it back wherever a descender is in the way)
        return side_bearing("S", case, w) - cls[1]
    if isinstance(cls, (int, float)):
        v = cls
    else:
        v = {"S": base, "O": 0.85 * base, "A": 0.55 * base, "D": 0.5 * w + 20}[cls]
    return max(v, 0.5 * w + 15)       # two neighbours never come closer than w + 30


class Font(dict):
    """{char: glyph} plus .kern = {"AV": -120, ...} for this weight (from kerning.json, made by kerning.py)."""
    kern = {}


_KFILE = os.path.join(HERE, "kerning.json")
KERNING = json.load(open(_KFILE, encoding="utf-8")) if os.path.exists(_KFILE) else {}


def build(w, chars=None):
    """Returns Font {char: dict(adv, lsb, ink, contours, warnings)} for stroke w, with .kern set."""
    k = K(w)
    out = Font()
    out.kern = KERNING.get(next((n for n, v in WEIGHTS.items() if v == w), ""), {})
    for c, (case, f) in REGISTRY.items():
        if chars and c not in chars:
            continue
        ink, (lc, rc), prims = f(k)
        lsb, rsb = side_bearing(lc, case, w), side_bearing(rc, case, w)
        warn = []
        if isinstance(prims, dict):                  # explicit contours from geo.Path (+ optional prims)
            cs = list(prims.get("contours", []))
            if prims.get("prims"):
                cs += geo.outline(prims["prims"], k.rr, k.ri, warn)
        else:
            cs = geo.outline(prims, k.rr, k.ri, warn) if prims else []
        xs = [p[0] for s, segs in cs for p in [s] + [sg[-1] for sg in segs]]
        if xs and (min(xs) < -1 or max(xs) > ink + 1):      # ink must stay inside the declared width
            warn.append(f"ink {min(xs):.0f}..{max(xs):.0f} outside declared width 0..{ink:.0f}")
        cs = [(_shift(s, lsb), [(_shift_seg(sg, lsb)) for sg in segs]) for s, segs in cs]
        out[c] = dict(adv=lsb + ink + rsb, lsb=lsb, ink=ink, contours=cs, warnings=warn)
    if " " not in out:
        out[" "] = dict(adv=250, lsb=0, ink=0, contours=[], warnings=[])
    return out


def _shift(p, dx):
    return (p[0] + dx, p[1])


def _shift_seg(s, dx):
    return (s[0],) + tuple(_shift(p, dx) for p in s[1:])


def layout(font, text, kerning=True):
    """Place a string: returns [(x_offset, glyph_dict)] and total advance (kerning applied unless switched off)."""
    kern = getattr(font, "kern", {}) if kerning else {}
    x, out, prev = 0.0, [], None
    for c in text:
        gl = font.get(c)
        if gl is None:
            continue
        if prev is not None:
            x += kern.get(prev + c, 0)
        out.append((x, gl)); x += gl["adv"]; prev = c
    return out, x


def svg_sheet(font, title, per_row=12, cell=1000):
    chars = [c for c in font if c != " "]
    rows = (len(chars) + per_row - 1) // per_row
    H = rows * 1250 + 200
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {per_row * cell} {H}" width="{per_row * cell // 4}" height="{H // 4}">',
             f'<rect width="100%" height="100%" fill="#fff"/><text x="40" y="120" font-family="sans-serif" font-size="80">{title}</text>']
    for i, c in enumerate(chars):
        gl = font[c]
        cx, base = (i % per_row) * cell, 200 + (i // per_row) * 1250 + 950
        dx = cx + (cell - gl["adv"]) / 2
        for y, col in ((0, "#4a90d9"), (CAP, "#ddd"), (XH, "#ddd"), (DESC, "#ddd"), (ASC, "#eee")):
            parts.append(f'<line x1="{cx + 30}" x2="{cx + cell - 30}" y1="{base - y}" y2="{base - y}" stroke="{col}" stroke-width="4"/>')
        parts.append(f'<rect x="{dx:.0f}" y="{base - ASC}" width="{gl["adv"]:.0f}" height="{ASC - DESC}" fill="none" stroke="#f3c" stroke-width="2" stroke-dasharray="10 10"/>')
        parts.append(f'<path fill="#111" fill-rule="evenodd" d="{geo.svg_d(gl["contours"], dx, base)}"/>')
    parts.append("</svg>")
    return "".join(parts)


if __name__ == "__main__":
    outdir = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "specimens", SLUG)
    os.makedirs(outdir, exist_ok=True)
    for wname, w in WEIGHTS.items():
        font = build(w)
        for c, gl in font.items():
            for m in gl["warnings"]:
                print(f"{wname} {c!r}: {m}")
        open(os.path.join(outdir, f"sheet-{wname}.svg"), "w").write(svg_sheet(font, f"Brokkr Sans 3D {wname}"))
        gdir = os.path.join(ROOT, "out", SLUG, "svg", wname); os.makedirs(gdir, exist_ok=True)
        for c, gl in font.items():
            if gl["contours"]:
                open(os.path.join(gdir, f"BrokkrSans3D-{wname}-{glyph_name(c)}.svg"), "w").write(
                    f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 {-ASC - 40} {gl["adv"]:.0f} {ASC - DESC + 80}">'
                    f'<path fill="#000" fill-rule="evenodd" d="{geo.svg_d(gl["contours"])}"/></svg>')
    print("glyphs:", len(font))
