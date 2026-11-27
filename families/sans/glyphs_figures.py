# Copyright 2026 Brokkr 3D AS (https://brokkr.design), with Reserved Font Name "Brokkr".
# Part of the Font Software licensed under the SIL Open Font License 1.1 - see OFL.txt in the repository root.
"""Brokkr Sans 3D digits 0-9 and punctuation / symbols. Same conventions as glyphs_upper.py."""
import math


def _vee(K, W, H, y0=0.0, flat=1.0):
    w = K.w; b = 0.3 * w
    for _ in range(10):
        h = w / math.sin(math.atan2(H - y0, W / 2 - b))
        b = flat * h / 2
    L = K.edge((0, H), (W / 2 - b, y0), "R")
    return (L, K.mirror(L, W)), h, b


def _zig(K, W, H, ym, R):
    """Squared '2': top bar (terminal left), right side, middle bar, left side, bottom bar (terminal right)."""
    w = K.w
    return K.poly((0, 0), (W, 0), (W, w), (w, w), (w, ym - w / 2, R - w), (W, ym - w / 2, R), (W, H, R), (0, H),
                  (0, H - w), (W - w, H - w, R - w), (W - w, ym + w / 2, R - w), (0, ym + w / 2, R))


def _S(K, W, H, R, ym):
    w = K.w
    return K.poly((0, 0), (W, 0, R), (W, ym + w / 2, R), (w, ym + w / 2, R - w), (w, H - w, R - w), (W, H - w), (W, H),
                  (0, H, R), (0, ym - w / 2, R), (W - w, ym - w / 2, R - w), (W - w, w, R - w), (0, w))


# ---------------- digits ----------------
def zero(K):
    W = 460
    return W, ("O", "O"), [K.ring(0, 0, W, K.CAP, 170, 170, 170, 170)]


def one(K):
    w, C = K.w, K.CAP; W = 290
    # flag's upper edge starts exactly at the stem's top-left corner
    flag = K.clip(K.edge((W - w, C), (30, C - 160), "R", cut_a=("x", W - w / 2), cut_b=("perp",)), ymax=C)
    return W, ("A", "S"), [K.stem(W - w, 0, C), flag]


def two(K):
    return 470, ("A", "A"), [_zig(K, 470, K.CAP, 330, 160)]


def three(K):
    w, C = K.w, K.CAP; W = 470; ym, xm, R = 380, 130, 160
    Rw = 70; s = Rw + K.ri + 2
    lower = K.mirror(K.cshape(0, 0, W, ym + w / 2, R_bl=R, R_tl=Rw, top_to=W - xm, bot_to=W), W)
    Wu = W - s
    upper = K.mirror(K.cshape(0, ym - w / 2, Wu, C, R_bl=None, R_tl=R, top_to=Wu, bot_to=Wu - xm), Wu)
    return W, ("A", "O"), [lower, upper]


def four(K):
    w, C = K.w, K.CAP; W = 500; yc, R = 210, 140; xs = W - w - 60
    return W, ("O", "A"), [K.poly((0, yc, R), (W, yc), (W, yc + w), (w, yc + w, R - w), (w, C), (0, C)),
                           K.stem(xs, 0, C)]


def five(K):
    return 470, ("A", "O"), [K.flip(_zig(K, 470, K.CAP, K.CAP - 395, 160), K.CAP)]


def _six(K, W):
    w, C = K.w, K.CAP; yb, R = 430, 170
    return [K.ring(0, 0, W, yb, bl=R, br=R, tr=R),
            K.poly((0, yb / 2), (w, yb / 2), (w, C - w, R - w), (W, C - w), (W, C), (0, C, R))]


def six(K):
    return 470, ("O", "A"), _six(K, 470)


def seven(K):
    w, C = K.w, K.CAP; W = 460
    d = K.clip(K.edge((W, C - w), (200, 0), "L", cut_a=("y", C - w / 2), cut_b=("y", 0)), xmax=W)
    return W, ("A", "D"), [K.bar(0, W, C - w), d]


def eight(K):
    """Two stacked rounded boxes sharing the middle bar. Where their corners meet, the waist forms a notch
    with a small fillet. Counters are concentric with every outer curve, so the stroke stays exactly w."""
    w, C, ri = K.w, K.CAP, K.ri; g = K.g; W = 480; yb = 390
    Rb, Rt, Rm = 170, 150, 110
    c1 = (W - Rm, yb + w / 2 - Rm)                                   # lower box, top-right corner centre
    c2 = (W - Rm, yb - w / 2 + Rm)                                   # upper box, bottom-right corner centre
    F = (W - Rm + math.sqrt((Rm + ri) ** 2 - (Rm - w / 2) ** 2), yb)  # notch fillet centre
    T1 = (c1[0] + (F[0] - c1[0]) * Rm / (Rm + ri), c1[1] + (F[1] - c1[1]) * Rm / (Rm + ri))
    T2 = (c2[0] + (F[0] - c2[0]) * Rm / (Rm + ri), c2[1] + (F[1] - c2[1]) * Rm / (Rm + ri))
    ang = lambda p, c: math.atan2(p[1] - c[1], p[0] - c[0])
    mx = lambda p: (W - p[0], p[1])
    P = g.Path((W / 2, 0))
    P.L((W - Rb, 0)).A((W - Rb, Rb), Rb, 0)
    P.L((W, c1[1])).A(c1, Rm, ang(T1, c1)).A(F, ri, ang(T2, F), ccw=False).A(c2, Rm, 0)
    P.L((W, C - Rt)).A((W - Rt, C - Rt), Rt, math.pi / 2)
    P.L((Rt, C)).A((Rt, C - Rt), Rt, math.pi)
    c2m, c1m, Fm = mx(c2), mx(c1), mx(F)
    P.L((0, c2m[1])).A(c2m, Rm, ang(mx(T2), c2m)).A(Fm, ri, ang(mx(T1), Fm), ccw=False).A(c1m, Rm, math.pi)
    P.L((0, Rb)).A((Rb, Rb), Rb, 3 * math.pi / 2)
    lower = g.outline([g.rect(w, w, W - w, yb - w / 2, Rb - w, Rb - w, Rm - w, Rm - w)], ri, ri)[0]
    upper = g.outline([g.rect(w, yb + w / 2, W - w, C - w, Rm - w, Rm - w, Rt - w, Rt - w)], ri, ri)[0]
    return W, ("O", "O"), {"contours": [P.close(), g.reverse_contour(lower), g.reverse_contour(upper)]}


def nine(K):
    return 470, ("A", "O"), [K.rot(p, 470, K.CAP) for p in _six(K, 470)]


# ---------------- punctuation ----------------
def period(K):
    return K.D, ("S", "S"), [K.dot(0, 0)]


CSX = 50   # comma slant


def _comma(K):
    """Square dot sheared down-left into a tail of the same width (no slivers at the joint)."""
    D = K.D; yl = D + 40
    return K.poly((0, -yl), (D, -yl), (D + CSX, 0), (D + CSX, D), (CSX, D), (CSX, 0))


def comma(K):
    return K.D + CSX, ("S", "S"), [_comma(K)]


def colon(K):
    return K.D, ("S", "S"), [K.dot(0, 0), K.dot(0, K.XH - K.D)]


def semicolon(K):
    return K.D + CSX, ("S", "S"), [_comma(K), K.dot(CSX, K.XH - K.D)]


def exclam(K):
    w, D = K.w, K.D; g = max(w, 90)
    return D, ("S", "S"), [K.rect((D - w) / 2, D + g, (D + w) / 2, K.CAP), K.dot(0, 0)]


def question(K):
    w, C, D = K.w, K.CAP, K.D; W = 420; R = 150; ym = 360; xc = 190; g = max(w, 90)
    hook = K.poly((0, C - w), (W - w, C - w, R - w), (W - w, ym + w / 2, R - w), (xc - w / 2, ym + w / 2),
                  (xc - w / 2, ym - w / 2), (W, ym - w / 2, R), (W, C, R), (0, C))
    return W, ("A", "O"), [hook, K.rect(xc - w / 2, D + g, xc + w / 2, ym), K.dot(xc - D / 2, 0)]


def quotesingle(K):
    return K.w, ("S", "S"), [K.stem(0, K.CAP - 230, K.CAP)]


def quotedbl(K):
    w = K.w; gap = max(w, 80)
    return 2 * w + gap, ("S", "S"), [K.stem(0, K.CAP - 230, K.CAP), K.stem(w + gap, K.CAP - 230, K.CAP)]


def hyphen(K):
    return 250, ("A", "A"), [K.bar(0, 250, 290 - K.w / 2)]


def parenleft(K):
    return 210, ("O", "A"), [K.cshape(0, -140, 210, 760, R_bl=150, R_tl=150)]


def parenright(K):
    return 210, ("A", "O"), [K.mirror(K.cshape(0, -140, 210, 760, R_bl=150, R_tl=150), 210)]


def bracketleft(K):
    return 190, ("S", "A"), [K.cshape(0, -140, 190, 760)]


def bracketright(K):
    return 190, ("A", "S"), [K.mirror(K.cshape(0, -140, 190, 760), 190)]


def _brace(K):
    w = K.w; W = 250; xv = 80; R = 140; y0, y1 = -140, 760; ym = (y0 + y1) / 2
    return W, [K.cshape(xv, y0, W, y1, R_bl=R, R_tl=R), K.rect(0, ym - w / 2, xv + w / 2, ym + w / 2)]


def braceleft(K):
    W, ps = _brace(K)
    return W, ("A", "A"), ps


def braceright(K):
    W, ps = _brace(K)
    return W, ("A", "A"), [K.mirror(p, W) for p in ps]


def slash(K):
    W = 340
    return W, ("D", "D"), [K.tan((0, -140), (W, 760), ("y", -140), ("y", 760), "L")]


def backslash(K):
    W = 340
    return W, ("D", "D"), [K.mirror(K.tan((0, -140), (W, 760), ("y", -140), ("y", 760), "L"), W)]


def bar(K):
    return K.w, ("S", "S"), [K.stem(0, -140, 760)]


def underscore(K):
    return 500, ("A", "A"), [K.bar(0, 500, -170)]


def plus(K):
    w = K.w; W = 440; cy = 300
    return W, ("A", "A"), [K.stem(W / 2 - w / 2, cy - W / 2, cy + W / 2), K.rect(0, cy - w / 2, W, cy + w / 2)]


def equal(K):
    w = K.w; W = 440; cy = 300; g = max(w, 80)
    return W, ("A", "A"), [K.bar(0, W, cy + g / 2), K.bar(0, W, cy - g / 2 - w)]


def _less(K):
    W, cy, hh = 400, 300, 220
    arm = K.clip(K.stroke((0, cy), (W, cy + hh), ("x", -K.w), ("x", W)), xmin=0)
    return W, [arm, K.flip(arm, 2 * cy)]


def less(K):
    W, ps = _less(K)
    return W, ("D", "A"), ps


def greater(K):
    W, ps = _less(K)
    return W, ("A", "D"), [K.mirror(p, W) for p in ps]


def asterisk(K):
    w = K.w; L = 190 + 0.3 * w; cy = 520
    dx, dy = L * math.cos(math.radians(30)), L * math.sin(math.radians(30))
    W = 2 * (dx + w / 4) + 4; cx = W / 2
    d1 = K.stroke((cx - dx, cy - dy), (cx + dx, cy + dy))
    return W, ("A", "A"), [K.stem(cx - w / 2, cy - L, cy + L), d1, K.mirror(d1, W)]


def percent(K):
    w, C = K.w, K.CAP; rw = max(200, 3 * w + 30); rh = max(300, 3 * w + 30); R = max(90, 1.3 * w)
    W = 2 * rw + max(160, 1.8 * w)
    return W, ("O", "O"), [K.ring(0, C - rh, rw, C, R, R, R, R), K.ring(W - rw, 0, W, rh, R, R, R, R),
                           K.tan((0, 0), (W, C), ("y", 0), ("y", C), "L")]


def ampersand(K):
    """Classic & topology, squared: closed upper loop; lower bowl (left side, bottom, right side ending in a
    tail below the loop); leg from the loop's bottom-right corner to the bottom right, crossing the bowl."""
    w, C = K.w, K.CAP; R = max(100, 1.3 * w); Rb = 150
    lw, lh = max(230, 3 * w + 20), max(250, 3 * w + 20); lx = 70; Rtl = lx - K.ri - 2
    y0 = C - lh                                       # loop bottom edge
    yt = y0 - w - 15                                  # tail top: gap >= w below the loop
    yc = 0.5 * yt + 0.3 * w                           # leg crosses the bowl's right side here
    ctop = (lx + w / 2, y0 + w / 2)                   # leg starts in the loop's bottom-left corner ...
    xb = ctop[0] + (ctop[1] - yc) + w / 2             # ... runs at 45 degrees to the bowl's right side ...
    ccr = (xb - w / 2, yc)
    xf = ctop[0] + (ccr[0] - ctop[0]) * ctop[1] / (ctop[1] - ccr[1])   # ... and on to the baseline
    h = w / math.sin(math.atan2(ctop[1], xf - ctop[0]))
    W = xf + h / 2
    loop = K.ring(lx, y0, lx + lw, C, tr=R, tl=R)
    bowl = K.poly((0, 0, 170), (xb, 0, Rb), (xb, yt), (xb - w, yt), (xb - w, w, Rb - w), (w, w, 170 - w),
                  (w, y0), (lx + w, y0), (lx + w, y0 + w), (0, y0 + w, Rtl))
    leg = K.stroke(ctop, (xf, 0), ("y", y0 + w / 2), ("y", 0))
    return W, ("O", "D"), [loop, bowl, leg]


def at(K):
    w = K.w; W = max(720, 9 * w + 40); y0, y1 = -130, 690
    g = max(w, 0.13 * W)                             # gap between the outer ring and the inner bowl
    Ro, Rc, Ri = 170, max(120, 1.3 * w), max(110, 1.3 * w)
    xl, xr, yc, yt = w + g, W - w - g, y0 + w + g, y1 - w - g
    xt = 0.70 * W
    outer = K.poly((xt, y0), (xt, y0 + w), (w, y0 + w, Ro - w), (w, y1 - w, Ro - w), (W - w, y1 - w, Ro - w),
                   (W - w, yc + w, Rc - w), (xr - w / 2, yc + w), (xr - w / 2, yc), (W, yc, Rc), (W, y1, Ro),
                   (0, y1, Ro), (0, y0, Ro))
    return W, ("O", "O"), [outer, K.ring(xl, yc, xr, yt, bl=Ri, tr=Ri, tl=Ri)]


def numbersign(K):
    w = K.w; x1 = 110; W = max(520, 2 * x1 + 3 * w + 20); y0, y1 = 40, 660
    return W, ("A", "A"), [K.stem(x1, y0, y1), K.stem(W - x1 - w, y0, y1), K.bar(0, W, 220 - w / 2), K.bar(0, W, 440 - w / 2)]


def dollar(K):
    w, C = K.w, K.CAP; W = 490
    return W, ("O", "O"), [_S(K, W, C, 150, 362), K.rect(W / 2 - w / 2, C - w / 2, W / 2 + w / 2, C + 90),
                           K.rect(W / 2 - w / 2, -90, W / 2 + w / 2, w / 2)]


def asciitilde(K):
    w = K.w; R = 1.3 * w + 10; y0 = 300 - (2 * R + 10) / 2; y1 = y0 + 2 * R + 10; W = max(400, 4 * R + w)
    return W, ("A", "A"), [K.poly((0, y0), (W / 2 + w / 2, y0, R), (W / 2 + w / 2, y1 - w, R - w), (W, y1 - w), (W, y1),
                                  (W / 2 - w / 2, y1, R), (W / 2 - w / 2, y0 + w, R - w), (0, y0 + w))]


def asciicircum(K):
    C = K.CAP; W = 360; y0 = 360
    (L, Rr), h, b = _vee(K, W, C, y0=y0)
    return W, ("D", "D"), [K.flip(L, C + y0), K.flip(Rr, C + y0)]


def grave(K):
    w, C = K.w, K.CAP; W = 200
    return W, ("A", "A"), [K.clip(K.stroke((w / 2, C - w / 2), (W - w / 2, C - 170)), xmin=0, xmax=W, ymax=C)]


GLYPHS = {ch: ("uc", fn) for ch, fn in {
    "0": zero, "1": one, "2": two, "3": three, "4": four, "5": five, "6": six, "7": seven, "8": eight,
    "9": nine}.items()}
GLYPHS.update({ch: ("lc", fn) for ch, fn in {
    ".": period, ",": comma, ":": colon, ";": semicolon, "!": exclam, "?": question, "'": quotesingle,
    '"': quotedbl, "-": hyphen, "(": parenleft, ")": parenright, "[": bracketleft, "]": bracketright,
    "{": braceleft, "}": braceright, "/": slash, "\\": backslash, "|": bar, "_": underscore, "+": plus,
    "=": equal, "<": less, ">": greater, "*": asterisk, "%": percent, "&": ampersand, "@": at,
    "#": numbersign, "$": dollar, "~": asciitilde, "^": asciicircum, "`": grave}.items()})
