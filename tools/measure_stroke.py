"""Thickest spot in every Brokkr Sans 3D glyph: 2 x the largest circle that fits inside the shape.
A clean straight or curve is 1.0 w; junctions run about 1.2-1.5 w; diagonal joins (V, W, M feet) more.
usage: python -I tools/measure_stroke.py <family> [Light,Regular,Bold] [chars]
"""
import importlib.util, math, os, sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
if "b3d_fontlib" not in sys.modules:               # shared loader: family from the first argument, paths
    _s = importlib.util.spec_from_file_location("b3d_fontlib", os.path.join(HERE, "fontlib.py"))
    _m = importlib.util.module_from_spec(_s); sys.modules["b3d_fontlib"] = _m; _s.loader.exec_module(_m)
FL = sys.modules["b3d_fontlib"]
G = FL.family()
STEP, CELL = 6.0, 40.0


def thickest(contours, w):
    polys = [G.geo.flatten(c, 10) for c in contours]
    segs = [(p[i - 1], p[i]) for p in polys for i in range(len(p))]
    bins = defaultdict(list)
    for s in segs:
        for i in range(int(min(s[0][0], s[1][0]) // CELL), int(max(s[0][0], s[1][0]) // CELL) + 1):
            for j in range(int(min(s[0][1], s[1][1]) // CELL), int(max(s[0][1], s[1][1]) // CELL) + 1):
                bins[(i, j)].append(s)
    reach = int(math.ceil(1.6 * w / CELL))
    xs = [p[0] for p in sum(polys, [])]; ys = [p[1] for p in sum(polys, [])]
    best, at = 0.0, None
    y = min(ys) + STEP / 2
    while y < max(ys):
        cuts = sorted(a[0] + (y - a[1]) * (b[0] - a[0]) / (b[1] - a[1]) for a, b in segs if (a[1] > y) != (b[1] > y))
        for x0, x1 in zip(cuts[0::2], cuts[1::2]):
            x = x0 + STEP / 2
            while x < x1:
                d = 1e9; ci, cj = int(x // CELL), int(y // CELL)
                for i in range(ci - reach, ci + reach + 1):
                    for j in range(cj - reach, cj + reach + 1):
                        for (ax, ay), (bx, by) in bins.get((i, j), ()):
                            dx, dy = bx - ax, by - ay; L2 = dx * dx + dy * dy or 1e-12
                            t = max(0.0, min(1.0, ((x - ax) * dx + (y - ay) * dy) / L2))
                            d = min(d, math.hypot(x - ax - t * dx, y - ay - t * dy))
                if d > best:
                    best, at = d, (x, y)
                x += STEP
        y += STEP
    return 2 * best, at


if __name__ == "__main__":
    weights = sys.argv[1].split(",") if len(sys.argv) > 1 else list(G.WEIGHTS)
    chars = sys.argv[2] if len(sys.argv) > 2 else None
    for wname in weights:
        w = G.WEIGHTS[wname]
        font = G.build(w, set(chars) if chars else None)
        rows = []
        for c, gl in font.items():
            if gl["contours"]:
                t, at = thickest(gl["contours"], w)
                rows.append((t / w, c, at))
        rows.sort(reverse=True)
        print(f"== {wname} (w={w}): thickest spots, worst first")
        print("   " + "  ".join(f"{c}:{r:.2f}" for r, c, at in rows[:24]))
        print(f"   median {sorted(r for r, _, _ in rows)[len(rows) // 2]:.2f} w")
