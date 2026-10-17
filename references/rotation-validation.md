# Actual Cross-Topic Validation, 2026-10-18

This test made a real 11-page animated lesson about rotating a point around an arbitrary centre. The author began without the original conversation or course project, using only this skill and general runtimes. Coordinates and basic trigonometry were known; matrices were not assumed.

## What Actually Happened

The unaided first PPT was built, rendered and mathematically correct, but **failed teaching/visual review**. Its overview needed actual process construction; the essential perpendicular-leg justification was only in notes; general centre coordinates were undefined; a numerical-route shortcut reached the general discussion; moving/reference labels collided. This is evidence that the guidance and automatic checks alone did not ensure quality.

The repaired worked example uses author self-review and concrete parent/independent artifact feedback. It dynamically carries the same offset through subtraction, rotation and addition; isolates its two legs; visibly derives the rotated components; returns those components to the original centre; then uses the rule for a new angle. It is not a second unaided cold-start success. Geometric magnification was not needed: actual object continuity and a justified decomposition were.

The final PPT, exact recipe, source ledger, story map, page contracts, rendered states, first-failure specimen and independent findings are in `assets/examples/rotation-continuity`. Exact hashes and measured statuses are in [the dated receipt](rotation-e2e-results.json). Do not substitute this topic's formulas or force a two-leg decomposition into unrelated lessons.

## Reuse And Rebuild

Stage a NEW external workspace with `scripts/workflow.py stage`, as described in [implementation](implementation.md). Copy the root files from `assets/examples/rotation-continuity` into that workspace. Use its `lesson-story.mjs` and `lesson-demos.mjs` through `workflow.py build --story ... --demos ... --topic ...`; run `workflow.py review`, then its copied `topic-check.py RUN_ID`. The checker expects newly generated frames, not the archived first/last-only samples. The archived example is read-only.

The independent validation tools in `evidence/independent` include an oracle and an actual-model checker. The latter takes `WORKSPACE RUN_PATH NEW_TAG` and expects its neighboring `math-oracle.json`; it refuses to overwrite reports. It checks actual author functions and generated state metadata, not just a second copy of a displayed formula. Its assertions are rotation-specific.

A separate fresh-stage rebuild of the frozen repaired recipe checks self-contained restoration and compares actual rendered states. This is **same-recipe reproducibility**, not pixel equality as a quality requirement for another topic or independent confirmation that the first authoring attempt succeeds.

## Evidence Limits

Package and timing audits, mathematical tests, modeled animation frames and agent visual reviews have separate recorded scopes. The Computer Use connection failed before any window action after the prescribed recovery attempts. No existing PowerPoint window was operated; native playback, Left/Right/replay behavior, rehearsal duration and user teaching approval are NOT certified.

The frozen first PPT and its actual image/manifest evidence are authentic. Its neighboring story source had already changed during author self-revision, so that source was not archived as exact first-build provenance. The final recipe was frozen after authoring stopped and separately rebuilt. This distinction prevents later source intent from being mistaken for visible first-artifact evidence.
