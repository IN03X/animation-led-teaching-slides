# Beginner Storyboard: One Scale, Then a New Value

Source: the current request only. Arithmetic prerequisite: subtraction and division.
One persistent table; nine visible states, eight advances, approximately 2-3 minutes of planned narration. This is not nine slides or a timed rehearsal.

| State | Visible change | Local reason and result |
| --- | --- | --- |
| 0. Input | Rows A=10, B=20, C=30; target [0,1]; empty working/output columns. | Start with the actual training data. |
| 1. Endpoints | Mark A=10 as minimum and C=30 as maximum. | These training endpoints must become 0 and 1. |
| 2. Span | Beside the endpoints, show 30-10=20. | This full distance will become one unit. Retain 10, 30, 20. |
| 3. Subtract | Fill shifted cells: 10-10=0, 20-10=10, 30-10=20. Keep raw values. | Subtract 10 to put the lower endpoint at zero. |
| 4. Divide | From those SAME cells, show 0/20=0, 10/20=0.5, 20/20=1. | Divide by the full span 20 to make the upper endpoint one. |
| 5. Save | Keep the completed table; collect the established operations into y=(x-10)/(30-10)=(x-10)/20. | x means the value being processed. Label 10 and 20 as fixed from training. |
| 6. New Input | Add a separate New row: x=25, blank working/output cells. Keep the saved rule and training outputs. | Measure the new value on the established scale. |
| 7. Subtract New | Highlight the saved subtract-10 operation; fill 25-10=15. | Use the training minimum again. |
| 8. Divide New | Highlight divide-by-20; fill 15/20=0.75. Hold table and rule. | Use the training span again: 25 maps to 0.75. |

Final held table:

| Row | Raw x | x-10 | (x-10)/20 |
| --- | ---: | ---: | ---: |
| A (training) | 10 | 0 | 0 |
| B (training) | 20 | 10 | 0.5 |
| C (training) | 30 | 20 | 1 |
| New | 25 | 15 | 0.75 |

Final retained conclusion: establish min=10 and span=20 from training once; use y=(x-10)/20 for subsequent values. Keep the training rows unchanged.
Put the necessary condition beside the saved rule: positive training span; values within [10,30] map into [0,1]. No clipping or guarantee for all possible future values is implied.

No focus branch, return page, router, extra theory, or exercise is needed. Every operation is legible in the same table. Row identities, column positions, raw values, saved parameters, and training outputs persist. Entry is static; reveal only the changed cells, once per advance, then hold. Numerator and final quotient appear on separate advances. The final answer receives the strongest emphasis.

The saved fixed-rule result opts into keepVisibleDuringUse=true. Its later consumers carry the rule, which may appear incorporated into 25-10 and 15/20 rather than duplicating the proof. Other known prerequisites do not automatically need to stay visible.

The story-map checker checks graph dependencies only. Mathematical checks, review observations, and their limits are saved separately. The initial checker report predates this opt-in; followup-check-receipts.json records verification against the updated installed checker.

