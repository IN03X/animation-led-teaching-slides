# Independent R1 Artifact Review

Frozen candidate: `C:/Users/10486/Desktop/Personal/博一/ELEG2310B/tmp/skill-e2e-validation/cold-first/candidate.pptx`

SHA256 verified before and after inspection: `3117ca0fd93b3364d63b17343cd49de61c3a09db7fd711f1dd547185be103fc6`.

Disposition: blocking teaching and rendering findings remain in R1. This report does not assess R3, certify classroom readiness, or certify native playback.

## Blocking Findings

### B1 [P1] The essential vertical-leg justification remains in notes rather than visible teaching states

Evidence: slide 8 stages 0-3, especially [stage 2 / click-022.png](C:/Users/10486/Desktop/Personal/博一/ELEG2310B/tmp/skill-e2e-validation/cold-first/quality-review/click-022.png), [final](C:/Users/10486/Desktop/Personal/博一/ELEG2310B/tmp/skill-e2e-validation/cold-first/slide-008.png), and `quality-review/demo-8-vertical.png` frames 0/14/28. The visible explanation says the other leg stays perpendicular, shows it turning and joining, then supplies `K=(-v sin(theta), v cos(theta))`. It does not visibly connect the already established quarter-turn rule to the rotated unit direction `(cos(theta),sin(theta))`. The angle/complement and projections of K are not identified sufficiently to supply that missing calculation geometrically either.

The full bridge DOES exist in the candidate's `ppt/notesSlides/notesSlide8.xml`: quarter-turn the horizontal unit direction, then multiply by signed v. The notes also explain negative and zero legs; those explanations are absent from the visible states. All component demonstrations use positive u,v and 35 degrees, whereas the conclusion claims any angle and the final page admits negative angles.

Novice consequence: students can copy the formula and the positive acute example, but the sine/cosine exchange, minus sign, and extension beyond that pictured case still depend on an unshown explanation. This is an insufficiency of the visible justification, not an incorrect coordinate formula or a demand for matrices.

Bounded repair criterion: visibly reuse `(s,t)->(-t,s)` on the rotated unit direction, scale by signed v, and state how reversed/zero legs and signed angles are handled before claiming the general rule. A concise geometric explanation can meet this; another full example or geometric zoom is not inherently required.

### B2 [P2] The general centre's coordinates are used before they are defined

Evidence: [slide 6, stage 0 / click-016.png](C:/Users/10486/Desktop/Personal/博一/ELEG2310B/tmp/skill-e2e-validation/cold-first/quality-review/click-016.png) introduces `Q=(u,v)=(x-a,y-b)` and `P=(x,y)` but never displays `C=(a,b)`. That definition first becomes visible on slide 9, after the two-page branch. Earlier slides defined only the numerical centre `(2,1)`.

Novice consequence: a and b appear as unexplained extra parameters precisely where the example becomes general. The relation of the new formula to subtracting the SAME centre must be guessed.

Bounded repair criterion: introduce `C=(a,b)` alongside `P=(x,y)` on slide 6 before using a,b.

### B3 [P2] Required local labels collide or detach from their objects in held and moving states

- Slide 3 entry, [click-007.png](C:/Users/10486/Desktop/Personal/博一/ELEG2310B/tmp/skill-e2e-validation/cold-first/quality-review/click-007.png): active P/C labels overlap the gray old P/C labels before movement starts. At stage 1/2, `C moved to 0` runs along the x tick labels; see [click-008.png](C:/Users/10486/Desktop/Personal/博一/ELEG2310B/tmp/skill-e2e-validation/cold-first/quality-review/click-008.png) and slide-003.png. Native embedded subtract frames 0 and 28 confirm both defects.
- Slides 7 and 8: H is printed directly over the gray unrotated Q reference marker/vertical leg. See [click-018.png](C:/Users/10486/Desktop/Personal/博一/ELEG2310B/tmp/skill-e2e-validation/cold-first/quality-review/click-018.png), click-020.png through click-023.png, and both final pages. Embedded horizontal frame 27/28 and vertical frame 0/7/14/21/27/28 confirm that this persists, rather than being a contact-sheet artifact.
- Slide 10: the `C=(2,1)` label sits across the y axis well left/below its actual point, without a leader. Entry also overlaps `Turning the same P` with the reference P label. See [click-027.png](C:/Users/10486/Desktop/Personal/博一/ELEG2310B/tmp/skill-e2e-validation/cold-first/quality-review/click-027.png), [final](C:/Users/10486/Desktop/Personal/博一/ELEG2310B/tmp/skill-e2e-validation/cold-first/slide-010.png), and embedded thirty frames 0/7/14/21/27/28.

Novice consequence: the learner cannot reliably distinguish the transformed endpoint from its reference, read the local coordinate ticks, or associate the centre label with the fixed centre. This directly weakens the visual explanation of subtraction, component construction, and rotation about C.

Bounded repair criterion: separate reference/active labels before movement, reserve a gutter below tick labels, move H away from the reference marker, and attach the centre label locally or with a leader. Recheck the held endpoints and intervening states.

### B4 [P2] The numerical process's rotation shortcut bypasses its own operation

Evidence: slide 2's visible `Rotate about zero` label, [click-003.png](C:/Users/10486/Desktop/Personal/博一/ELEG2310B/tmp/skill-e2e-validation/cold-first/quality-review/click-003.png). In actual `ppt/slides/slide2.xml` and its relationships, `operation-1-text` links via `rIdNav2` to `slide6.xml`, the general-angle question, rather than slide 4's 90-degree operation. The same destination is reused in the numerical route on slides 3-5. This matches manifest.links; it is not inferred from link counts.

Novice consequence: using the process as a router skips the demonstration establishing `Q'=(-1,2)` and arrives at a generalization that presumes the numerical example is complete. Normal sequential slide order includes the operation, but the optional shortcut does not preserve its meaning.

Bounded repair criterion: numerical-route rotation links should reach the quarter-turn step; general-route rotation links may reach the general-angle branch. Native hyperlink behavior was not exercised.

## Positive Findings And Mainline Assessment

| Sequence | Actual evidence and teaching value |
| --- | --- |
| Slide 1, stages 0-1 | Known P and C, fixed centre and distance, and the requested CCW quarter turn are visible. The task is concrete before algebra. |
| Slide 2, stages 0-3 | Clicks accumulate subtraction, `Q -> Q'`, and addition while the three-operation scaffold remains stable. This is some dynamic construction, but not a fully constructed numerical overview: Q is already `(2,1)` on entry, rotation remains a placeholder, and the final numerical output is not filled into this overview. |
| Slides 3-5 | The actual numerical process is constructed geometrically across the sequence, rather than presented as completed thumbnails. Fixed axes continue across these pages. Subtraction preserves the displacement, the quarter turn visibly turns its two legs, and addition translates the SAME turned offset back to C. Final coordinates are `(1,3)`. Label failures are B3. |
| Slide 6 -> 7 | The selected middle operation and explicit missing question motivate the branch. Slide 7 explicitly identifies Q as coming from subtracting C, then splits it into coordinate legs. The example change to 35 degrees is locally labeled. A geometric zoom would not inherently improve this straightforward algebra/geometry focus; its absence is not a defect. |
| Slide 7 -> 8 | H remains the same object with the same coordinates, numerical parameters, and axes. Turning the remaining leg and joining it head to tail has a visible purpose: recover the endpoint Q'. The visible proof is incomplete under B1, but this is not an unrelated new process. |
| Slide 8 -> 9 -> 10 | The return is substantive. The exact three-operation layout and selected middle operation from slide 6 return with U,V formulas; clicks then form x',y'. The retained 90-degree example remains accessible. Slide 10 visibly reuses the returned U,V rule for the SAME P,C, changing the requested angle to 30 degrees, then plots the resulting point. This is a usable return and consumer, not an unchanged overview followed by an unrelated topic. |
| Slide 11 | The same process closes the lesson with offset/output formulas, signed-angle convention, equal scales, fixed-centre/distance checks and the original `(1,3)` answer. The general method and original task remain connected. |

## Mathematical And Readability Notes

Independent arithmetic agrees with the visible numerical endpoints. At 90 degrees, Q=(2,1) becomes (-1,2): dot product 0, oriented cross product +5, squared radius 5. Adding C gives (1,3). At 30 degrees, Q'=(1.2320508,1.8660254), giving P'=(3.2320508,2.8660254), again squared radius 5. At the illustrated 35 degrees, H=(1.6383041,1.1471529), K=(-0.5735764,0.8191520), and their sum is (1.0647277,1.9663049), matching the displayed endpoint locations. The final general coordinate formulas are correct and require no matrices. Formula correctness does not resolve B1.

Secondary notation concern: slide 10's stage 1/final renders `V=2 1/2 + sqrt(3)/2 = 1+sqrt(3)/2`, with no multiplication sign between 2 and 1/2. A beginner can read that as the mixed number two-and-a-half. Explicit multiplication or parentheses would remove the ambiguity. This is separate from the correct intended numerical result.

The large retained calculation lines and separated bottom results are readable on the final pages. Sampled formula reveals remain complete and do not cross retained equations. The reported defects are local object/label problems and missing visible reasoning, not a claim that the whole deck is unreadable.

## Evidence Boundaries

Inspected all 11 final PNGs and all 32 individual click endpoint PNGs; all 95 supplied modeled snapshots through per-slide motion sheets; individual modeled images 023,032,051,060,066,080,086 at full size; all six first/middle/final demo strips. Additionally inspected the frozen PPTX's own embedded demonstration frames 0,7,14,21,27,28 for all six demos in memory. These are sampled states, not every native display frame. The modeled 0/350/700/1050 ms samples alone cover only the start of the 4840 ms demonstrations; the embedded middle/late frames were therefore checked separately.

The timeline evidence's sourceSha256 matches the frozen candidate. The neighboring source modules are not exact frozen-source evidence: `lesson-story.mjs` contains a `perpendicular-reason` equation absent from both the frozen slide 8 objects and manifest.equations. Its `route(false,false)` would also show `Q=P-C` on slide 2 entry, whereas the actual entry shows `Q=(2,1)`. Source intent was not credited as visible teaching evidence.

Applied the installed skill's SKILL.md, mainline-branches.md, teaching-contract.md and acceptance.md; consulted its reference-role/failure guidance and a bounded sample of its archived visual examples. No parent history, ELEG2310B project documents, author workspace, external math report, or R3 artifact was read. No schema test was used as teaching evidence. No edits, rebuilds, environment changes, PowerPoint automation or UI interaction were performed; only this new report was written.

Native PowerPoint playback/navigation/replay: NOT TESTED. Timed rehearsal and user teaching approval: NOT TESTED. Desktop playback is unavailable per the user's stated pipe limitation. R3 requires its own exact artifact/hash and a separate independent recheck; these R1 findings must not be carried over as unverified R3 defects.
