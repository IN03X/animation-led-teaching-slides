# Animation-Led Teaching Slides

A self-contained Codex skill for technical teaching PowerPoints: establish the
actual process, focus on a necessary detail, then return to the same process
with a result that is visibly used.

Start with [SKILL.md](SKILL.md). The repository contains the full templates,
editable authoring sources, mathematical demonstrations, animation backend,
worked lessons, visual evidence, and validation tools. No course project folder
or prior conversation is needed to inspect these resources.

## Install on Windows

Clone into a **new, unused** skill directory. Do not overwrite an installed copy:

```powershell
gh repo clone IN03X/animation-led-teaching-slides "$HOME\.codex\skills\animation-led-teaching-slides"
```

Then invoke `$animation-led-teaching-slides` in Codex. For dependencies and
isolated stage/build/review commands, read
[Windows restoration](references/implementation.md). Builds belong outside this
archive; do not run historical course scripts directly in its assets.

## Verification and Scope

- [Latest actual cross-topic test](references/rotation-validation.md): a real
  11-page animated rotation lesson, concrete first-draft failures, iterative
  repairs, independent reviews, and a fresh rebuild matching 185 reviewed images.
- [Detailed receipt](references/rotation-e2e-results.json): separate mathematical,
  visual, package, reproducibility, and native-playback statuses.
- [Archive inventory](archive-index.json): SHA256 identities for all 1,552 skill
  files, approximately 264 MB. Preserve the whole archive, not only SKILL.md.

Native PowerPoint playback and navigation were **not** certified in the latest
test because desktop control was unavailable. Rendered-state checks are not a
substitute for native playback, student understanding, or a timed rehearsal.
The skill does not guarantee first-attempt quality for every subject.

This private repository contains original course examples and provenance.
No blanket redistribution license is asserted for third-party materials.
