# Windows Restoration And Authoring

## Contents
Dependencies; exact replay; another subject; engine API; native frames; verification; archive maintenance.

## Dependencies And Immutable Resources

Before building a new lesson, read `mainline-branches.md`, inspect the corrected case in `assets/continuity`, and write its story map. Run `scripts/story-map.py MAP.json --report NEW_REPORT.json` with bundled Python. This checks planning dependencies and return closure, not actual visible continuity. The included `story-map.example.json` is a small worked two-branch case, not a fixed syllabus.

`scripts/continuity-case-check.py` verifies the later deck/images, six exact same-scene frame boundaries and its 62 declared click-start zoom gates without reading the original project. `scripts/story-map-tests.py` tests positive/negative planning cases, including a simple mainline with no forced branch. Both run read-only against skill assets. Neither is a native PowerPoint playback test.

`assets/continuity/corrected-ttr5.pptx` is a self-contained later source deck: figures, native frame timing and notes are inside it, with no original course directory needed to inspect or import its objects. Use it for narrative/playback examples and the old recipe for the build API. Do not execute historical course patch scripts or copy 116 pages into a new subject. The new reference does not require SVG compression. Preserve existing accepted playback; later global restart/group/previous-action experiments caused regressions despite passing static checks. A new focus/return design needs a small native navigation test before rollout, not a transplanted magic parameter.

The archive contains the actual templates, example content, frame-generating math, template importer, TeX-to-vector math workflow, incremental formula/term motion, native click-frame backend, endpoint and modeled timeline samplers, package validators, schemas, lossless compactor and golden evidence. It does NOT bundle a full Node/Python/TeX distribution or commercial fonts.

Use the desktop `load_workspace_dependencies` tool to obtain the supplied runtime. `scripts/workflow.py` auto-detects the normal Windows installation. Environment overrides: `CODEX_DEPENDENCIES` (directory containing node and python), `TEACHING_NODE`, `TEACHING_PYTHON`, `TEX_BIN` (containing latex.exe and dvisvgm.exe). Dependencies include @oai/artifact-tool, sharp, Pillow, lxml, pypdf, TeX standalone/amsmath/upgreek/xcolor, and Times New Roman. Do not install/replace global software automatically. If missing, preserve work and report the exact prerequisite.

Bundled small validators are versioned snapshots under `assets/vendor`; the engine uses these rather than an unstable plugin-version path. External general runtimes remain prerequisites. Raw authoring sources under `assets/recipe/project` intentionally retain their historical paths as provenance; **do not execute them in place**. `stage` adapts them in a NEW workspace, explicitly removes unused T4-only imports, and supplies runtime/schema locations. All course template paths then resolve inside that workspace.

## Exact Golden Replay

Replace the path variables below with actual discovered paths. Example Windows PowerShell:

```powershell
$skill = 'C:/Users/10486/.codex/skills/animation-led-teaching-slides'
$py = 'C:/Users/10486/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'
$work = 'C:/Users/10486/.codex/tmp/teaching-replay-unique'
& $py -B "$skill/scripts/workflow.py" verify
& $py -B "$skill/scripts/workflow.py" doctor
& $py -B "$skill/scripts/workflow.py" stage $work
& $py -B "$skill/scripts/workflow.py" build $work --run-id replay
& $py -B "$skill/scripts/workflow.py" review $work --run-id replay --golden --pages 7 9 16
$run = "$work/tmp/tutorial_base/tutorial3/methods-work/replay"
& $py -B "$skill/scripts/workflow.py" compare $run --states
```

`stage` refuses existing targets; it does not clear or overwrite a folder. `build` can rerun an existing private run for iteration; use distinct run IDs when evidence must remain immutable. The output is private `candidate.pptx`, a hash-named validated copy, static/endpoint preview decks, manifest, numerical assets and checks. No live course output is overwritten and PowerPoint is never used. Build/review may take minutes. Do not stop while a required build/review process is still running.

## Another Subject Without Course Leakage

Stage once, then create a topic-specific `lesson-story.mjs` exporting `async function content(a)` and `lesson-demos.mjs` exporting `async function generateDemos({run, sharp, python})`. Modify copies, never golden assets. Supply:

```powershell
& $py -B "$skill/scripts/workflow.py" build $work --run-id lesson `
  --story "$work/lesson-story.mjs" --demos "$work/lesson-demos.mjs" --topic 'Actual topic'
& $py -B "$skill/scripts/workflow.py" review $work --run-id lesson
```

Generic mode copies actual header/layout/theme ancestry but not the course cover, route pages, assistant names or contact. Author your own cover/end; use `bare:true` on pages when not using the communications route, and draw the actual topic route if useful. Page titles have automatic links to `overview` or `lesson-map`; define those IDs or aliases. Avoid `system`, `ideal`, `course`, `course-return` as content IDs because they identify inherited openings in the original reviewer. Use `a.navigationAliases` for all default route targets, or keep the corresponding page IDs. Inspect the resulting link destinations.

Generic `cover` and `end` pages are authored pages, not inherited exclusions: their click endpoints and timeline states are reviewed too. A demos module returning `{}` is valid for a lesson using only native objects/formulas. The small `assets/tests/edge-story.mjs` and `empty-demos.mjs` are deliberately minimal ENGINE regression fixtures for these cases, not pedagogical templates to imitate.

The golden engine is a concrete helper, not a restriction to communication courses. A future supplied template may need a new template-import adapter; do not force it into the archived T3 geometry if the user requests otherwise. Preserve the tested timing/formula/validation helpers where compatible.

The independent zero-context test produced the complete six-slide moving-average lesson in `assets/examples/moving-average`. It includes the actual candidate, final renders, all review images, source/page contracts, story/demo modules and topic-specific checker. This is a SECOND worked recipe for learning the API without communication-specific content. It has agent-reviewed math/visual evidence, not user teaching approval. To rerun it, copy `lesson-story.mjs`, `lesson-demos.mjs`, `page-contract.json` and `topic-check.py` into a staged workspace's root, then build with those modules. Invoke `topic-check.py RUN_ID` from that copied location after building. Do not run it in the read-only archive, because its ROOT-relative paths intentionally refer to the staged workspace.

The 2026-10-18 cold-context **planning** test is in `assets/examples/normalization-plan`: one persistent table, nine states, no artificial branches, fixed training parameters reused for a new value. Its map passes the current planning checker. This is not a rendered deck or a native playback test; it shows that the revised narrative rules do not mandate communication notation, router pages or zooms. Dated checks and repaired lint probes are in `references/continuity-update-results.json`. The earlier full moving-average build/replay evidence remains separately dated.

The subsequent **actual** 11-page cross-topic PPT and complete repaired recipe are in `assets/examples/rotation-continuity`. It establishes an actual subtract/rotate/add process, justifies its missing rotation rule and returns to use it. Read [the test's evidence and rebuild instructions](rotation-validation.md) before citing success: the first cold artifact failed concrete teaching/label/navigation checks, repairs used independent feedback, and a fresh-stage rebuild tests the frozen repaired recipe. Earlier planning-only evidence does not substitute for this real artifact. This worked case uses geometric decomposition without requiring a physical zoom; do not confuse motion style with a motivated focus and used result.

For engine edge regression, stage and build using `assets/tests/edge-story.mjs` and `empty-demos.mjs`, run review and export a private PDF, then execute `scripts/portability-tests.py WORKSPACE --pdf ABSOLUTE.pdf`. This checks authored cover/end navigation and states, zero-demo support, the absence of the old external schema path, single relocation rather than double application, final PDF pixels and identity metadata. It is not a teaching-quality test.

## Authoring API

See the complete `t5-story.mjs` for executable examples and `t4-build.mjs` for signatures. All dimensions are logical1280x720 units.

| API | Purpose and important convention |
| --- | --- |
| page(id,title,subtitle,focus,note,{bare,purpose,parent}) | New page, unique id; bare suppresses original m/s route; source notes student-facing |
| text(name,value,x,y,w,h,size,bold,align,color) | Native Times text; explicit dimensions, no negative tracking |
| eq / statement(name,tex,x,y,w,h,size,align) | Upright bold LaTeX -> SVG+PNG fallback; statement marks equation role |
| reveal(stage,callback) | Put complete objects at an explicit cumulative click stage |
| line / shape / curve / arrow | Static diagram scaffolding; shape names must be unique within slide |
| block(name,label,x,y,w,h) | Rectangular operation module, not decorative section card |
| comparisonTable(name,values,x,y,w,h,options) | Native table for genuinely parallel information |
| demo(id,{x,y,w,h,stage,continuation}) | Register native click-start frame bundle; default stage1; continuation hides later case until its own click |
| copy / motion / relocate | Move/copy an existing meaningful object; source must be visible before dependent action |
| replace(from,name,tex,stage,options) | Local rewrite, with fixedPrefix/localTransition where suitable; do not erase needed derivations |
| flyTerm(sourceName,sourceTex,targetName,targetTex) | Semantic whole-term substitution; check actual path at intermediate frames |
| link(name,target) | Object link to page id (check signature in engine before use) |

Spacing should serve content, not fixed bands. A complex fraction needs enough height; if actualFontSize falls below20, redesign instead of shrinking. Titles/subtitles remain template-native; mathematical symbols remain TeX, not ad hoc plain text approximations. Avoid putting a long final result in an undersized borrowed placeholder.

## Numerical Demonstrations / Native Click Frames

Start by studying actual `t5-demos.mjs` plus its sample output in `assets/golden/demos`. For another topic implement its mathematical process, do not relabel an unrelated signal animation. Each renderer should have numerical invariants and finite-value checks.

Return a dictionary keyed by demo id. Example entry:

```javascript
{
  file: 'demos/my-process/first.png',
  first: 'demos/my-process/first.png',
  poster: 'demos/my-process/last.png',
  width: 1120, height: 250,
  durationMs: durations.reduce((a,b)=>a+b,0),
  description: 'Actual process, initial state and final result.',
  parameters: { /* actual parameter values */ }
}
```

That directory contains `frames.json` with ordered relative PNG filenames and equal-length `durations` in milliseconds; first.png and last.png are copies of corresponding frames. Prefer opaque white PNGs2240x500 for1120x250 logical diagrams, with Times text large enough to read. No NaN/Infinity. First/middle/last states and any critical crossing must be checked. Use cached frames only when the full renderer/shared-helper/parameters/durations hash matches.

The backend `t4-click-media.py` installs each ordered PNG as native timed appearance/set effects in the main click sequence. There is no hidden GIF player clock or loop. One click, static initial image, held final image. Do not call staged_entrance after installing frame timing, do not renumber a second time, and preserve dense stage numbering. It verifies exact durations, source pixels, native visibility and schema structure. Run `workflow.py self-test WORKSPACE` for unit tests with the correct schema environment; `workflow.py review` includes a read-only media audit. Direct helper calls require the environment supplied by the wrapper. Its full integration contract is in its docstring.

The legacy metadata field is called `gifs` even though TTR5 uses **native PNG frame layers**, not embedded GIFs. Do not 'optimize' it into auto-looping GIF playback.

## Verification And Optional Lossless Size Reduction

`review` checks the actual packaged deck, creates all endpoint renders, sampled motion renders, a full overview and demo strips under `quality-review`. It refuses broken targets, small formulas and out-of-bounds authored content. It deliberately leaves teaching/source/visual approval pending. The original golden reviewer has additional Note7-specific assertions; do not reuse those to validate another subject.

For installed frame timing, the wrapper uses `scripts/audit-installed.py` and the backend's `validate` function. The legacy backend command named `audit` attempts an in-memory INSTALL and must not be used on an already installed candidate: duplicate installation is deliberately rejected. This distinction was found by the cold-start test.

For a requested PDF, use `workflow.py pdf WORKSPACE --run-id NAME --output ABSOLUTE.pdf [--author NAME]`. It exports the already-verified `static-preview.pptx`, preserving final diagram frames and formula positions exactly once, and retains internal links. Existing output paths and export directories are refused. The handout is high-resolution page imagery, not selectable vector text. The archived legacy PDF helper is adapted during staging to prevent double relocation and hard-coded author metadata; prefer the wrapper rather than reconstructing its environment manually.

For lossless compaction, use the staged `compact-package.py` with explicit `--source`, NEW `--run`, `--expected-hash`, `--slides` and `--manifest`. Copy the correct original static-preview.pptx into that compact run before finalization. The compactor shares identical media and removes verified unreachable package parts; inspect its lossless-check.json. Never achieve size savings by lowering resolution or omitting frames/derivations. Do not run original course publication scripts; none are needed for private restoration.

## Small Edits To An Accepted Deck

A timing, wording or one-label request is not permission to redesign the deck. Reuse the existing source and touch the smallest relevant parameter/object. Keep speed, loop behavior, click gates and frame pixels independent: changing one does not authorize changing the others. For a local edit, test affected states and package integrity, and prove unrelated slide/XML/media content unchanged by hashes or semantic comparison. Reuse unchanged render evidence rather than rebuilding the entire numerical animation library. A full new lesson still needs the full page/state review; narrow edits need proportionate regression checks, not a simplified or incomplete deliverable.

## Maintaining This Archive

Keep the approved deck, raw implementation and index immutable during ordinary authoring. New learning can update guidance only when supported by actual feedback/tests. If intentionally upgrading assets, retain provenance, regenerate SHA256 inventory, run the skill structural validator, exact restoration, generic-topic forward test and independent reviews again. Test receipts document observed outcomes and limitations, not timeless guarantees. No global dependency updates or source-deck edits are implied by invoking this skill.
