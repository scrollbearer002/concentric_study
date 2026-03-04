# Cousin Visual Reasoning Showcase

Environment basis: this showcase is built from the actual saved puzzle artifacts
generated during the live FreeWWW IQ-test run in Safari on this machine. It is
not a fabricated example and it does not depend on a new external site. The
source artifacts are under `operator/cre/iq_test_freewww_q*/`.

## What this demonstrates

This repo is already strong at browser control, screenshot capture, and
structured evidence logging. The point of this showcase is narrower:

- take real saved visual puzzle artifacts from a live run
- classify the puzzle family
- explain the rule cleanly
- show what correct visual reasoning looks like

That is the right showpiece for the current branch because the live IQ result
showed the system is strongest in logic/math/verbal reasoning and relatively
weaker in pattern/spatial reasoning.

## Example 1: Rotation

Artifact:
- `operator/cre/iq_test_freewww_q26/montage.png`

Puzzle family:
- `rotation_reflection`

Observed rule:
- the arrow is rotated `90 degrees clockwise`

Correct reasoning:
1. Start from the up arrow.
2. Rotate it one quarter turn clockwise.
3. The result is a right-pointing arrow.

Correct answer:
- `B`

Why this is a good baseline:
- it is a clean single-rule visual transform
- the system should classify this family reliably before looking at options

## Example 2: Mirror transform

Artifact:
- `operator/cre/iq_test_freewww_q27/montage.png`

Puzzle family:
- `rotation_reflection`

Observed rule:
- reflect the triangle across the vertical mirror line

Correct reasoning:
1. The source triangle points right.
2. Mirroring across a vertical line flips left-right orientation.
3. The image should point left, with the same vertical placement.

Correct answer:
- `A`

Why this matters:
- this is not just “pick the one that looks opposite”
- it is a specific transform family with a predictable output

## Example 3: Matrix progression

Artifact:
- `operator/cre/iq_test_freewww_q29/montage.png`

Puzzle family:
- `matrix_progression`

Observed rule:
- the number of diagonal stripes increases as you move through the matrix

Working hypothesis:
1. Top-left has the fewest diagonal marks.
2. Top-right increases the stripe count.
3. Bottom-left increases again.
4. The missing bottom-right cell should continue that count progression.

Most defensible answer:
- `D`

Why this is a good weak-spot example:
- it requires relation tracking across the grid
- the answer should be chosen by preserving the progression rule, not by
  nearest visual similarity

## Example 4: Shape-to-solid mapping

Artifact:
- `operator/cre/iq_test_freewww_q30/montage.png`

Puzzle family:
- `net_folding` / `shape_to_solid_mapping`

Observed rule:
- a central square with four surrounding triangles folds into a square pyramid

Correct reasoning:
1. The center square is the base.
2. Each surrounding triangle becomes one triangular side face.
3. The only solid matching that net is a square pyramid.

Correct answer:
- `B`

Why this matters:
- this is a true spatial transform
- it rewards explicit part-to-solid mapping instead of option guessing

## What this says about the project

The strong path already exists:

- capture visual artifact
- preserve evidence
- classify problem family
- derive rule
- choose by contradiction or transform consistency

The next bounded enhancement is therefore not a full rewrite. It is:

- add a lightweight visual reasoning support layer
- make family classification explicit
- log rule hypotheses and option eliminations
- improve confidence/revisit behavior on weak visual families

## Files to inspect

- `operator/cre/iq_test_freewww_q26/montage.png`
- `operator/cre/iq_test_freewww_q27/montage.png`
- `operator/cre/iq_test_freewww_q29/montage.png`
- `operator/cre/iq_test_freewww_q30/montage.png`
- `operator/cre/VISUAL_REASONING_ENHANCEMENT_PHD.md`
