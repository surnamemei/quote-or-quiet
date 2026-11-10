# S41 result: long-form end to end on the 50 design biographies

Run 2026-11-10. Plan and run notes: docs/S41_LONGFORM_E2E_PLAN.md. Counts: results/runs/s41/S41_result.md (per-item
lists stay out of the release). Design data, not a sealed test.

| Quantity | Result | Prediction | Outcome |
|---|---|---|---|
| Slots | 1,492 from 50 biographies | | |
| Kept (Verified) slots | 147 (9.9%); 39 of 50 biographies keep at least one | 20 to 50% | failed |
| Decoys called wrong by both reviewers | 20 of 20 | at least 18 | met |
| False kept, both reviewers | 2 of 147 (1.4%); cluster-bootstrap 97.5% upper bound 3.4%; 3 by either | at most 2% | met |
| Rule Q: slots that become Qualified | 360 (24.1%) | 3 to 12 points | failed |
| Rule Q: value wrong for both reviewers | 19 of 40 reviewed (47.5%) | at most 15% | failed |
| Random dropped slots wrong for both | 5 of 20 | | |

Funnel: reader support at least 3 for 243 slots, gate passes for 200, Phi-4 agrees for 147. Retention is highest for
nationality (55%), person (26%) and year (23%) slots and near zero for free-form slots.

The two false kept slots: a question from the draft that asks for a person's nephew and is answered with the name of
his son (the name occurs in the page, so the gate passes), and a slot whose value is the pronoun "He", which is not an
answer. In both the value exists in the source and the source does not state the claim.

Reading.

1. The verification step keeps few slots of a 4B draft (one in ten) and those are right at about the rate of the
   short-answer rule; the stop criterion (false kept above 3%) is not met in the point estimate, and the upper bound of
   this small set does not exclude it. A sealed long-form test at this retention would say little; raising retention on
   design data comes first.
2. Rule Q does not carry over to long-form drafts. A slot value that merely occurs in a pinned page is wrong half the
   time, because the draft's false claims reuse real names and years from the same pages. This agrees with E6 of
   docs/S42_CLAIM_AUDIT_AND_PLAN.md: the existence of a quote is not evidence that the quote states the claim.
   Qualified output needs the same quote-sufficiency check as Verified output before it is shown.
3. Non-answer values (pronouns, fragments) have to be rejected before the gate.
