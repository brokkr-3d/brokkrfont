# Brokkr Sans 3D – design notes

## Goal
A monoline font called **Brokkr Sans 3D** (a Brokkr Serif 3D will follow), made for 3D printing: text printed in a second colour in the **first layer**.
Stroke width is a line width in XY, so it should come out as whole 0.4 mm nozzle lines. Output: TTF files.

## Status (2026-11-27)
- **101 glyphs drawn** in three weights: A–Z, a–z, Æ Ø Å æ ø å, 0–9 and all printable ASCII punctuation/symbols
  (`. , : ; ! ? ' " - ( ) [ ] { } / \ | _ + = < > * % & @ # $ ~ ^ `` ` and space).
- **Fonts built** (v0.9): `fonts/BrokkrSans3D/BrokkrSans3D-Light.ttf`, `-Regular.ttf`, `-Bold.ttf`, checked by `check_ttf.py`.
- Every glyph is **sliced in PrusaSlicer 2.9.6** (Arachne, 0.4 mm first-layer width, 8 mm caps), both as text
  and as the background plate around it, and scored automatically (see "Slicer test 2").
- **Kerned** (2026-11-27): about 950–1,400 pairs per weight in `kerning.json`, checked visually and in the slicer.
- Not done yet: Bambu Studio / Orca check, the cheat sheet, a real test print.

## Files
This family lives in `families/sans/`; the tools in `tools/` are shared with every family (see the repo README).
| File | What |
|---|---|
| `families/sans/glyphs.py` | Family identity (names, version), metrics, spacing rules, build step, kerning loader |
| `families/sans/glyphs_upper.py`, `_lower`, `_figures`, `_nordic` | The drawings: one short function per glyph |
| `families/sans/kerning.json` | Kerning pairs per weight, made by `tools/kerning.py sans` |
| `tools/b3d_geom.py` | Geometry engine: union of sharp primitives → true-arc fillets; `Path` for explicit arcs (the 8) |
| `tools/render.py sans [kern]` | Pure-Python PNG specimens → `specimens/sans/` |
| `tools/measure_stroke.py sans` | Thickest spot per glyph (junction blobs) |
| `tools/slice_test.py sans <outdir>` | STL plates → PrusaSlicer CLI → scored toolpath maps; `words:AV\|To` slices kerned words |
| `tools/kerning.py sans` | Autokerning with a printing floor |
| `tools/build_ttf.py sans` → `fonts/BrokkrSans3D/` | Builds the three TTFs (fontTools) |
| `tools/check_ttf.py sans` | Reads the TTFs back: direction, crossings, kerning; renders `specimens/sans/specimen-from-ttf.png` |
| `tools/make_testprint.py sans [--verify]` → `testprint/sans/` | Two-colour test plate (3MF + STLs), optional slicer check |
Everything runs with `python -I` (standard library only, plus fontTools for the TTF steps). Analysis output goes
to `out/` (not committed); its G-code is analysis-only (no homing/heating) and must never be sent to a printer.

## Metrics (font units, UPM 1000)
- Baseline 0, cap height 700, x-height 550, ascender 760, descender −220. **Base size: 8 mm caps.**
- Stroke w: Light 35 / Regular 70 / Bold 105 = **0.4 / 0.8 / 1.2 mm** at 8 mm caps (1 / 2 / 3 lines).
- Stroke ends: radius rr = w/4. Inside corners (junctions): fillet ri = w/4.
- Round capitals: outer radius 180; lowercase bowls 160; counters concentric (outer − w) so the stroke stays w.
- Dots: Light 70, Regular 105, Bold 140 units (2 / 3 / 4 lines); i/j dots capped so the gap to the stem is ≥ w.
- Word space 250. Highest point: the Å ring (994 in Bold); lowest: descenders (−220).

## Design rules (enforced in the code)
1. Every stroke is exactly w. Curves are concentric; a counter corner is only rounded (outer − w) where its outside
   is a concentric curve. Against a stem it gets the small fillet ri.
2. Gaps between separate strokes ≥ w (x-height/descender were raised for Bold's a and g; @ and % widen in Bold).
3. Diagonals end in flat cuts (no points): feet and apexes are about one stroke wide.
4. Two neighbouring glyphs never come closer than w + 30 units (side bearing floor 0.5 w + 15).
5. Any corner radius that does not fit its edges is reported as "clamped" by `glyphs.py` — keep that list empty.

## Glyph decisions
- Squared, technical style (Eurostile/DIN family feel). Two-storey a, single-storey g with squared hook; y uses the same hook.
- **l has a tail**, I is a plain stem, 1 has a flag: `lIl1|` are all distinct. 0 is narrower than O.
- 8 is two stacked rounded boxes with a filleted notch at the waist (built with explicit arcs).
- B and 3 (redrawn 2026-11-27): rounded bowls like P and R, upper bowl narrower, and where the two waist corners
  meet (radius 110) the outline has the 8's filleted notch, built with explicit arcs (`K.waist()`). The 3 is the
  B's right side with open ends. The earlier stepped waist (square upper corner on a small ledge) looked foreign.
- Capitals are 4 % narrower than first drawn (`UC_WIDTH = 0.96` in `glyphs.py`, 2026-11-27): each capital's width
  and width-tied positions go through `K.uc()`; strokes, radii, heights and spacing are unchanged.
- Q: 45° tail through the bottom-right corner. R: diagonal leg; junction moves out in Bold to keep the gap ≥ w.
- &: classic form — closed upper loop, lower bowl ending in a tail, 45° leg crossing it. Tight but legible in Bold.
- **Å** ring sits on the A's apex (no thin gap to fuse, saves height); **å** ring floats one stroke above the a.
  Ring hole ≥ w, so the ring grows in Bold (325 units). Seated ring has smaller bottom corners where the legs join.
- **Ø / ø**: O with a slash between the bowl's corners, kept inside the outline (no spikes); clearly different from
  O and 0. In Light the slash is joined to the already-rounded ring (thin stroke + big radius), see `_slashed`.
- **Æ**: diagonal leg into a vertical E stem; A crossbar low and E arm higher, so two T-joins instead of a crossing.
  **æ**: a and e share the middle stem; the a's top bar runs on into the e.
- Proportional spacing with classes (straight / round / open / diagonal). j's stem is spaced like a stem, so its
  hook tucks under the previous letter (negative left side bearing); kerning pushes it back where a descender is.

## Kerning (`tools/kerning.py`)
- **Method, "slide room":** spacing already makes every glyph right next to a straight stem, so kerning only fixes
  how two shapes interlock. Per pair, the gap is measured every 5 units of height where both glyphs have ink;
  slide room = smallest row gap minus the gap between the two glyphs' edges (edges judged at or above the
  baseline). Kern = −½ × slide room. HT, AA, oo and nn get 0; AV −115, AT −105, LT −105, To −105, P. −100 (Regular).
- **Printing floor:** after kerning, the two inks stay ≥ w + 30 units apart in 2D, the same floor as the spacing,
  so the background colour always prints between letters. The floor also adds positive kerns where descenders would
  clash (gj, yj, qj, jj: +55…+115).
- **Guards:** no sliding into a space closed above and below (a hyphen into C or S); caps of −130 for letter pairs
  and −100 with punctuation; **digits are not kerned**, so number columns on labels line up.
- Pairs: Light 1,374 · Regular 1,179 · Bold 965 (incl. Æ Ø Å æ ø å). Manual overrides go in `KERN_MANUAL` in `families/sans/glyphs.py`. Re-run it after
  any change to shapes or spacing.
- Slicer check (kerned words AVATAR, Today, P.F.T., WAVY, Fjord, enjoy, gjyjqj, LTA, 'A'): background between
  letters prints everywhere; uncovered text Light 0.04 / Regular 0 / Bold 1.0 mm² (Bold's known junction specks).

## Slicer test 2 (PrusaSlicer 2.9.6, all 95 glyphs × 3 weights)
Uncovered text area, summed over all glyphs (mm²):

| | Light | Regular | Bold |
|---|---|---|---|
| Arachne defaults | 0.3 | 5.3 | 4.5 |
| **Recommended settings** (below) | **0.3** | **0.3** | 3.6 |

- **Light dots were dropped** by the slicer at 0.63 mm (55 units). Dots now start at 0.8 mm; nothing is dropped.
- **Crossings** (+ # t f 4 *) leave a ~0.25 mm² diamond at the centre with Arachne defaults: the centre is more than
  one line from every edge and Arachne's default minimum bead width (85 %) won't add the thin middle line.
- **Recommended text settings** (PrusaSlicer → Print Settings → Layers and perimeters → Advanced):
  Minimum perimeter width **50 %** (`min_bead_width`), Perimeter transitioning threshold angle **40°**,
  Perimeter transition length **40 %**. Perimeter count and the Classic generator do not help.
- **Bold** still leaves small specks at crossings and sharp diagonal joins (# t f 4 + z K w &) even with those settings:
  its three-line strokes lose the middle line in junctions. Small "bead traps" (ink-trap notches) at crossings were
  considered and **declined (2026-11-27): Bold stays as drawn**, keeping the rounded inside corners.
- Background voids near glyphs are small and only recessed (layer 2 is the same colour), so they don't show.
- Remaining junction "thickest spots" are 1.2–1.9 w (inherent to joins); the asterisk centre is 2.4 w.
- Re-run 2026-11-27 after the new B and 3 and the 4 % narrower capitals (all 101 glyphs, recommended settings):
  uncovered text Light 0.32 · Regular 0.27 · Bold 3.9 mm² (before: 0.29 · 0.28 · 4.19), nothing dropped; B and 3
  have no uncovered text in any weight. Per-glyph changes are within ±0.06 mm² (slicer noise level).

## Font files (`tools/build_ttf.py`, v0.9)
- 102 glyphs (101 characters + .notdef), AGL glyph names, outers clockwise, no overlapping or crossing contours.
- Curves: cubic → quadratic with cu2qu (max error 0.5 unit = 0.006 mm at 8 mm caps), coordinates rounded to units.
- Naming: Regular + Bold = family "Brokkr Sans 3D" (style-linked); Light = family "Brokkr Sans 3D Light" so Windows menus
  list it; all three share the typographic family "Brokkr Sans 3D" (Light / Regular / Bold).
- Vertical metrics shared by all weights: ascent 1004, descent −230 (covers the Å ring); typo 780 / −220.
- Kerning in GPOS (`kern` feature) and a legacy `kern` table with the same pairs (Light 1,374 · Regular 1,179 ·
  Bold 965 — re-run `kerning.py` then `build_ttf.py` after changes).
- Ownership: Copyright 2026 Brokkr 3D AS, SIL Open Font License 1.1 with Reserved Font Name "Brokkr" (OFL.txt); written into each font (name IDs 0, 8, 11, 13, 14). Tools are MPL-2.0.
- In a slicer: install the TTF (right-click → Install) or point the text tool at the file. Font size → cap height:
  caps are 0.7 × the font size (font size 11.43 mm ≈ 8 mm caps) — to be confirmed per tool in the cheat sheet.

## Test print (`tools/make_testprint.py` → `testprint/sans/`)
- 144 × 114 × 2 mm plate, text 0.6 mm deep (3 layers) on the bed side: all weights at 8 mm, Æ Ø Å æ ø å, kerning,
  crossings, digits, look-alikes, then Regular 6 / Bold 5 / Regular 4 / Bold 3 mm. `--text=` / `--plate=` change
  the depth and thickness. Files: PrusaSlicer 3MF (extruders assigned), base + text STLs, preview of the face, and
  `testprint/sans/README.md` with settings and what to look at.
- The face is seen from below, so the text is mirrored left-right in the model (`bed_side()`) and reads the right
  way round on the print. The first version (1.2 mm plate, text 0.2 mm deep) was not mirrored and came out
  backwards (2026-11-27). The text is triangulated as it reads and then mirrored as a mesh: triangulating the
  mirrored outlines left gaps in the faces of every B (two counters with the same right edge trip the hole
  bridging). Every build checks that both meshes are closed.
- Verified by slicing the 3MF in PrusaSlicer 2.9.6 as a two-extruder print (`tools/make_testprint.py sans --verify`,
  every text layer plus the one above). With the recommended settings, including 0.4 mm perimeters, every text
  layer has 0.0 mm of extruder-1 line inside the text and 0.0 mm of extruder-2 line outside it, all 236 text parts
  get plastic in all three layers, and there is no text colour above 0.6 mm. With 0.45 mm perimeters (the usual
  profile width), the two 0.45 mm dots of the Bold 3 mm row get none in layers 2–3. **With Arachne defaults, five
  small dots (0.45–0.6 mm, 3–4 mm rows) get none on the face and six in the layers behind it.** Four filament
  changes (layers 1–4).
- Result of the real print: _pending_.

## Open questions
1. Slicer first-layer width: Bambu Studio defaults to 0.5 mm; Light/Regular were identical at 0.4 and 0.5 in test 1.

## Next steps
1. Cheat sheet: font size setting in Bambu Studio / PrusaSlicer / Fusion / OpenSCAD → cap height in mm (each tool
   defines "size" differently), plus the slicer settings above.
2. Print `testprint/sans/` (ready) and note the results above; later, also try the TTFs in a slicer's own text tool.
