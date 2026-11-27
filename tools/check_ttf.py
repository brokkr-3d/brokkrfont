# Copyright 2026 Brokkr 3D AS (https://brokkr.design).
# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. If a copy of the MPL
# was not distributed with this file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Independent check of the built fonts: reads fonts/*.ttf only (not the glyph source).

python -I tools/check_ttf.py <family> [fontdir] [out.png]
- every glyph: outer contours clockwise (TrueType), no contour crossing another or itself
- kerning present in GPOS and in the legacy kern table
- renders a specimen from the font files, kerning applied, to compare with render.py's output
"""
import importlib.util, math, os, site, sys

sys.path.append(site.getusersitepackages())
from fontTools.pens.basePen import BasePen
from fontTools.ttLib import TTFont

HERE = os.path.dirname(os.path.abspath(__file__))
if "b3d_fontlib" not in sys.modules:               # shared loader: family from the first argument, paths
    _s = importlib.util.spec_from_file_location("b3d_fontlib", os.path.join(HERE, "fontlib.py"))
    _m = importlib.util.module_from_spec(_s); sys.modules["b3d_fontlib"] = _m; _s.loader.exec_module(_m)
FL = sys.modules["b3d_fontlib"]
R = FL.tool("render"); G = FL.family()


class FlatPen(BasePen):
    """Collects contours as polylines (quadratic segments flattened)."""

    def __init__(self, gs):
        super().__init__(gs); self.polys = []; self.cur = None

    def _moveTo(self, p):
        self.cur = [p]

    def _lineTo(self, p):
        self.cur.append(p)

    def _qCurveToOne(self, c, p):
        p0 = self.cur[-1]
        for i in range(1, 9):
            t = i / 8; u = 1 - t
            self.cur.append((u * u * p0[0] + 2 * u * t * c[0] + t * t * p[0], u * u * p0[1] + 2 * u * t * c[1] + t * t * p[1]))

    def _curveToOne(self, c1, c2, p):
        p0 = self.cur[-1]
        for i in range(1, 9):
            t = i / 8; u = 1 - t
            self.cur.append(tuple(u ** 3 * a + 3 * u * u * t * b + 3 * u * t * t * c + t ** 3 * d
                                  for a, b, c, d in zip(p0, c1, c2, p)))

    def _closePath(self):
        if len(self.cur) > 1 and self.cur[0] == self.cur[-1]:
            self.cur.pop()
        self.polys.append(self.cur); self.cur = None

    _endPath = _closePath


def area(p):
    return 0.5 * sum(p[i - 1][0] * p[i][1] - p[i][0] * p[i - 1][1] for i in range(len(p)))


def crossings(polys):
    segs = [(k, i, p[i - 1], p[i]) for k, p in enumerate(polys) for i in range(len(p))]
    bad = 0
    for x in range(len(segs)):
        k1, i1, a, b = segs[x]
        for y in range(x + 1, len(segs)):
            k2, i2, c, d = segs[y]
            if k1 == k2 and (abs(i1 - i2) <= 1 or {i1, i2} == {0, len(polys[k1]) - 1}):
                continue
            if max(a[0], b[0]) < min(c[0], d[0]) or max(c[0], d[0]) < min(a[0], b[0]) or \
                    max(a[1], b[1]) < min(c[1], d[1]) or max(c[1], d[1]) < min(a[1], b[1]):
                continue
            d1 = (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
            d2 = (b[0] - a[0]) * (d[1] - a[1]) - (b[1] - a[1]) * (d[0] - a[0])
            d3 = (d[0] - c[0]) * (a[1] - c[1]) - (d[1] - c[1]) * (a[0] - c[0])
            d4 = (d[0] - c[0]) * (b[1] - c[1]) - (d[1] - c[1]) * (b[0] - c[0])
            if d1 * d2 < -1e-9 and d3 * d4 < -1e-9:
                bad += 1
    return bad


def main(fontdir, out):
    files = [f for f in sorted(os.listdir(fontdir)) if f.endswith(".ttf")]
    sample = [G.FAMILY + "  AVATAR Today P.F.T.", "Blåbærsyltetøy ÆØÅ æøå", "0123456789 #7 (a+b)=c @ & %"]
    cap_px, lines = 40, []
    for fn in files:
        f = TTFont(os.path.join(fontdir, fn)); gs = f.getGlyphSet(); cmap = f.getBestCmap()
        wrong_dir = []; cross = []
        for g in f.getGlyphOrder():
            pen = FlatPen(gs); gs[g].draw(pen)
            if not pen.polys:
                continue
            if sum(area(p) for p in pen.polys) > 0:          # TrueType: outers clockwise -> negative total
                wrong_dir.append(g)
            if crossings(pen.polys):
                cross.append(g)
        kern = {}
        if "kern" in f:
            kern = f["kern"].kernTables[0].kernTable
        npairs = sum(ps.PairValueCount for lk in f["GPOS"].table.LookupList.Lookup for st in lk.SubTable
                     if getattr(st, "Format", 0) == 1 for ps in st.PairSet) if "GPOS" in f else 0
        print(f"{fn}: {len(f.getGlyphOrder())} glyphs, wrong direction {wrong_dir or 'none'}, "
              f"crossing contours {cross or 'none'}, kern table {len(kern)} pairs, GPOS {npairs} pairs, "
              f"ascent {f['hhea'].ascent} descent {f['hhea'].descent}")
        lines.append((fn, f, gs, cmap, kern))
    s = cap_px / 700
    lh = int(1250 * s)
    cv = R.Canvas(int(cap_px * 34), len(lines) * len(sample) * lh + 30)
    y = 10
    for fn, f, gs, cmap, kern in lines:
        hmtx = f["hmtx"]
        for text in sample:
            x, prev, polys = 20.0, None, []
            for ch in text:
                g = cmap.get(ord(ch))
                if g is None:
                    continue
                if prev:
                    x += kern.get((prev, g), 0) * s
                pen = FlatPen(gs); gs[g].draw(pen)
                base = y + 1000 * s
                polys += [[(x + px * s, base - py * s) for px, py in p] for p in pen.polys]
                x += hmtx[g][0] * s; prev = g
            if polys:
                cv.fill(polys, (20, 20, 20))
            y += lh
    cv.save(out)
    print("rendered", out)


if __name__ == "__main__":
    fd = sys.argv[1] if len(sys.argv) > 1 else FL.out("fonts", G.PS_FAMILY)
    main(fd, sys.argv[2] if len(sys.argv) > 2 else os.path.join(FL.out("specimens", FL.SLUG), "specimen-from-ttf.png"))
