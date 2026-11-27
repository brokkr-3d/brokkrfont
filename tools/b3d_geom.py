"""Brokkr 3D geometry engine.

Glyphs are built from *primitives*: sharp polygons whose vertices carry an optional
corner radius.  union() merges overlapping primitives into clean outlines (outer
contours CCW, holes CW, material always on the left), then fillet() rounds every
corner with a true circular arc:
  * explicit radius from the primitive, when that vertex keeps its convexity
  * otherwise rr for convex corners (stroke ends) and ri for concave ones (junctions)
"""
import math

EPS = 1e-6


def _cross(ax, ay, bx, by):
    return ax * by - ay * bx


def area(c):
    return 0.5 * sum(c[i - 1][0] * c[i][1] - c[i][0] * c[i - 1][1] for i in range(len(c)))


class Prim:
    """One primitive: list of contours of (x, y, r). The largest contour is the outer one."""

    def __init__(self, contours):
        cs = [[(float(p[0]), float(p[1]), p[2] if len(p) > 2 else None) for p in c] for c in contours]
        cs.sort(key=lambda c: -abs(area(c)))
        self.contours = []
        for k, c in enumerate(cs):
            a = area(c)
            if (k == 0 and a < 0) or (k > 0 and a > 0):
                c = c[::-1]
            self.contours.append(c)


# ---------- primitive helpers ----------
def poly(*pts):
    return Prim([pts])


def rect(x0, y0, x1, y1, bl=None, br=None, tr=None, tl=None):
    return Prim([[(x0, y0, bl), (x1, y0, br), (x1, y1, tr), (x0, y1, tl)]])


def ring(x0, y0, x1, y1, w, bl=None, br=None, tr=None, tl=None):
    """Rounded-rectangle ring of stroke w. Outer radii given; inner radius = outer - w
    (concentric) where an outer radius is given, otherwise the junction fillet."""
    inner = lambda R: (R - w) if R and R - w > 0 else None
    return Prim([[(x0, y0, bl), (x1, y0, br), (x1, y1, tr), (x0, y1, tl)],
                 [(x0 + w, y0 + w, inner(bl)), (x0 + w, y1 - w, inner(tl)),
                  (x1 - w, y1 - w, inner(tr)), (x1 - w, y0 + w, inner(br))]])


def isect(p, d, q, e):
    """Intersection of lines p + s*d and q + t*e."""
    den = _cross(d[0], d[1], e[0], e[1])
    s = _cross(q[0] - p[0], q[1] - p[1], e[0], e[1]) / den
    return (p[0] + s * d[0], p[1] + s * d[1])


def _cutline(cut, p, n):
    if cut is None or cut[0] == "perp":
        return p, n                       # perpendicular end through p
    if cut[0] == "line":                  # ('line', point, direction)
        return cut[1], cut[2]
    kind, v = cut
    return ((0.0, v), (1.0, 0.0)) if kind == "y" else ((v, 0.0), (0.0, 1.0))


def stroke(p0, p1, w, cut0=None, cut1=None, r=None):
    """Straight stroke of width w along centreline p0->p1. Ends are perpendicular,
    or cut by a horizontal ('y', value) / vertical ('x', value) line."""
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    L = math.hypot(dx, dy); u = (dx / L, dy / L); n = (-u[1], u[0])
    h = w / 2
    lp = (p0[0] + n[0] * h, p0[1] + n[1] * h); rp = (p0[0] - n[0] * h, p0[1] - n[1] * h)
    c0 = _cutline(cut0, p0, n); c1 = _cutline(cut1, p1, n)
    R0 = isect(rp, u, *c0); R1 = isect(rp, u, *c1); L1 = isect(lp, u, *c1); L0 = isect(lp, u, *c0)
    return Prim([[(R0[0], R0[1], r), (R1[0], R1[1], r), (L1[0], L1[1], r), (L0[0], L0[1], r)]])


def edge_stroke(a, b, w, side, cut_a=None, cut_b=None):
    """Stroke whose `side` ('L' or 'R', looking from a to b) edge is exactly the line a-b.
    Ends cut horizontally at a.y and b.y unless other cuts are given."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    L = math.hypot(dx, dy); n = (-dy / L, dx / L)
    s = -1 if side == "L" else 1          # centreline lies on the other side of the edge
    o = (n[0] * s * w / 2, n[1] * s * w / 2)
    return stroke((a[0] + o[0], a[1] + o[1]), (b[0] + o[0], b[1] + o[1]), w,
                  cut_a or ("y", a[1]), cut_b or ("y", b[1]))


def tangent_stroke(a, b, w, cut_a, cut_b, a_side="L"):
    """Stroke with point a on one edge and point b on the other (looking a->b):
    a_side='L' puts a on the left edge and b on the right edge, 'R' the reverse.
    Used for diagonals that must meet two corner points exactly. Cuts as in stroke()."""
    vx, vy = b[0] - a[0], b[1] - a[1]
    D = math.hypot(vx, vy); th = math.asin(min(1.0, w / D))
    base = math.atan2(vy, vx)
    sgn = 1 if a_side == "L" else -1
    ang = base + sgn * th
    u = (math.cos(ang), math.sin(ang)); n = (-u[1], u[0])
    c = (a[0] - sgn * n[0] * w / 2, a[1] - sgn * n[1] * w / 2)
    return stroke(c, (c[0] + u[0] * D, c[1] + u[1] * D), w, cut_a, cut_b)


def line_x(p, q, y):
    """x where the line through p and q crosses height y."""
    return p[0] + (y - p[1]) * (q[0] - p[0]) / (q[1] - p[1])


def offset_pts(p, q, d):
    """The line p-q shifted d to its left (looking p->q); returns the two shifted points."""
    L = math.dist(p, q); n = (-(q[1] - p[1]) / L, (q[0] - p[0]) / L)
    return (p[0] + n[0] * d, p[1] + n[1] * d), (q[0] + n[0] * d, q[1] + n[1] * d)


def transform(prim, f):
    return Prim([[(*f(x, y), r) for x, y, r in c] for c in prim.contours])


def flip_y(prim, H):
    return transform(prim, lambda x, y: (x, H - y))


def rot180(prim, W, H):
    return transform(prim, lambda x, y: (W - x, H - y))


def cshape(x0, y0, x1, y1, w, R_bl=None, R_tl=None, top_to=None, bot_to=None):
    """C opening to the right: left side, top arm to top_to, bottom arm to bot_to.
    Outer left corners R_bl / R_tl (None = square); inner corners concentric."""
    top_to = x1 if top_to is None else top_to
    bot_to = x1 if bot_to is None else bot_to
    inner = lambda R: (R - w) if R else None
    return poly((x0, y0, R_bl), (bot_to, y0), (bot_to, y0 + w), (x0 + w, y0 + w, inner(R_bl)),
                (x0 + w, y1 - w, inner(R_tl)), (top_to, y1 - w), (top_to, y1), (x0, y1, R_tl))


def clip(prim, xmin=-1e9, xmax=1e9, ymin=-1e9, ymax=1e9):
    """Clip a single-contour primitive to a box (Sutherland-Hodgman). New corners get auto radius."""
    pts = prim.contours[0]
    for axis, lim, keep_lo in ((0, xmin, False), (0, xmax, True), (1, ymin, False), (1, ymax, True)):
        out = []
        inside = (lambda p: p[axis] <= lim + EPS) if keep_lo else (lambda p: p[axis] >= lim - EPS)
        for i in range(len(pts)):
            a, b = pts[i - 1], pts[i]
            if inside(b):
                if not inside(a):
                    t = (lim - a[axis]) / (b[axis] - a[axis])
                    out.append((a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1]), None))
                out.append(b)
            elif inside(a):
                t = (lim - a[axis]) / (b[axis] - a[axis])
                out.append((a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1]), None))
        pts = out
    return Prim([pts])


def mirror_x(prim, W):
    return Prim([[(W - x, y, r) for x, y, r in c] for c in prim.contours])


# ---------- union ----------
class _Pts:
    def __init__(self, tol=1e-5):
        self.tol, self.grid, self.xy = tol, {}, []

    def get(self, x, y):
        k = (round(x / (self.tol * 4)), round(y / (self.tol * 4)))
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for i in self.grid.get((k[0] + dx, k[1] + dy), ()):
                    if abs(self.xy[i][0] - x) <= self.tol and abs(self.xy[i][1] - y) <= self.tol:
                        return i
        self.xy.append((x, y)); self.grid.setdefault(k, []).append(len(self.xy) - 1)
        return len(self.xy) - 1


def _classify(mx, my, prim):
    """'in' / 'out' / (dx, dy) of the boundary edge the point lies on."""
    wn = 0
    for c in prim.contours:
        n = len(c)
        for i in range(n):
            ax, ay = c[i][0], c[i][1]; bx, by = c[(i + 1) % n][0], c[(i + 1) % n][1]
            ex, ey = bx - ax, by - ay
            L2 = ex * ex + ey * ey
            t = max(0.0, min(1.0, ((mx - ax) * ex + (my - ay) * ey) / L2))
            if math.hypot(mx - ax - t * ex, my - ay - t * ey) < 1e-5:
                return (ex, ey)
            if ay <= my < by and _cross(ex, ey, mx - ax, my - ay) > 0:
                wn += 1
            elif by <= my < ay and _cross(ex, ey, mx - ax, my - ay) < 0:
                wn -= 1
    return "in" if wn != 0 else "out"


def union(prims):
    E = []
    for pid, p in enumerate(prims):
        for c in p.contours:
            for i in range(len(c)):
                a, b = c[i], c[(i + 1) % len(c)]
                if math.hypot(b[0] - a[0], b[1] - a[1]) > EPS:
                    E.append((a[0], a[1], b[0], b[1], pid))
    splits = [[0.0, 1.0] for _ in E]
    for i in range(len(E)):
        ax, ay, bx, by, pi = E[i]
        rx, ry = bx - ax, by - ay; L1 = math.hypot(rx, ry)
        for j in range(i + 1, len(E)):
            cx, cy, dx, dy, pj = E[j]
            if pi == pj or max(ax, bx) < min(cx, dx) - EPS or max(cx, dx) < min(ax, bx) - EPS \
                    or max(ay, by) < min(cy, dy) - EPS or max(cy, dy) < min(ay, by) - EPS:
                continue
            sx, sy = dx - cx, dy - cy; L2 = math.hypot(sx, sy)
            den = _cross(rx, ry, sx, sy)
            if abs(den) <= 1e-9 * L1 * L2:
                if abs(_cross(rx, ry, cx - ax, cy - ay)) / L1 > EPS:
                    continue
                for px, py in ((cx, cy), (dx, dy)):
                    t = ((px - ax) * rx + (py - ay) * ry) / (L1 * L1)
                    if EPS / L1 < t < 1 - EPS / L1:
                        splits[i].append(t)
                for px, py in ((ax, ay), (bx, by)):
                    u = ((px - cx) * sx + (py - cy) * sy) / (L2 * L2)
                    if EPS / L2 < u < 1 - EPS / L2:
                        splits[j].append(u)
            else:
                t = _cross(cx - ax, cy - ay, sx, sy) / den
                u = _cross(cx - ax, cy - ay, rx, ry) / den
                if -EPS / L1 <= t <= 1 + EPS / L1 and -EPS / L2 <= u <= 1 + EPS / L2:
                    splits[i].append(min(1.0, max(0.0, t))); splits[j].append(min(1.0, max(0.0, u)))
    P = _Pts()
    pieces = []
    for (ax, ay, bx, by, pid), ts in zip(E, splits):
        ids = []
        for t in sorted(ts):
            k = P.get(ax + t * (bx - ax), ay + t * (by - ay))
            if not ids or ids[-1] != k:
                ids.append(k)
        for k0, k1 in zip(ids, ids[1:]):
            pieces.append((k0, k1, pid))
    keep = []
    for k0, k1, pid in pieces:
        (x0, y0), (x1, y1) = P.xy[k0], P.xy[k1]
        mx, my = (x0 + x1) / 2, (y0 + y1) / 2
        ok = True
        for j, pr in enumerate(prims):
            if j == pid:
                continue
            st = _classify(mx, my, pr)
            if st == "in":
                ok = False; break
            if st != "out":
                same = st[0] * (x1 - x0) + st[1] * (y1 - y0) > 0
                if not same or j < pid:
                    ok = False; break
        if ok:
            keep.append((k0, k1))
    # remove exact duplicates (same piece kept twice)
    keep = list(dict.fromkeys(keep))
    out_of = {}
    for idx, (k0, k1) in enumerate(keep):
        out_of.setdefault(k0, []).append(idx)
    used = [False] * len(keep)
    loops = []
    for s in range(len(keep)):
        if used[s]:
            continue
        loop = []; cur = s
        while not used[cur]:
            used[cur] = True
            k0, k1 = keep[cur]
            loop.append(k0)
            cands = [c for c in out_of.get(k1, []) if not used[c]]
            if not cands:
                break
            if len(cands) > 1:
                (ax, ay), (bx, by) = P.xy[k0], P.xy[k1]
                din = (bx - ax, by - ay)

                def turn(c):
                    (qx, qy) = P.xy[keep[c][1]]
                    d = (qx - bx, qy - by)
                    return math.atan2(_cross(din[0], din[1], d[0], d[1]), din[0] * d[0] + din[1] * d[1])
                cands.sort(key=turn, reverse=True)
            cur = cands[0]
        pts = [P.xy[k] for k in loop]
        # drop collinear / duplicate points
        changed = True
        while changed and len(pts) > 3:
            changed = False
            for i in range(len(pts)):
                a, b, c = pts[i - 1], pts[i], pts[(i + 1) % len(pts)]
                cr = _cross(b[0] - a[0], b[1] - a[1], c[0] - b[0], c[1] - b[1])
                if abs(cr) < 1e-7 * (1 + math.hypot(b[0] - a[0], b[1] - a[1]) * math.hypot(c[0] - b[0], c[1] - b[1])) \
                        and (b[0] - a[0]) * (c[0] - b[0]) + (b[1] - a[1]) * (c[1] - b[1]) >= 0:
                    pts.pop(i); changed = True; break
        if len(pts) >= 3 and abs(area(pts)) > 1e-3:
            loops.append(pts)
    return loops


# ---------- fillets ----------
def _convex(a, b, c):
    return _cross(b[0] - a[0], b[1] - a[1], c[0] - b[0], c[1] - b[1]) > 0


def outline(prims, rr, ri, report=None):
    """Union + fillet. Returns contours as (start, [('L', p) | ('C', c1, c2, p), ...])."""
    loops = union(prims)
    orig = []
    for p in prims:
        for c in p.contours:
            for i in range(len(c)):
                orig.append((c[i][0], c[i][1], c[i][2], _convex(c[i - 1], c[i], c[(i + 1) % len(c)])))
    res = []
    for pts in loops:
        n = len(pts)
        rad, tan, geo = [], [], []
        for i in range(n):
            a, b, c = pts[i - 1], pts[i], pts[(i + 1) % n]
            cv = _convex(a, b, c)
            r = None
            for ox, oy, orr, ocv in orig:
                if abs(ox - b[0]) < 1e-4 and abs(oy - b[1]) < 1e-4 and ocv == cv and orr is not None and orr > 0:
                    r = orr; break
            if r is None:
                r = rr if cv else ri
            u1 = (a[0] - b[0], a[1] - b[1]); l1 = math.hypot(*u1); u1 = (u1[0] / l1, u1[1] / l1)
            u2 = (c[0] - b[0], c[1] - b[1]); l2 = math.hypot(*u2); u2 = (u2[0] / l2, u2[1] / l2)
            phi = math.acos(max(-1.0, min(1.0, u1[0] * u2[0] + u1[1] * u2[1])))
            t = r / math.tan(phi / 2) if r > 0 and phi < math.pi - 1e-6 else 0.0
            rad.append(r); tan.append(t); geo.append((b, u1, u2, phi))
        scale = [1.0] * n
        for i in range(n):
            j = (i + 1) % n
            L = math.dist(pts[i], pts[j])
            if tan[i] + tan[j] > L + 1e-9:
                s = L / (tan[i] + tan[j])
                scale[i] = min(scale[i], s); scale[j] = min(scale[j], s)
        segs, start = [], None
        for i in range(n):
            b, u1, u2, phi = geo[i]
            if scale[i] < 0.99 and report is not None:
                report.append(f"radius {rad[i]:.1f} at ({b[0]:.0f},{b[1]:.0f}) clamped to {rad[i] * scale[i]:.1f}")
            r, t = rad[i] * scale[i], tan[i] * scale[i]
            p1 = (b[0] + u1[0] * t, b[1] + u1[1] * t)
            p2 = (b[0] + u2[0] * t, b[1] + u2[1] * t)
            if start is None:
                start = p1
            else:
                segs.append(("L", p1))
            if t > 1e-9:
                k = 4 / 3 * math.tan((math.pi - phi) / 4) * r
                segs.append(("C", (p1[0] - u1[0] * k, p1[1] - u1[1] * k),
                             (p2[0] - u2[0] * k, p2[1] - u2[1] * k), p2))
        segs.append(("L", start))
        res.append((start, segs))
    return res


def arc_segs(c, r, a0, a1):
    """Cubic segments for a circular arc around c from angle a0 to a1 (radians; a1 < a0 = clockwise)."""
    n = max(1, int(math.ceil(abs(a1 - a0) / (math.pi / 2) - 1e-9)))
    da = (a1 - a0) / n; k = 4 / 3 * math.tan(da / 4) * r
    segs = []
    for i in range(n):
        t0, t1 = a0 + i * da, a0 + (i + 1) * da
        p0 = (c[0] + r * math.cos(t0), c[1] + r * math.sin(t0))
        p1 = (c[0] + r * math.cos(t1), c[1] + r * math.sin(t1))
        segs.append(("C", (p0[0] - k * math.sin(t0), p0[1] + k * math.cos(t0)),
                     (p1[0] + k * math.sin(t1), p1[1] - k * math.cos(t1)), p1))
    return segs


class Path:
    """Explicit outline builder (lines + true arcs) for shapes the union cannot make, e.g. notches
    where two rounded corners meet. Produces the same contour format as outline()."""

    def __init__(self, start):
        self.start = self.cur = start; self.segs = []

    def L(self, p):
        self.segs.append(("L", p)); self.cur = p; return self

    def A(self, c, r, a_end, ccw=True):
        a0 = math.atan2(self.cur[1] - c[1], self.cur[0] - c[0])
        a1 = a_end
        if ccw:
            while a1 <= a0 + 1e-9: a1 += 2 * math.pi
        else:
            while a1 >= a0 - 1e-9: a1 -= 2 * math.pi
        self.segs += arc_segs(c, r, a0, a1)
        self.cur = self.segs[-1][3]; return self

    def close(self):
        self.segs.append(("L", self.start)); return (self.start, self.segs)


def reverse_contour(contour):
    start, segs = contour
    pts = [start]
    for s in segs:
        pts.append(s[-1])
    out = []
    for i in range(len(segs) - 1, -1, -1):
        s, p_prev = segs[i], pts[i]
        out.append(("L", p_prev) if s[0] == "L" else ("C", s[2], s[1], p_prev))
    return (pts[-1], out)


def flatten(contour, n=12):
    start, segs = contour
    pts, cur = [start], start
    for s in segs:
        if s[0] == "L":
            cur = s[1]; pts.append(cur)
        else:
            (x0, y0), (x1, y1), (x2, y2), (x3, y3) = cur, s[1], s[2], s[3]
            for i in range(1, n + 1):
                t = i / n; u = 1 - t
                pts.append((u ** 3 * x0 + 3 * u * u * t * x1 + 3 * u * t * t * x2 + t ** 3 * x3,
                            u ** 3 * y0 + 3 * u * u * t * y1 + 3 * u * t * t * y2 + t ** 3 * y3))
            cur = s[3]
    out = [p for i, p in enumerate(pts) if i == 0 or math.dist(p, pts[i - 1]) > 1e-9]
    if len(out) > 1 and math.dist(out[0], out[-1]) < 1e-9:
        out.pop()
    return out


def svg_d(contours, dx=0.0, dy=0.0, flip=True):
    f = lambda p: (p[0] + dx, (-p[1] if flip else p[1]) + dy)
    out = []
    for start, segs in contours:
        x, y = f(start); out.append(f"M{x:.2f} {y:.2f}")
        for s in segs:
            if s[0] == "L":
                x, y = f(s[1]); out.append(f"L{x:.2f} {y:.2f}")
            else:
                (a, b), (c, d), (e, g) = f(s[1]), f(s[2]), f(s[3])
                out.append(f"C{a:.2f} {b:.2f} {c:.2f} {d:.2f} {e:.2f} {g:.2f}")
        out.append("Z")
    return " ".join(out)
