# Copyright 2026 Brokkr 3D AS (https://brokkr.design), with Reserved Font Name "Brokkr".
# Part of the Font Software licensed under the SIL Open Font License 1.1 - see OFL.txt in the repository root.
"""Brokkr Sans 3D Norwegian letters: Æ Ø Å æ ø å. Same conventions as glyphs_upper.py.

Printing rules carried over: the ring's hole is at least one stroke wide (so the ring grows in Bold), the
capital ring sits on the A's apex (no thin gap to fuse, less height), the lowercase ring floats one stroke
above the a, and the Ø slash runs between the counter's corners, ends buried in the bowl (no spikes)."""
import importlib.util, math, os

_HERE = os.path.dirname(os.path.abspath(__file__))


def _load(name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(_HERE, name + ".py"))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m


U, L = _load("glyphs_upper"), _load("glyphs_lower")


def _ring(K, cx, y0, s, seated=False):
    """Rounded-square ring of size s. seated=True (on the A's apex): smaller bottom corners, because the legs
    join right next to them and a full radius would not fit."""
    R = 0.42 * s; Rb = 0.16 * s if seated else R
    return K.ring(cx - s / 2, y0, cx + s / 2, y0 + s, Rb, Rb, R, R)


def _slash(K, W, H, R):
    """Slash between the middles of the bowl's stroke in its bottom-left and top-right corners (on each corner's
    45-degree line). Its square ends stay buried in the bowl in every weight - aiming at the counter's corner
    points instead would poke out of the rounded corners in Light - so the outline remains a clean O."""
    w, s2 = K.w, math.sqrt(2)
    dmax = math.sqrt((R - 8) ** 2 - (w / 2) ** 2)    # furthest end (from the corner centre) that stays inside
    dc = s2 * (R - w)                                 # the counter's corner point on the same 45-degree line
    D = (dc + 10 + dmax) / 2 if dc + 10 <= dmax else min(dmax, dc - 15)   # never right on that point
    d = D / s2
    return K.stroke((R - d, R - d), (W - R + d, H - R + d))


def Aring(K):
    w, C = K.w, K.CAP
    W, sides, prims = U.A(K)
    s = max(200, 3 * w + 10)                       # hole >= w
    return W, sides, prims + [_ring(K, W / 2, C - 0.3 * w, s, seated=True)]


def aring(K):
    w, X = K.w, K.XH
    W, sides, prims = L.a(K)
    s = max(180, 3 * w + 10)
    return W, sides, prims + [_ring(K, W / 2, X + max(w, 70), s)]


def _round_ring(K, W, H, R, n=24):
    """The O ring with its corners already rounded (fine polygon, ~0.1 unit from the true arcs), for the case
    where the slash only meets the bowl after rounding (Light: thin stroke, large radius)."""
    def rrect(xa, ya, xb, yb, r):
        pts = []
        for cx, cy, a0 in ((xb - r, ya + r, -90), (xb - r, yb - r, 0), (xa + r, yb - r, 90), (xa + r, ya + r, 180)):
            for i in range(n + 1):
                a = math.radians(a0 + 90 * i / n)
                pts.append((cx + r * math.cos(a), cy + r * math.sin(a), 1e-6))   # 1e-6: keep as drawn
        return pts
    w = K.w
    return K.g.Prim([rrect(0, 0, W, H, R), rrect(w, w, W - w, H - w, R - w)])


def _slashed(K, base, H, R):
    W, sides, prims = base(K)
    w, s2 = K.w, math.sqrt(2)
    if s2 * (R - w) + 10 <= math.sqrt((R - 8) ** 2 - (w / 2) ** 2):
        return W, sides, prims + [_slash(K, W, H, R)]           # normal case: union of sharp shapes, then round
    # Light: union against the already-rounded ring; junctions stay sharp (ri would be 0.1 mm anyway)
    return W, sides, {"contours": K.g.outline([_round_ring(K, W, H, R), _slash(K, W, H, R)], K.rr, 1e-6)}


def Oslash(K):
    return _slashed(K, U.O, K.CAP, K.R_UC)


def oslash(K):
    return _slashed(K, L.o, K.XH, K.R_LC)


def AE(K):
    """Diagonal left leg into a vertical E stem; A crossbar low, E middle arm higher (two T-joins, no crossing)."""
    w, C = K.w, K.CAP
    xs = K.uc(300) + 1.7 * (w - 70)                # stem position: keeps the A-part counter >= w in Bold
    W = xs + w + K.uc(390)
    leg = K.edge((0, 0), (xs, C), "L")              # outer edge of the leg ends at the stem's top-left
    h = w / math.sin(math.atan2(C, xs))
    yb = 0.29 * C - w / 2
    k = xs / C
    xe = (k * (yb + w) + h + k * yb) / 2            # crossbar end: inside the leg over its full height
    return W, ("D", "A"), [leg, K.stem(xs, 0, C), K.bar(xs, W, C - w), K.bar(xs, W - 40, 360 - w / 2),
                           K.bar(xs, W, 0), K.rect(xe, yb, xs + w / 2, yb + w)]


def ae(K):
    """a and e sharing the middle stem; the a's top bar runs on into the e's top."""
    w, X = K.w, K.XH; R = K.R_LC
    Wa, We = 400, 400; Rb, bt, hx = 120, 325, 40
    xe = Wa - w; Wt = xe + We; eb = 285 - w / 2
    a_outer = [(0, 0, Rb), (0, bt, Rb), (Wa - w, bt), (Wa - w, X - w), (hx, X - w), (hx, X), (Wa, X), (Wa, 0)]
    a_hole = [(w, w, Rb - w), (w, bt - w, Rb - w), (Wa - w, bt - w), (Wa - w, w)]
    e_outer = [(Wt, 0), (Wt, w), (xe + w, w), (xe + w, eb), (Wt, eb), (Wt, X, R), (xe, X), (xe, 0)]
    e_hole = [(xe + w, eb + w), (xe + w, X - w), (Wt - w, X - w, R - w), (Wt - w, eb + w)]
    return Wt, ("O", "A"), [K.g.Prim([a_outer, a_hole]), K.g.Prim([e_outer, e_hole])]


GLYPHS = {"Å": ("uc", Aring), "Æ": ("uc", AE), "Ø": ("uc", Oslash),
          "å": ("lc", aring), "æ": ("lc", ae), "ø": ("lc", oslash)}
