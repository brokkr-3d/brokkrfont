# Copyright 2026 Brokkr 3D AS (https://brokkr.design), with Reserved Font Name "Brokkr".
# Part of the Font Software licensed under the SIL Open Font License 1.1 - see OFL.txt in the repository root.
"""Brokkr Sans 3D lowercase a-z. Same conventions as glyphs_upper.py."""
import math


def _vee(K, W, H, y0=0.0, flat=1.0):
    w = K.w; b = 0.3 * w
    for _ in range(10):
        h = w / math.sin(math.atan2(H - y0, W / 2 - b))
        b = flat * h / 2
    L = K.edge((0, H), (W / 2 - b, y0), "R")
    return (L, K.mirror(L, W)), h, b


def a(K):   # two-storey, as approved: bowl 325 high, bowl radius 120, hook radius 160
    w, X = K.w, K.XH; W = 440; Rb, Rh, bt, hx = 120, 160, 325, 40
    outer = [(0, 0, Rb), (0, bt, Rb), (W - w, bt), (W - w, X - w, Rh - w), (hx, X - w), (hx, X), (W, X, Rh), (W, 0)]
    hole = [(w, w, Rb - w), (w, bt - w, Rb - w), (W - w, bt - w), (W - w, w)]
    return W, ("O", "S"), [K.g.Prim([outer, hole])]


def b(K):
    W = 440; R = K.R_LC
    return W, ("S", "O"), [K.stem(0, 0, K.ASC), K.ring(0, 0, W, K.XH, br=R, tr=R)]


def c(K):
    W = 420; R = K.R_LC
    return W, ("O", "A"), [K.cshape(0, 0, W, K.XH, R_bl=R, R_tl=R)]


def d(K):
    W = 440; R = K.R_LC
    return W, ("O", "S"), [K.stem(W - K.w, 0, K.ASC), K.ring(0, 0, W, K.XH, bl=R, tl=R)]


def e(K):
    w, X = K.w, K.XH; W = 440; R = K.R_LC; eb = 285 - w / 2
    outer = [(W, 0), (W, w), (w, w, R - w), (w, eb), (W, eb), (W, X, R), (0, X, R), (0, 0, R)]
    hole = [(w, eb + w), (w, X - w, R - w), (W - w, X - w, R - w), (W - w, eb + w)]
    return W, ("O", "A"), [K.g.Prim([outer, hole])]


def f(K):
    w, X, A = K.w, K.XH, K.ASC; W = 290; fx = 60; Rf = 140
    return W, ("A", "A"), [K.poly((fx, 0), (fx + w, 0), (fx + w, A - w, Rf - w), (W, A - w), (W, A), (fx, A, Rf)),
                           K.rect(0, X - w, fx + w + 110, X)]


def g(K):   # single storey, squared hook, as approved
    w, X, Dd = K.w, K.XH, K.DESC; W = 440; Rb, Rh, hx = 160, 160, 40
    outer = [(0, X, Rb), (W, X), (W, Dd, Rh), (hx, Dd), (hx, Dd + w), (W - w, Dd + w, Rh - w), (W - w, 0), (0, 0, Rb)]
    hole = [(w, w, Rb - w), (w, X - w, Rb - w), (W - w, X - w), (W - w, w)]
    return W, ("O", "S"), [K.g.Prim([outer, hole])]


def h(K):
    w, X = K.w, K.XH; W = 440; R = K.R_LC
    return W, ("S", "S"), [K.poly((0, 0), (w, 0), (w, X - w), (W - w, X - w, R - w), (W - w, 0), (W, 0), (W, X, R),
                                  (w, X), (w, K.ASC), (0, K.ASC))]


def i(K):
    w = K.w; Di = K.Di; W = max(w, Di)
    return W, ("S", "S"), [K.stem((W - w) / 2, 0, K.XH), K.dot((W - Di) / 2, K.ASC - Di, Di)]


def j(K):
    w, X, Dd = K.w, K.XH, K.DESC; Di = K.Di; Wj = 220; Rj = 140
    W = Wj + max(0.0, (Di - w) / 2)
    hook = K.poly((0, Dd), (Wj, Dd, Rj), (Wj, X), (Wj - w, X), (Wj - w, Dd + w, Rj - w), (0, Dd + w))
    dot_x = Wj - w / 2 - Di / 2
    return W, (("stem", min(Wj - w, dot_x)), "S"), [hook, K.dot(dot_x, K.ASC - Di, Di)]


def k(K):
    w, X = K.w, K.XH; W = 440
    p_lo, p_top = (w, 0.32 * X), (W, X)
    arm = K.clip(K.edge(p_lo, p_top, "R", cut_a=("y", 0.32 * X - w)), xmin=w / 2)
    s = 0.38
    P = (p_lo[0] + s * (p_top[0] - p_lo[0]), p_lo[1] + s * (p_top[1] - p_lo[1]))
    q0, q1 = K.g.offset_pts(p_lo, p_top, w / 2)
    leg = K.edge((W, 0), P, "R", cut_a=("y", 0), cut_b=("line", q0, (q1[0] - q0[0], q1[1] - q0[1])))
    return W, ("S", "D"), [K.stem(0, 0, K.ASC), arm, leg]


def l(K):   # tail tells it apart from I and 1
    w = K.w; W = 210; Rl = 140
    return W, ("S", "A"), [K.poly((0, 0, Rl), (W, 0), (W, w), (w, w, Rl - w), (w, K.ASC), (0, K.ASC))]


def m(K):
    w, X = K.w, K.XH; W = 680; xm = W / 2; Rm = 150
    return W, ("S", "S"), [K.poly((0, 0), (w, 0), (w, X - w), (xm - w / 2, X - w), (xm - w / 2, 0), (xm + w / 2, 0),
                                  (xm + w / 2, X - w), (W - w, X - w, Rm - w), (W - w, 0), (W, 0), (W, X, Rm), (0, X))]


def n(K):
    w, X = K.w, K.XH; W = 440; R = K.R_LC
    return W, ("S", "S"), [K.poly((0, 0), (w, 0), (w, X - w), (W - w, X - w, R - w), (W - w, 0), (W, 0), (W, X, R), (0, X))]


def o(K):
    W = 440; R = K.R_LC
    return W, ("O", "O"), [K.ring(0, 0, W, K.XH, R, R, R, R)]


def p(K):
    W = 440; R = K.R_LC
    return W, ("S", "O"), [K.stem(0, K.DESC, K.XH), K.ring(0, 0, W, K.XH, br=R, tr=R)]


def q(K):
    W = 440; R = K.R_LC
    return W, ("O", "S"), [K.stem(W - K.w, K.DESC, K.XH), K.ring(0, 0, W, K.XH, bl=R, tl=R)]


def r(K):
    w, X = K.w, K.XH; W = 290
    return W, ("S", "A"), [K.poly((0, 0), (w, 0), (w, X - w), (W, X - w), (W, X), (0, X))]


def s(K):
    w, X = K.w, K.XH; W = 420; R = 140; ym = 275
    return W, ("O", "O"), [K.poly((0, 0), (W, 0, R), (W, ym + w / 2, R), (w, ym + w / 2, R - w), (w, X - w, R - w),
                                  (W, X - w), (W, X), (0, X, R), (0, ym - w / 2, R), (W - w, ym - w / 2, R - w),
                                  (W - w, w, R - w), (0, w))]


def t(K):
    w, X = K.w, K.XH; tx = 70; Rt = 140; yt = 690; xb = tx + w + 140; W = max(290, xb)
    return W, ("A", "A"), [K.poly((tx, 0, Rt), (W, 0), (W, w), (tx + w, w, Rt - w), (tx + w, yt), (tx, yt)),
                           K.rect(0, X - w, xb, X)]


def u(K):
    w, X = K.w, K.XH; W = 440; R = K.R_LC
    return W, ("S", "S"), [K.poly((0, 0, R), (W, 0), (W, X), (W - w, X), (W - w, w), (w, w, R - w), (w, X), (0, X))]


def v(K):
    W = 460
    (L, Rr), hh, bb = _vee(K, W, K.XH)
    return W, ("D", "D"), [L, Rr]


def w_(K):
    w, X = K.w, K.XH; W = 680; x1 = 0.255 * W
    b_ = a_ = 0.3 * w
    for _ in range(10):
        h1 = w / math.sin(math.atan2(X, x1 - b_)); h2 = w / math.sin(math.atan2(X, W / 2 - x1))
        b_ = 0.6 * max(h1, h2); a_ = h2 / 2
    s1 = K.edge((0, X), (x1 - b_, 0), "R")
    s2 = K.tan((x1 + b_, 0), (W / 2 - a_, X), ("y", 0), ("y", X), a_side="R")
    return W, ("D", "D"), [s1, s2, K.mirror(s2, W), K.mirror(s1, W)]


def x(K):
    W = 450
    dd = K.tan((0, 0), (W, K.XH), ("y", 0), ("y", K.XH), "L")
    return W, ("D", "D"), [dd, K.mirror(dd, W)]


def y(K):   # u with the g's squared descender
    w, X, Dd = K.w, K.XH, K.DESC; W = 440; R = K.R_LC; Rh, hx = 160, 40
    return W, ("S", "S"), [K.poly((0, X), (0, 0, R), (W - w, 0), (W - w, Dd + w, Rh - w), (hx, Dd + w), (hx, Dd),
                                  (W, Dd, Rh), (W, X), (W - w, X), (W - w, w), (w, w, R - w), (w, X))]


def z(K):
    w, X = K.w, K.XH; W = 420
    dd = K.clip(K.tan((0, w), (W, X - w), ("y", w / 2), ("y", X - w / 2), "L"), xmin=0, xmax=W)
    return W, ("A", "A"), [K.bar(0, W, 0), K.bar(0, W, X - w), dd]


GLYPHS = {ch: ("lc", fn) for ch, fn in {
    "a": a, "b": b, "c": c, "d": d, "e": e, "f": f, "g": g, "h": h, "i": i, "j": j, "k": k, "l": l, "m": m,
    "n": n, "o": o, "p": p, "q": q, "r": r, "s": s, "t": t, "u": u, "v": v, "w": w_, "x": x, "y": y, "z": z}.items()}
