# Teaching Contract

## Contents
Main picture; local branches and returns; page contracts; derivations; visual attention; pacing; exercises; source fidelity. Read `mainline-branches.md` for the corrected worked sequences and planning checks.

## Main Picture Before Details

Start and end with the same small map. It tells students what they can construct, inspect, and recover. Intermediate chapters are operations on that map, not an inventory of technical names. A map can act as a clickable router; nested routers should show only the next meaningful choice.

In TTR5 the processing route is known message -> pulse construction -> transmitted waveform -> read sample heights -> reconstruction -> recovered message. The s(t) <-> S(f) view is an analysis branch of the SAME transmitted waveform, not a processing stage inserted between transmitter and receiver. Bandwidth is one result of this analysis, not its defining purpose. Sampling mathematics explains needed factors and recovery conditions. TDM reuses already established samples and reconstruction.

Establish the process by showing the operations build it, before relying on the finished overview. A focus begins at an identifiable existing object; the reader sees why a local result is missing. After the detail, return to that same process, attach the result with its conditions, retain earlier conclusions and visibly use it. Local direction is required inside chapters too: a route badge by itself is insufficient. A static collage of completed plots or repeated zooms without this information flow does not meet the contract.

For another topic preserve the idea, not the symbols: e.g. data -> transformation -> prediction -> evaluation. A title like 'A unified exploration of the frequency-domain landscape' is not useful. Use a familiar literal topic and an operation-level subtitle; use a question only when it clarifies the current obstacle. Do not turn every page into a new question that fragments the story.

## Page Contract

Before drawing, write one sentence saying what a student will understand after this page. Then specify:

| Field | Required decision |
| --- | --- |
| Already known | Exact prior formula/object/frame reused |
| Narrative location | Main operation or branch; originating overview and selected object |
| Current task | Operation on that object, or a justified property being inspected |
| Why now | Missing fact needed to complete that specific operation |
| New increment | Only what changes now, including introduced symbols |
| Dominant result | The single result that should survive a quick glance |
| Conditions | Approximation, example/general distinction, domain/units |
| Evidence | Source pages and numerical tests |
| Clicks | State 0; changed object at each click; final held state |
| Continuation | Return state, retained conclusion and next operation that consumes it |

Reject a page whose purpose requires several unrelated 'and' clauses. But do not create artificial pages for two consecutive steps that fit legibly on one page. A formula derivation page and its interpretation page can be separate when the reader's task genuinely changes.

## Derivations Without Formula Walls

- Keep the main object recognisable. Prefer a stable m line then s line while constructing s; later m may be removed if not needed, but s remains the anchor.
- Begin with the known general expression; a solvable example extends it rather than overwrites it without explanation.
- Preserve substitution, change of variables, integration limits, coefficient/gain cancellation and assumptions where essential. A long supporting derivation can immediately follow a clearly supplied, qualified result, then return to the process. Do not hide required explanations in an appendix or gather all proofs far from their use. Do not interleave disconnected proofs into every small process change.
- Successive lines need not repeat the left-hand variable. Horizontal extension can work until it gets long, then contract deliberately to the established result.
- Known terms remain in place while only a new argument/coefficient changes. Keep complete expressions during rewriting; do not show a lone '=' or incomplete equation.
- Use semantic term-copy motion only where it communicates a substitution or identity. Straight source -> destination; no detour that crosses retained work.
- Derive before assigning a special-function or module name. The name is a label for an object already encountered.
- At the end, make the answer visibly stronger by size, weight, position or a restrained underline. Only after derivation is complete may intermediate work intentionally contract/fade to free space. Never erase a step while students still need it to follow the next one.

## Visuals That Explain Rather Than Decorate

Each illustration must answer 'what changes under this operation?' A second panel is not useful merely because it contains another correct graph.

Keep a fixed empty coordinate system, known reference, same message and parameters. If changing a parameter, label that specific parameter locally. Label axis quantities and units; show positive and negative frequency when necessary. Distinguish a spectrum from its magnitude, components from their signed sum, exact support from occupied bandwidth or first-null conventions.

Place attention at the operation itself: small arrows, circles, selected points, faded previous outlines, precisely matched guides. A pointer must touch the intended copy/edge/sample, not a generic central position. Arrow text must be separated from both the shaft and the graph. Demonstrate adding every original term when interpreting a sum, not only jump to the combined answer.

Formula before animation or animation before formula is a pedagogical choice. Start from what the audience already knows. Separate changes in different places into different clicks unless they are one directly matched event.

## Pacing

The user found TTR3/TTR4 too long despite mathematical completeness. TTR5 improves pacing by making demonstrations and takeaways carry meaning, without removing derivations. Do not make the lecturer narrate every symbol on every line. The screen should identify the changed quantity and result without physical pointing.

Use source scope, rehearsal, narration and click time to decide length. Neither the original 23-page TTR5 nor its later 116 physical states is a target: duplicated overview/zoom states and optional practice are not separate lecture topics. Avoid adding extra theory just because it is adjacent. A requested review can build each method's process, visit its operations and return with cumulative results; do not make it a dense formula catalogue or a second full lecture.

## Exercises, If Requested

An exercise is a worked solution students can copy, not just an animated demonstration. Keep the problem visible. Use 'Calculate: ...' rather than unexplained question marks. Include necessary prose and source-aligned equations. Show where intermediate quantities arise in the processing path before using them. A compact full input -> output overview can precede detailed steps. Let diagrams animate once, then hold while the solution accumulates. Do not add exercises to a request that explicitly excludes them (as TTR5 did).

## Source And Learner Fidelity

The actual current teacher material governs notation, derivation order, difficulty and coverage. Prior tutorials are style/examples, not proof of current scope. Capture a source ledger before editing. Do not silently rename h to p, switch Fourier conventions, drop normalization gains, or replace an idealization with a different system.

Every new symbol is introduced where its generating operation first occurs. If a beginner can only guess from an unlabeled curve what a filter or intermediate means, the page has failed even if the math is correct. A dense collection of technically true labels is not a high-density explanation.
