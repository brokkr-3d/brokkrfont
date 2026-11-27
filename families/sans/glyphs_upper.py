"""Brokkr Sans 3D capitals A-Z. Each function f(K) -> (ink width, (left, right) spacing class, primitives).
Spacing classes: S straight stem, O round side, A open arm/terminal, D diagonal extreme, or a number."""
import math


def _vee(K, W, H, y0=0.0, flat=1.0):
    """Two diagonals from the top corners (0,H), (W,H) meeting at the centre at height y0
    with a flat foot `flat` times the horizontal stroke thickness h. Returns (left, right), h, half-foot."""
    w = K.w; b = 0.3 * w
    for _ in range(10):
        h = w / math.sin(math.atan2(H - y0, W / 2 - b))
        b = flat * h / 2
    L = K.edge((0, H), (W / 2 - b, y0), "R")
    return (L, K.mirror(L, W)), h, b


def A(K):
    w, C = K.w, K.CAP; W = 600
    (L, Rr), h, a = _vee(K, W, C)
    k = (W / 2 - a) / C                       # outer edge: x = k*y
    yb = 0.29 * C - w / 2                     # crossbar bottom
    xe = (k * (yb + w) + h + k * yb) / 2      # crossbar end: inside the leg over its full height
    return W, ("D", "D"), [K.flip(L, C), K.flip(Rr, C), K.rect(xe, yb, W - xe, yb + w)]


def B(K):
    w, C = K.w, K.CAP; W = 500; ym = 372
    Rw = 70; s = Rw + K.ri + 2                # waist: step just wide enough for the lower bowl's corner
    return W, ("S", "O"), [K.stem(0, 0, C), K.ring(0, ym - w / 2, W - s, C, tr=150),
                           K.ring(0, 0, W, ym + w / 2, br=170, tr=Rw)]


def C_(K):
    W = 500; R = K.R_UC
    return W, ("O", "A"), [K.cshape(0, 0, W, K.CAP, R_bl=R, R_tl=R)]


def D(K):
    W = 520; R = K.R_UC
    return W, ("S", "O"), [K.ring(0, 0, W, K.CAP, br=R, tr=R)]


def E(K):
    w, C = K.w, K.CAP; W = 450
    return W, ("S", "A"), [K.stem(0, 0, C), K.bar(0, W, C - w), K.bar(0, W - 40, 360 - w / 2), K.bar(0, W, 0)]


def F(K):
    w, C = K.w, K.CAP; W = 440
    return W, ("S", "A"), [K.stem(0, 0, C), K.bar(0, W, C - w), K.bar(0, W - 40, 345 - w / 2)]


def G_(K):
    w, C = K.w, K.CAP; W = 520; R = K.R_UC; yg, xg = 380, 280
    return W, ("O", "O"), [K.poly((0, 0, R), (W, 0, R), (W, yg), (xg, yg), (xg, yg - w), (W - w, yg - w),
                                  (W - w, w, R - w), (w, w, R - w), (w, C - w, R - w), (W, C - w), (W, C), (0, C, R))]


def H(K):
    w, C = K.w, K.CAP; W = 520
    return W, ("S", "S"), [K.stem(0, 0, C), K.stem(W - w, 0, C), K.rect(w / 2, C / 2 - w / 2, W - w / 2, C / 2 + w / 2)]


def I(K):
    return K.w, ("S", "S"), [K.stem(0, 0, K.CAP)]


def J(K):
    w, C = K.w, K.CAP; W = 440; R = 160; yj = 230
    return W, ("A", "S"), [K.poly((0, 0, R), (W, 0, R), (W, C), (W - w, C), (W - w, w, R - w), (w, w, R - w),
                                  (w, yj), (0, yj))]


def K_(K):
    w, C = K.w, K.CAP; W = 520
    p_lo, p_top = (w, 0.30 * C), (W, C)
    arm = K.clip(K.edge(p_lo, p_top, "R", cut_a=("y", 0.30 * C - w)), xmin=w / 2)
    s = 0.36
    P = (p_lo[0] + s * (p_top[0] - p_lo[0]), p_lo[1] + s * (p_top[1] - p_lo[1]))
    q0, q1 = K.g.offset_pts(p_lo, p_top, w / 2)            # arm centreline
    leg = K.edge((W, 0), P, "R", cut_a=("y", 0), cut_b=("line", q0, (q1[0] - q0[0], q1[1] - q0[1])))
    return W, ("S", "D"), [K.stem(0, 0, C), arm, leg]


def L(K):
    w, C = K.w, K.CAP; W = 430
    return W, ("S", "A"), [K.stem(0, 0, C), K.bar(0, W, 0)]


def M(K):
    w, C = K.w, K.CAP; W = 660
    (L, Rr), h, b = _vee(K, W, C, y0=0.38 * C)
    return W, ("S", "S"), [K.stem(0, 0, C), K.stem(W - w, 0, C), L, Rr]


def N(K):
    w, C = K.w, K.CAP; W = 540
    d = K.tan((0, C), (W, 0), ("y", C), ("y", 0), a_side="R")
    return W, ("S", "S"), [K.stem(0, 0, C), K.stem(W - w, 0, C), d]


def O(K):
    W = 520; R = K.R_UC
    return W, ("O", "O"), [K.ring(0, 0, W, K.CAP, R, R, R, R)]


def P(K):
    w, C = K.w, K.CAP; W = 490; yb = 0.40 * C - w / 2
    return W, ("S", "O"), [K.stem(0, 0, C), K.ring(0, yb, W, C, br=170, tr=170)]


def Q(K):
    w, C = K.w, K.CAP; W = 520; R = K.R_UC; e = 40
    # 45-degree tail through the bottom-right corner: both corner points sit on its centreline,
    # so the corner is fully absorbed and no short edges or squeezed radii remain
    s = 170 + 0.6 * w                                # inner end stays clear of the counter walls
    tail = K.stroke((W - s, s), (W + e, -e))
    return W + e + 0.36 * w + 2, ("O", "D"), [K.ring(0, 0, W, C, R, R, R, R), tail]


def R_(K):
    w, C = K.w, K.CAP; W = 510; yb = 0.40 * C - w / 2
    xj = max(W - 245, 3.4 * w)                       # leg meets the bowl here; keeps the gap to the stem >= w
    phi = math.atan2(yb, W - xj)
    br = min(170, (W - 10 - xj) - K.ri / math.tan(phi / 2) - 2)   # bowl corner radius that still fits
    leg = K.edge((W, 0), (xj, yb), "R", cut_a=("y", 0), cut_b=("y", yb + w / 2))
    return W, ("S", "D"), [K.stem(0, 0, C), K.ring(0, yb, W - 10, C, br=br, tr=170), leg]


def S(K):
    w, C = K.w, K.CAP; W = 490; R = 170; ym = 362
    return W, ("O", "O"), [K.poly((0, 0), (W, 0, R), (W, ym + w / 2, R), (w, ym + w / 2, R - w), (w, C - w, R - w),
                                  (W, C - w), (W, C), (0, C, R), (0, ym - w / 2, R), (W - w, ym - w / 2, R - w),
                                  (W - w, w, R - w), (0, w))]


def T(K):
    w, C = K.w, K.CAP; W = 520
    return W, ("A", "A"), [K.bar(0, W, C - w), K.stem(W / 2 - w / 2, 0, C - w / 2)]


def U(K):
    w, C = K.w, K.CAP; W = 520; R = K.R_UC
    return W, ("S", "S"), [K.poly((0, 0, R), (W, 0, R), (W, C), (W - w, C), (W - w, w, R - w), (w, w, R - w),
                                  (w, C), (0, C))]


def V(K):
    W = 580
    (L, Rr), h, b = _vee(K, W, K.CAP)
    return W, ("D", "D"), [L, Rr]


def W_(K):
    w, C = K.w, K.CAP; W = 840; x1 = 0.255 * W
    b = a = 0.3 * w
    for _ in range(10):   # feet a bit wider than one stroke so the two strokes' feet never form slivers
        h1 = w / math.sin(math.atan2(C, x1 - b)); h2 = w / math.sin(math.atan2(C, W / 2 - x1))
        b = 0.6 * max(h1, h2); a = h2 / 2
    s1 = K.edge((0, C), (x1 - b, 0), "R")
    s2 = K.tan((x1 + b, 0), (W / 2 - a, C), ("y", 0), ("y", C), a_side="R")
    return W, ("D", "D"), [s1, s2, K.mirror(s2, W), K.mirror(s1, W)]


def X(K):
    w, C = K.w, K.CAP; W = 540
    d = K.tan((0, 0), (W, C), ("y", 0), ("y", C), "L")
    return W, ("D", "D"), [d, K.mirror(d, W)]


def Y(K):
    w, C = K.w, K.CAP; W = 580; yy = 0.40 * C; xs = W / 2 - w / 2
    arm = K.clip(K.edge((0, C), (xs, yy), "R", cut_b=("y", yy - w)), xmax=W / 2)
    return W, ("D", "D"), [arm, K.mirror(arm, W), K.stem(xs, 0, yy + w)]


def Z(K):
    w, C = K.w, K.CAP; W = 490
    d = K.clip(K.tan((0, w), (W, C - w), ("y", w / 2), ("y", C - w / 2), "L"), xmin=0, xmax=W)
    return W, ("A", "A"), [K.bar(0, W, 0), K.bar(0, W, C - w), d]


GLYPHS = {c: ("uc", f) for c, f in {
    "A": A, "B": B, "C": C_, "D": D, "E": E, "F": F, "G": G_, "H": H, "I": I, "J": J, "K": K_, "L": L,
    "M": M, "N": N, "O": O, "P": P, "Q": Q, "R": R_, "S": S, "T": T, "U": U, "V": V, "W": W_, "X": X,
    "Y": Y, "Z": Z}.items()}
