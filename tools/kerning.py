"""Brokkr Sans 3D kerning: "slide room" autokerning with a printing floor.

The spacing classes already make every glyph look right next to a straight stem (HH, nn). Kerning only fixes the
interaction of two shapes. For a pair, the gap is measured row by row (every STEP units) where both glyphs have ink.
Slide room = the smallest row gap minus the gap between the two glyphs' extremes. HT has none (T's arm faces H's
stem), AT / LT / T. / Vo have a lot. Kern = -FRACTION x slide room, at most MAX_KERN.
Then the printing floor: the two inks must stay at least w + 30 units apart in 2D (same floor as the spacing),
so the background colour always gets more than one full line between letters. Manual overrides win.

python -I tools/kerning.py <family>   -> writes families/<family>/kerning.json {weight: {"AV": -85, ...}} and prints the strongest pairs
"""
import importlib.util, json, math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
if "b3d_fontlib" not in sys.modules:               # shared loader: family from the first argument, paths
    _s = importlib.util.spec_from_file_location("b3d_fontlib", os.path.join(HERE, "fontlib.py"))
    _m = importlib.util.module_from_spec(_s); sys.modules["b3d_fontlib"] = _m; _s.loader.exec_module(_m)
FL = sys.modules["b3d_fontlib"]
G = FL.family()

STEP, FRACTION, MIN_KERN = 5, 0.5, 15
MAX_KERN, MAX_PUNCT = 130, 100       # cap for letter pairs / pairs with punctuation
ENCLOSE = 400                        # look this far above/below a glyph for arms that would enclose it
LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZÆØÅabcdefghijklmnopqrstuvwxyzæøå"   # digits unkerned (columns line up)
LEFT = LETTERS + ".,:;-'\")]}/?!*&"
RIGHT = LETTERS + ".,:;-'\"([{/?!*&@"
MANUAL = getattr(G, "KERN_MANUAL", {})     # per family, in families/<family>/glyphs.py; applied last


def profiles(gl):
    """Leftmost / rightmost ink per row: {y: x}."""
    polys = [G.geo.flatten(c, 8) for c in gl["contours"]]
    left, right = {}, {}
    for y in range(G.DESC - 150, G.ASC + 160, STEP):
        yy = y + 0.37
        xs = [a[0] + (yy - a[1]) * (b[0] - a[0]) / (b[1] - a[1])
              for p in polys for a, b in zip(p, p[1:] + p[:1]) if (a[1] > yy) != (b[1] > yy)]
        if xs:
            left[y], right[y] = min(xs), max(xs)
    return left, right


def kern_table(wname):
    w = G.WEIGHTS[wname]
    font = G.build(w)
    floor = w + 30
    P = {}
    for c, gl in font.items():
        if gl["contours"]:
            l, r = profiles(gl)
            # a glyph's edge is judged from ink at or above the baseline: descenders (j's hook) don't set it
            ru = [x for y, x in r.items() if y >= 0] or list(r.values())
            lu = [x for y, x in l.items() if y >= 0] or list(l.values())
            P[c] = (l, r, max(ru), min(lu))
    table = {}
    for a in LEFT:
        for b in RIGHT:
            if a not in P or b not in P:
                continue
            rl, lr = P[a][1], P[b][0]
            rows = [y for y in rl if y in lr]
            if not rows:
                continue
            adv = font[a]["adv"]
            extremes = adv - P[a][2] + P[b][3]                 # gap between the two glyphs' extremes
            mg = min(adv - rl[y] + lr[y] for y in rows)        # smallest row gap
            room = mg - extremes
            cap = MAX_KERN if a in LETTERS and b in LETTERS else MAX_PUNCT
            want = -min(FRACTION * room, cap)
            near = mg < floor + 60 or adv - P[a][2] + P[b][3] < floor   # might break the printing floor
            if want > -MIN_KERN and not near:
                continue
            # no sliding into a space that is closed above and below (hyphen into C, period into S ...)
            y_lo, y_hi = min(rows), max(rows)
            for prof, other, sign in ((rl, lr, 1), (lr, rl, -1)):
                above = [prof[y] for y in prof if y_hi < y <= y_hi + ENCLOSE]
                below = [prof[y] for y in prof if y_lo - ENCLOSE <= y < y_lo]
                if above and below:
                    if sign == 1:      # left glyph encloses: right glyph may not pass its shorter arm
                        arm = min(max(above), max(below))
                        limit = arm - (adv + min(other[y] for y in rows)) + floor
                        want = max(want, min(0, limit))
                    else:              # right glyph encloses the left glyph
                        arm = max(min(above), min(below))
                        limit = max(other[y] for y in rows) - (adv + arm) + floor
                        want = max(want, min(0, limit))
            if want > -MIN_KERN:
                want = 0.0                                      # no tightening, only the floor check below
            kmin = -1e9                                         # printing floor, 2D
            ry = sorted(lr)
            for y1, x1 in rl.items():
                for y2 in ry:
                    dy = y2 - y1
                    if abs(dy) >= floor:
                        continue
                    dx = adv + lr[y2] - x1
                    kmin = max(kmin, -dx + math.sqrt(floor * floor - dy * dy))
            k = max(want, kmin)
            k = int(math.ceil(k / 5.0)) * 5 if k > 0 else int(round(k / 5.0)) * 5   # pushes round up
            if k <= -MIN_KERN or k > 0:
                table[a + b] = k
    table.update(MANUAL.get(wname, {}))
    return table


if __name__ == "__main__":
    out = {}
    for wname in G.WEIGHTS:
        t = kern_table(wname)
        out[wname] = dict(sorted(t.items()))
        top = sorted(t.items(), key=lambda kv: kv[1])[:30]
        print(f"== {wname}: {len(t)} pairs; strongest: " + " ".join(f"{p}{v}" for p, v in top))
    with open(os.path.join(os.path.dirname(G.__file__), "kerning.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=0, ensure_ascii=False)
