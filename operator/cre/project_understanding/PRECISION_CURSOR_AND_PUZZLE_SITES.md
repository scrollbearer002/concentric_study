# Precision Cursor + Aim-Focused & Puzzle Test Sites

Reference list of websites used for motor-function and intelligence+cursor validation. Human Benchmark suite (sequence, aim, chimp, typing, verbal, number, visual, reaction) lives in `human_benchmark_suite.py`; these are the broader set of sites for precision cursor and puzzle testing.

---

## Precision Cursor + Aim-Focused Tests (Motor Functions)

Emphasize pixel-accurate clicking, tracking, and steadiness—for spotting jitter, overshoot, or drift.

| Site | URL | Notes |
|------|-----|--------|
| **Human Benchmark – Aim Trainer** | https://humanbenchmark.com/tests/aim | Click 30 targets as fast and accurately as possible. Scores average time per target. Run multiple sessions for repeatability. Small/moving targets → cursor precision and reaction. *(In suite.)* |
| **Mouse Accuracy Training Game** | https://mouseaccuracy.com | Customizable: target size, speed, duration, difficulty. Tracks hits, misses, score. Start medium then shrink for fine control. Good for endurance (e.g. 60+ s loops). |
| **XBitLabs Mouse Accuracy Test** | https://xbitlabs.com/mouse-accuracy-test | Path following (trace curves), shape tracing, precision clicking, steady-hand. % accuracy (e.g. Expert 85%+). Surfaces mechanical issues in dragging or sustained hold. |
| **Arealme Mouse Tracking Accuracy Test** | https://arealme.com/mouse-test/en | Guide a ball along curves without leaving the path; speed + accuracy. Tight turns highlight wobble or delay. |

---

## Puzzle Sites (Intelligence + Precise Cursor)

Logic puzzles requiring accurate clicking, dragging, grid/cell selection—testing decision-making and motor reliability.

| Site | URL | Notes |
|------|-----|--------|
| **The Bézier Game** | https://bezier.method.ac | Master pen tool: click/drag control points to match curves. Very precise; exact handle placement. Levels get harder → curve understanding + fine cursor control. |
| **SolveMe Puzzles** | https://solveme.edc.org | Math/logic (MysteryGrid, Who Am I?, mobiles). Drag-drop and precise grid/element clicks. Visual and logic-based; interpret clues and execute accurate selections. |
| **Archimedes Lab Online Puzzles** | https://archimedes-lab.org/pix_games.html | Pic-a-Pix, Link-a-Pix, Slitherlink, Hashi, Fill-a-Pix. Click cells to fill grids or draw paths → planning + pixel accuracy. |
| **3D Aim Trainer** | https://3daimtrainer.com | Tracking, flick shots, precision clicks; stats. More “intelligent” than basic aim: patterns and scenarios needing anticipation and strategy. |

---

## Summary

- **Aim / motor**: Human Benchmark Aim, mouseaccuracy.com, xbitlabs.com, arealme.com.
- **Puzzle / intelligence + cursor**: bezier.method.ac, solveme.edc.org, archimedes-lab.org, 3daimtrainer.com.

Human Benchmark suite URLs are in `tools/human_benchmark_suite.py` → `HUMAN_BENCHMARK_URLS`. This doc is the master list for the broader precision-cursor and puzzle site set.
