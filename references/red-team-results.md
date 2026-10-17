# Independent Red-Team Record

Date:2026-10-15. Reviewer started without the originating conversation and was restricted to the skill and isolated test workspace. No original course folder, PowerPoint operation, dependency installation, or live-deck edit.

Initial review found five concrete defects. They were repaired in the stage adapter or review wrapper, without rewriting the archived raw provenance sources:

| Finding | Repair | Observed regression evidence |
| --- | --- | --- |
| E.parse retained the author's separate PPTX-skill schema path | Adapt E.parse as well as Path; reject unadapted known schema references | Staged Python files contain no old schema path; final golden and edge packaging pass |
| Generic end title forced a course link | Apply historical course routing only to historical content | Both two-slide fixture links resolve to cover without defining a course alias |
| Empty demos indexed nonexistent clickMedia | Explicit no-media path with consistency assertions | Empty-demos fixture completes review, no-frame audit and PDF preparation |
| Generic cover/end excluded from endpoint/timeline review | Exclude actual inherited pages, not authored generic cover/end by name | All five expected click endpoints and fourteen modeled frames exist and were visually inspected |
| PDF relocation applied twice | Track manifest-resolved shapes and skip second application; wrapper exports already-collapsed static preview | Point starts at100 and ends at200, not300; saved preview, manifest-route preparation and PDF input agree |

The same reviewer rechecked the current staged implementation and saved artifacts, independently verified the table above, and reported all five resolved with no remaining concrete blocker in that recheck. It also checked candidate-bound review/timeline hashes, two PDF pages/two links, blank author metadata and embedded image pixel equality.

This review did not certify native PowerPoint scheduling, native font metrics, rehearsal duration or universal future learner comprehension. Separate final-adapter golden/new-topic replay results are recorded in `test-results.json` with actual copied evidence under `assets/tests/evidence`. The raw original engine is intentionally preserved as provenance: execute only its staged, adapted copy via the workflow wrapper.
