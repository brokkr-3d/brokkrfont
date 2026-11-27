# Brokkr Sans 3D – test print

A 146 × 114 × 1.2 mm plate with the text in the **first layer** in a second colour (print face down: the text is
the side that touches the bed). Made by `tools/make_testprint.py sans`; preview: `testplate-preview.png`.

## Files
| File | Use |
|---|---|
| `brokkr_sans_3d_test.3mf` | PrusaSlicer project: one object, **base = extruder 1, text = extruder 2** already assigned |
| `brokkr_sans_3d_test_base.stl` + `brokkr_sans_3d_test_text.stl` | Same parts for any slicer (they share one coordinate system) |

## What is on the plate (top to bottom)
1. Regular 8 mm · 2. Light 8 mm + Æ Ø Å æ ø å · 3. Bold 8 mm + kerning (AVATAR, P.F.T.)
4. Digits and crossings (`# +`) · 5. Look-alikes `lIl1| O0 S5 B8` and `& @ %`
6. Regular 6 mm with dots and punctuation (`i.j:;!?`) and crossings (`f t 4`)
7. Bold 5 mm · 8. Regular 4 mm (0.4 mm strokes = 1 line) · 9. Bold 3 mm (0.45 mm strokes) — the size limits

## Slicer settings for the text
- Layer height 0.2 mm, **first layer 0.2 mm**, **first-layer line width 0.4 mm**, wall generator **Arachne**.
- **Minimum perimeter/wall width 50 %** (default 85 %), **transitioning threshold angle 40°** (default 10°),
  **transition length 40 %** (default 100 %). In Bambu Studio / Orca also set **Initial layer minimum wall width
  50 %** if your version has it.
- Why: with defaults, crossings (`# + t f 4`) keep a ~0.5 mm hole in the text colour, and in this plate **six
  small dots (0.45–0.6 mm, rows 8–9) get no text plastic at all**. With the settings above every one of the 236
  text parts prints (checked by slicing this exact project in PrusaSlicer 2.9.6 as a two-extruder print:
  extruder 1 puts 0.0 mm of line inside the text, extruder 2 0.0 mm outside it).

## How to load it
- **PrusaSlicer (MMU3, XL, multi-tool):** open `brokkr_sans_3d_test.3mf`, pick your printer and filaments, apply the
  settings above. The parts already have their extruders.
- **Bambu Studio / OrcaSlicer (AMS):** import **both STLs in one go** and answer **Yes** to "load as a single
  object with multiple parts" (keeps them aligned). Then set the text part to filament 2, the base to filament 1.
  Keep the prime tower on.
- A smooth PEI or glass plate gives the cleanest face; a textured plate shows its texture on the face.

## What to look at
- Do the **dots** survive at 6, 4 and 3 mm (`i j : ; ! ?` and the periods)?
- **Crossings** in `# + t f 4`: any speck of base colour in the middle (expected only in Bold, small)?
- **Kerned pairs** (AV, VA, TA, P.F.T.): is there still base colour between the letters?
- **Light** 8 mm: are the strokes continuous single lines? **Bold**: are the small counters (e, a, &, @) open?
- Æ Ø Å æ ø å: rings and slash clean, ring holes open?
- Colour bleed at edges, and the smallest size you would still call readable, per weight.
