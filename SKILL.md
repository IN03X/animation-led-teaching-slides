---
name: animation-led-teaching-slides
description: "Create or revise animation-led teaching PowerPoints using a visible mainline, motivated detail branches, and returns that retain results. Use for technical tutorials, process explanations, or TTR5-style teaching slides (动画课件、教学PPT、主线与支线). Includes real decks, templates, and source-aligned derivation/review tools; not marketing slides."
---

# Animation-Led Teaching Slides

The original approved 23-slide TTR5 remains the visual/template baseline, not the final teaching specification: later use exposed problems with continuity and navigation. The corrected case and **mainline -> branch -> return with results** contract below take precedence for narrative design. Both actual decks are included; no previous conversation or ELEG2310B project folder is needed. Neither a replay nor the later 116-slide count guarantees understanding or a suitable lesson length.

## Read And Look First

1. Read the current project's explicit constraints and the user's actual source material. Do not infer coverage from historical examples.
2. Read [mainline and branch design](references/mainline-branches.md), [teaching contract](references/teaching-contract.md), and [reference roles](references/golden-atlas.md). Open the actual **before focus / inside focus / after return** images listed there, as well as representative original golden pages. Some archived middle frames are documented failure specimens, not targets to copy. Reading filenames or copying the font is not template study.
3. For implementation, use [engine and Windows restoration](references/implementation.md). For review, read [acceptance gates](references/acceptance.md). Consult [lessons from failures](references/failure-cases.md) when a slide seems correct but remains confusing.

## The Teaching Contract

Preserve a visible invariant: input -> operation -> output. In the original course it is m -> s -> m, with s(t) <-> S(f) an observation of the SAME transmitted signal, not another transmission stage or merely a bandwidth chapter. For another subject use its actual objects, not communication terminology.

At both lesson and local-operation scale, the learner must see **what we are doing, why it is needed now, and what result it provides**. A highlighted chapter label does not meet this requirement. Establish the actual process dynamically; expand a known object when a necessary question arises; return to the SAME process with the new result and its conditions attached, then visibly use that result. Optional shortcuts and linear progression must both work. Do not substitute static thumbnails, repeated question slides, or zooming for this reasoning.

Each page has one simple purpose, but a sequence of individually prominent conclusions can still destroy the story. Separate lesson-level results from local supporting work. Keep full essential derivations; a long supporting proof may follow its clearly stated result on an immediately adjacent, identified derivation page, before returning to the process. Do not scatter proofs across the operation sequence or hide missing reasoning in an appendix. Reduce competing material, not necessary steps.

Begin from something already known. A new diagram, intermediate, symbol, equation, or branch must have a visible source. Maintain identities, parameters and axes across steps. Reveal only the changed increment. Animate mathematical terms or actual objects, not structural arrows or isolated equals signs. Formula changes and graph changes normally take separate clicks.

Slide entry is static. A click starts a numerical/process demonstration once, then its result holds. Supply on-screen local pointers and reference outlines so the presenter need not walk to the screen to identify what changed. Keep question statements and necessary preceding work readable.

The final result is stronger than its supporting work, not just the last of several equal-weight lines. For derivation pages, the user explicitly approved a clearly separated bottom conclusion: retain the necessary preceding steps, but give the final expression stronger size/weight and breathing room so it can be found at a glance. Put its conditions beside it; do not crowd it against the last intermediate line. Check both an active calculation state and the completed page to ensure that the current step and then the bottom result receive attention. This approval is for local visual hierarchy, not permission to treat every page's conclusion as an equally important lesson-level takeaway. Avoid scattered small-print explanations, undefined jargon, decorative motion, and extra parallel routes that dilute the main one.

## Workflow

1. Build the source/notation ledger and story map FIRST: main task, known objects, motivated branches, results, returns, and later uses. See `assets/continuity/story-map.example.json` and run `scripts/story-map.py` on a new map; this checks information flow, not teaching quality. Then write page contracts, including mainline/branch location, known input, operation, purpose, result, conditions, source, and clicks. Use `assets/page-contract.example.json` as an example, not a fixed slide layout. Budget narration/clicks, not page count alone.
2. Inspect and reuse the **actual** accepted template objects and layout ancestry. The default golden style is white, black/gray, Times New Roman, upright bold TeX. A new explicit user template takes precedence. Do not copy course names, instructor names, addresses, or subject-specific navigation into an unrelated deck.
3. Stage an isolated project using `scripts/workflow.py stage`. Keep the archive immutable. Adapt content and numerical demos in that staged project, using the engine API and complete examples. For a new topic use `--story` and `--demos`: these enable generic-template mode and avoid inherited course slides/identity. Do not rebuild the animation backend from scratch.
4. Implement the required deck completely. Derivation steps can accumulate, then deliberately contract to the established result. A parameter change must be visible before interpreting its effect. Derive before naming unfamiliar objects; do not use names as explanations.
5. Run `workflow.py build`, `workflow.py review`, numerical checks and the acceptance gates. Inspect complete overview -> focus -> return sequences, not only isolated endpoints. Verify the return retains the result and the next step uses it; inspect labels, axes, and graph/formula correspondence. Compare style to the original golden and narrative to the corrected case. Use an independent math/visual pass when warranted, with concrete slide/state evidence rather than vague approval.
6. Fix observed defects and rerender. Publish only after the requested scope, cognitive continuity, math, layout, navigation and package gates hold. Preserve an existing open deck; never close PowerPoint or automate it without explicit authorization. New private test/build files do not authorize overwriting the user's original.

## Restoration And Evidence

On Windows, discover the bundled Node/Python runtime using `load_workspace_dependencies`, or let `workflow.py doctor` detect it. TeX is an explicit prerequisite; no automatic environment changes. The scripts find installed paths or accept overrides. They do not depend on a fixed username, plugin version, or the original course directory. See implementation for commands.

`assets/recipe/project` and `assets/golden` preserve the original implementation/template evidence. `assets/continuity/corrected-ttr5.pptx` and its annotated reference states preserve later corrections; inspect them as worked cases, not a universal deck to copy. `archive-index.json` binds both. `workflow.py verify` checks integrity; `workflow.py compare` checks only the old unchanged-topic replay. **Do not** use pixel equality to judge a different lesson. The independent cold-start tests have dated scopes; a new guidance revision does not retroactively extend their claims.

The newer [actual rotation-lesson validation](references/rotation-validation.md) includes a failed cold-start PPT, concrete independent findings, a repaired full animated recipe and a separate restoration rebuild. Use this contrast to calibrate review of an actual branch/return, not just a well-filled outline. Its iterative result is not a claim of first-attempt or universal teaching success; native playback has a separately recorded limitation.

Golden-specific regression tests are not generic teaching tests. For a different topic, adapt mathematical assertions and use its own contracts. Structural/schema tests do not certify student understanding, PowerPoint playback, or classroom duration. Distinguish modeled timeline checks, native playback, rehearsal and user approval in the final report.

## Scope And Delivery

Deliver the editable animated PPTX and a concise account of what was actually checked. Export PDF only when requested; preserve final visible states and links. Lossless cleanup may share identical media and remove provably unused parts, never downsample diagrams or remove necessary steps just to meet a size target. Do not create multiple public versions unless requested.

Do not claim that loading this skill guarantees teaching quality automatically. The enforceable target is the archived accepted example plus source-specific, visual and cognitive verification. A zero-context restoration test is recorded in `references/test-results.json` when available; read its actual scope and limitations before citing it.
