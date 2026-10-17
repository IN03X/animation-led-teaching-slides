# Mainline -> Branch -> Return

## The Problem This Solves

A deck can have correct mathematics, attractive pages and prominent answers yet be incomprehensible as a sequence. The reader remembers neither why the current intermediate exists nor how it helps the main task. A route indicator such as "generation / spectrum / recovery" locates a chapter, not the reasoning inside it.

Design at two scales: the whole task, and the concrete operation currently needed. At either scale a viewer should be able to point to the object being processed, the reason for this operation, and the result we can now use. These can be communicated by objects, arrows and a dominant expression; do not turn them into three repeated prose labels on every slide.

## The Reusable Cycle

| Moment | What the viewer sees | What advances |
| --- | --- | --- |
| Establish | A process BUILDS from known input through actual operations; empty axes exist before moving curves | The viewer acquires the picture, not a collection of finished thumbnails |
| Need | A known operation or expression cannot yet be completed; its unresolved part is selected | A concrete reason to inspect this part |
| Focus | The selected object is enlarged or otherwise continuously isolated; identity and sufficient context persist | Only the necessary local change or calculation |
| Establish result | A visible operation gives the local result, with gain, units and assumptions | One supporting fact, not a new disconnected topic |
| Return | The SAME process/context reappears, with the result attached to its originating object | The previously unresolved part is now known |
| Use | Combine the known parts or proceed with the next operation | The main task actually progresses |

Do not force a detour when the operation is obvious on the overview. A branch can take several pages or one click. Actual geometric zoom is appropriate when teaching that a detail belongs to the existing process; it is not a substitute for motivation. Never make the reader infer location from a tiny top-left subtitle.

### Require Evidence in the Diagram, Not Only in the Outline

A cold-start rotation lesson exposed a weaker interpretation: static "subtract / rotate / add" boxes, an independent animated graph on later pages, and a formula beside the same boxes on return. The document can CLAIM a branch cycle while the operand never visibly travels through it. Do not accept a story-map pass, a selected box, a subtitle such as "Inside", or text saying "same object" as the evidence of continuous visual focus.

Before entering the detail, build the actual object/quantity through the overview's operations, leaving unresolved work visibly unresolved. At the boundary, retain/copy/enlarge that known operand or preserve its recognizable figure/formula before changing the local part. A physical zoom is optional; an unexplained reset to a new figure is not. On return, the actual originating representation must gain the new result, and a subsequent action must use it. After ignoring headings and speaker notes, a reviewer should still be able to identify the selected object and the changed local operation in the central figure/formula. For a simple table that already makes every operation legible, staying in the same table is preferable to creating a fake detail trip.

Source and reference labels need a coincidence policy: when they occupy the same point at a motion's first frame, show one readable label, then introduce the old-position label after they separate. In geometry, a projection formula needs its angle/components marked on the figure; a new term's name in a distant sentence is not an attachment to the corresponding arrow or point. Review these in actual first/middle/last frames, not only the final slide.

## Worked Case: Inspecting One Transmitted Signal

The archived corrected TTR5 is a CASE, not a prescribed topic or length. Page numbers below refer to that included 116-slide file.

| Source state | Cognitive role |
| --- | --- |
| 6, then 7-8 | Build the continuous message -> sample values -> pulses -> sample values -> recovered message picture. These are the same sample values, not unrelated drawings. |
| 10 | The known s(t) and its transform S(f) describe the SAME signal. Introduce S(f)=M_delta(f)H(f); show the factors arising from known time-domain objects. |
| 11-16 | Focus on M_delta: why sampling produces copies of M, and when copies stay separable. The formula describes a visible operation, not a new route. |
| 17 | Return to the same product and process. The sample-spectrum factor is now known; retain its result. |
| 18-20 | Focus on the existing pulse h and its response H; time/frequency labels, zero locations and a sufficiently wide axis make the shape identifiable. |
| 21-22 | Return with BOTH factors, then multiply to obtain S. First-null bandwidth is a consequence of that spectrum, not the whole purpose of inspecting it. |
| 23-27 | Receiver starts with s. Read m(nTs), then form m_delta; do not assume the unknown m is already available. |
| 28-29 | From known M_delta, select M with H_LP and the necessary gain. Show the two equivalent computation routes separately; visibly select the known-kernel convolution route. No extra G/g intermediate. |
| 30-33 | A sample's time sets its sinc centre and its value sets its weight. Move, scale and add each signed response with visible corresponding points. Return to the same receiver process. |
| 39-42 | Review example: establish the complete AM process; focus on generation, spectrum, recovery in turn; each return accumulates its result before the next focus. Normal direction keys traverse the sequence. |

Inspect `assets/continuity/01-overview.png` through `08-return-both-factors.png` in order, and `09-receiver-map.png` through `12-receiver-return.png`. Open full-size images too. `provenance.json` identifies the exact source and the limits of the adapted preview evidence. The complete deck contains actual frame sequences, not just these static examples.

**Known defects are not positive targets.** Cold-context visual review found frequency tick-label collisions in the transitional images `02-focus-enter`, `04-return-motion` (around x=665-705,y=620), and `06-next-focus` (around x=375-400,y=620). Keep these as failure specimens: endpoint/scene continuity does NOT imply clean middle frames. Before reusing this motion, clip or hide inactive labels, reserve a gutter, or sequence the label fade separately, then inspect the changed frames. The original case is archived unchanged, not silently repaired. Moving/faded curve crossings in `13-review-enter` and `15-review-recover` also require judgment: context can remain, but the current operation and labels must stay unambiguous. These are adapted-preview observations, not a claim of native PowerPoint testing.

The transferable idea is decomposition of a known task and recombination of established results. For a moving-average lesson, the context could be "input -> local window -> mean -> output"; a necessary branch explains startup padding, returns with the chosen boundary rule attached to the first window, then computes the SAME output. Do not import m/s notation, sampling theory or a three-phase syllabus into that lesson.

## Three Different Kinds of Page

| Role | Main content | What must remain accessible |
| --- | --- | --- |
| Process | Input, actual operation, output; animation carries the change | The local route, known objects and current task |
| Supporting derivation | One needed fact; cumulative, reproducible steps; prominent final expression | Its originating object and why this result is needed |
| Returned overview | The same established process plus the new conclusion | Previous useful conclusions and their conditions |

Supporting results may be stated before a long proof when that keeps the visible process coherent. Identify the result as supplied under stated conditions, place the full derivation immediately next, and return before advancing. Essential construction/recovery steps still cannot be skipped. A numerical special case extends a general expression; it does not silently replace it.

Bottom conclusions remain useful on derivation pages. They are not all equal in lesson importance: a transform identity is support; the completed S or recovered m is the main result. Return summaries carry only the result needed to proceed, not every intermediate line. If every page looks like a separate final takeaway, redesign the sequence.

## State And Object Discipline

- Use stable identities for the message/data, intermediate and result across overview and detail. A drawing, formula symbol and plotted sample must point to the same object. Introduce intermediates where the operation creates them; remove them from later pages once they are no longer the known input.
- Labels are part of the explanation: plot quantity, axis quantity/units, reference centre, amplitude and relevant edges belong next to the plotted objects. A sinc that appears to be a rounded bump or an ambiguous overlapping spectrum does not teach the intended property.
- Preserve common axes for panels that are directly compared or multiplied. A deliberately different example/view must be visibly identified. A triangular general-spectrum illustration and a finite sinc-sum time example are not a single unannounced Fourier pair.
- During transformation, alter the changed term or object, not the whole expression. Move an established formula if its role changes; do not disappear/recreate it to simulate movement. Do not animate scaffolding or equals signs as the subject.
- A sample-to-response demonstration needs explicit time/height correspondence. A moving curve alone does not show which sample determined its centre or sign. Mark the source and destination; show individual terms before their sum.
- Return to the actual originating process, not another schematic with similar labels. Retain accumulated conclusions at their originating objects, with enough context to recognize them. A row of static thumbnails is not a continuous-process overview.
- Keep ordinary forward/backward navigation functional. Click links are optional shortcuts, not the only way through the lesson. Zoom clips wait for a click after slide entry. Preserve an accepted playback backend; never broadcast experimental restart/group/previous-action changes because static renders look correct.

## Story Map And Review

Before authoring, write the objects, results, chronological states, branch origins, returns and consumers in a story map. `scripts/story-map.py` checks prerequisites, nested branch closure, same-scene returns, cumulative returned results, and use of each branch result. See `assets/continuity/story-map.example.json`.

In the map, `requires` means established knowledge; `carries` means the conclusions visibly retained in that state. They are not synonyms: supporting algebra need not remain everywhere. For a key rule that a later operation must visibly reuse, set the result's `keepVisibleDuringUse` to true and include it in that operation's `carries`; its visible form may be the rule incorporated into the actual calculation, not another copy of the whole derivation. This opt-in catches dropped key rules without forcing a wall of past equations onto every page. A focus state's active object must match the originating selected object. Internal results from a nested branch need not persist on every outer overview once absorbed into the parent conclusion.

This is a planning lint, not evidence that diagrams really share an object, that the formulas are correct, or that animations render as intended. A perfectly filled JSON can accompany a bad slide. Review the rendered before/inside/after sequence and actual package, then test native navigation separately.

For each branch, record a concrete answer from visible states: **what brought us here; why this detour; what was established; where it returned; which next step uses it**. Failure of any link blocks narrative acceptance even if the isolated page looks polished. Do not repair a missing link by adding vague prose. Often the correct repair is retaining a known expression, showing one operation, or attaching its result to the existing process.
