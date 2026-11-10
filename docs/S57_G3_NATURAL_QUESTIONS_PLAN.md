# S57: gate G3, rule R27 on natural questions not seen before (plan, 2026-11-11, before any S57 output)

Gate G3 (docs/PROGRESS_TRACKER.md): the shown quote does not state the answer; threshold 97.5% upper bound at most 3%; at least 250 reviewed releases; registered, unseen data, valid decoys.
Population: Mintaka test releases (results/runs/s22/mintaka_test_releases.jsonl) that no reviewer has seen: the 397 releases of the frozen system that S52 did not sample, and all 308 releases of the page-pinning variant (source 'pin'), 705 in all. None of them was used to design or tune rule R, the 27B prompt or anything else; the 27B prompt was tried on the 300 S52 review releases (design data), which are excluded.
Rule R27 (frozen now, as registered for S40 on 2026-11-10 23:33): candidate spans as in results/runs/s52/m_cands.py (gate-accepted spans of the answer on the release's pages, up to 30); a candidate is eligible if its quote is a sentence (sent) and contains the question's numbers and ordinals (N); the first eligible candidate for which Qwen3.8-27B (chat, thinking off, temperature 0) answers YES to the rule R prompt for the answer, and NO for a swapped answer of the same shape (seed 5701 for the pin releases; the S52 swaps for the others), is the witness. Otherwise the release is withheld.
Review: every release with a witness (all, not a sample), the witness quote, plus the displayed quote (first accepted span) where it differs, plus 30 decoys (witness quote with the swapped answer). Two blind reviewers per row, quote only, verdict states / incomplete / not; misleading = both 'not'.
Predictions: R27 gives a witness for 40 to 65% of the 705 releases; at least 250 witnesses; misleading among witnesses at most 2.5% (point), and the gate's upper bound at most 3%; displayed quote misleading for 15 to 40% of the releases where it differs from the witness; decoys at least 27 of 30.
A failure is reported as failed and the rule is not changed on these data.

## Result (2026-11-11 10:1x; results/runs/s57/G3_result.md)

R27 gave a witness for 367 of 705 releases (52.1%). Blind review of 543 rows (367 witnesses, 146 differing displayed quotes, 30 decoys), two reviewers each, quote only; decoys 30 of 30 misleading for both (valid). Every verdict file was checked for 181 rows, matching row numbers, no blank verdicts, and notes that refer to its own sheet (two reviewers had used the same scratch script name).

| Quotes | n | misleading for both | 'states' for both |
|---|---|---|---|
| R27 witness, every release with a witness | 367 | 2 (0.5%, 97.5% upper bound 2.0%) | 315 (85.8%) |
| Displayed quote where it differs from the witness | 146 | 59 (40.4%, upper 48.8%) | 22 (15.1%) |

Against the predictions: witnesses 40 to 65%: met (52.1%). At least 250 witnesses: met (367). Misleading among witnesses at most 2.5%: met (0.5%). Upper bound at most 3%: met (2.0%). Displayed quote misleading 15 to 40% where it differs: FAILED, just above (40.4%). Decoys at least 27 of 30: met.
Gate G3: T met (2.0% <= 3%), N met (367 >= 250), V met (registered, unseen releases, decoys 30 of 30). The gate passes. Limits: language-model reviewers; Mintaka only (crowd-worker questions over Wikipedia); 48% of the releases have no witness and are withheld; 'states' for both is 85.8%, the rest mostly 'incomplete' (the quote agrees but leaves part of the question to the page).
