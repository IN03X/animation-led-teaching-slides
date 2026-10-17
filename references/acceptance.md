# Acceptance Gates

## Deliverable Gate

Check source scope, requested output, speaker names/contact, no accidental duplicate public versions, student-facing notes, and required navigation. An old template link resolving to an existing but wrong page is still a failure. Test the meaning of the links, not only relationships or link count.

Never operate/close PowerPoint or use COM for export as an implicit convenience. Stage first, detect lock markers, compare the original hash again before any authorized overwrite, preserve a private backup and stop on conflicting edits. PDF uses the final visible state, not all hidden layers stacked. No publication script is invoked by the skill's staging/build tools.

## Teaching Gate: Inspect Every Page

Inspect the complete overview -> focus -> return sequence BEFORE scoring isolated pages. For each branch cite actual state images: the established originating object; the visible reason for the detour; the local result/conditions; the same process on return; retained earlier conclusions; the next operation that uses the new result. Any missing link is a blocking narrative finding. `story-map.py` catches planning inconsistencies only, not whether the visible slides actually meet their descriptions.

A static route box beside an unrelated local animation does not by itself pass the branch boundary. Inspect the actual operand's before/focus/after representation and change, not just shared titles or a stated scene ID. When both old and moving objects coincide initially, inspect their labels at frame0 for double-printing. A mathematical projection needs a visible angle/component correspondence rather than only an equation in a different page band.

For each page record evidence, not a generic score:

1. Can a novice locate the main route AND the concrete task inside it without reading notes? Chapter labels alone do not pass.
2. What is the only new idea? Can they identify the result in a quick glance?
3. Is each new symbol/plot/module generated from something already seen? Is the purpose of a side branch explicit?
4. Do notation, axes, examples and parameters continue from the previous page? Is a reset visible?
5. Are derivations sufficient to copy and reproduce? Are definitions, substitutions, factors and limits retained?
6. Does the plot actually depict that equation and that operation? Are sums signed correctly?
7. Can the presenter explain the change without walking to point? Does the local pointer target the correct object?
8. Is supporting work visibly subordinate without becoming unreadable? Are assumptions beside conclusions?
9. Does the next page use the established result, rather than suddenly begin a different analysis? After a branch, does the original process visibly gain that result rather than merely reappear unchanged?

Use blocking findings with page/state, observable defect, likely novice interpretation and concrete repair. Do not call a deck 'red-team passed' simply because tests ran or an agent said 'looks good'. Independent reviewers should inspect images and source facts, then verify the changed evidence after repairs.

## Render Gate

Inspect all final pages AND all click endpoints. Complex mathematical flights need intermediate samples. Every demonstration needs first/middle/final visual inspection and numerical verification. Inspect inherited opening animations separately: the generic timeline model skips inherited slides and cannot certify their native transition behavior.

- Initial state: only known context is visible; no stacked future curves or hidden continuation posters.
- Each click: one intelligible operation, complete equation, correct source and destination. No structural arrows flying, arbitrary disappearance, source not yet visible, equals sign preceding content or double animation competing with the graph.
- Middle: no motion through retained formulas, no transient overlaps/malformed equality, continuous path without unnecessary detours.
- End: full intended result holds, old necessary work remains; original plot axes have not jumped.
- Return: inspect the last detail frame, the moving return, and the returned overview together. Same object/example/scene, no unexplained reconstruction, result retained at its origin, no premature answer or lost prior conclusion.
- Graph: nonblank, matching reference and changed parameter, labeled units/cutoffs, no pointer/text collisions, correct signed components and combined curve.

For overview/focus playback, separately check static entry -> click -> focus -> Previous -> Next/replay and the corresponding return. A hyperlink to the overview does not demonstrate ordinary Left/Right navigation. Do not certify this from XSD, frame snapshots, a backend parameter or the old 23-page regression. Preserve a user's verified timing policy; if native testing is unavailable, record that limitation and seek a small-sample test before propagating an experimental playback change.

`workflow.py review` generates generic structural checks, all endpoint PNGs, a final overview, demo strips and sampled timeline states. It reports review work left to humans/agents rather than inventing approval. Increase time sampling around observed collisions;0/350/700/1050ms is a starting set, not exhaustive motion certification.

`workflow.py compare` is ONLY for unchanged-topic golden replay. Pixel differences must be inspected. Runtime/font changes may produce differences even if content is equivalent; do not automatically bless or automatically reject them without looking.

## Mathematics Gate

Maintain a source ledger and explicit numerical checks for the actual topic. For this golden example run the preserved `t5-review.mjs` after timeline generation. Its23-page/topic assertions are a regression suite, NOT reusable correctness proof for another lesson.

Check units, transform conventions, gains, support assumptions, approximations, finite vs infinite sums and plotted normalizations. The model and the diagram should use the same parameters; adjust only one parameter at a time when teaching its effect. Use sampled error bounds/invariants rather than only searching formulas for words.

## Package Gate

Run the schema, relationships, unique ids, master/layout/notes registration, font, media timing and geometry checks. The notes-master regression matters: individually valid slides can still prompt PowerPoint repair if there are unregistered or incompatible package-level master relationships. Re-import and render the actual packaged result, not only the authoring donor.

The native frame backend has unit tests and a read-only audit. Lossless compaction verifies retained XML/timing/media byte identity and relationships. Do not downsample, turn formulas into low-resolution bitmaps, silently convert to static-only slides, or remove essential pages to reduce file size.

## Claims And Completion

Report separate statuses: source/mathematical review; layout and endpoint renders; modeled timeline; package validation; native PowerPoint play; timed rehearsal; user teaching approval. 'Not tested' is a valid honest status. Classroom minutes cannot be measured by ZIP export. Do not claim native play from XML/XSD/render checks. All required work stays in scope until complete; a skill that only stores a manifesto without concrete assets and tested tools is not a completed archival capability.
