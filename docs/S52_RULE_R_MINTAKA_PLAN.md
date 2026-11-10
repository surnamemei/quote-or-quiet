# S52: rule R on a second set of open questions (plan, 2026-11-10 22:16, before any S52 output)

Purpose: rule R (docs/S48_RELATION_FREE_PLAN.md) was defined and first measured on the FRESH-5 releases. This is a second, different set that R was not designed on: the 697 releases of the frozen system
on the Mintaka test set (results/runs/s22/mintaka_test_releases.jsonl, source s19; natural crowd-worker questions). The set was opened and adjudicated earlier for other purposes, so this is a confirmation on an
unseen-by-R set, not a sealed test; the sealed test is the S40 secondary analysis registered on 2026-11-10 20:12 in docs/S40_PLAN.md.
Rule R, code (m_cands.py, m_run.py: copies of the S48 scripts with the data file changed), the review protocol (a random 300 releases, the displayed quote of the first accepted span, the R witness where it differs, 30 decoys, two
blind quote-only reviewers) and the predictions are those of S48, unchanged: the displayed quote is misleading in 8 to 20%; R keeps 65 to 90%; misleading among kept at most 2%; 'states' for both at least 90%; the judge accepts a
swapped answer for at most 10% of candidates. Reported whatever the result.

## Result (22:25; results/runs/s52/M_result.md and M_small_judge.md; the set was opened before)

Population: the 697 'source s19' releases are the part of the later combination rule (with its format gate) that comes from the frozen system, as on FRESH-5 (601 of 727); 685 of the 697 had a candidate span. R kept 453 of 685
(66.1%); the judge accepted a swapped answer for 3 of 2,166 candidates (0.14%). Blind quote-only review of 391 rows (300 releases, 61 R witnesses that differ from the displayed quote, 30 decoys; 28 distinct decoys, all caught):

| Quotes | n | misleading for both | 'states' for both |
|---|---|---|---|
| Displayed quote (first accepted span), 300 releases | 300 | 129 (43.0%, 97.5% upper 48.8%) | 123 (41.0%) |
| Displayed quote, the 192 releases R keeps | 192 | 63 (32.8%, upper 39.9%) | 99 (51.6%) |
| Rule R witness, the same 192 releases | 192 | 46 (24.0%, upper 30.6%) | 118 (61.5%) |

Against the predictions: displayed quote misleading in 8 to 20%: far off (43.0%). R keeps 65 to 90%: met at the edge (64.0% of the sample, 66.1% of all). Misleading among kept at most 2%: FAILED (24.0%). 'States' at least 90%: FAILED (61.5%).
Judge accepting a swapped answer at most 10%: met (0.14%).
Rule R, which left 1.0% misleading on FRESH-5, leaves 24% on natural Mintaka questions: the 4B judge accepts sentences that mention the answer entity or the page topic without answering the question (twelve examples read, among them a sentence on a
sports group for the home team of Fenway Park and a sentence on an award shortlist for the largest city in Scotland). Many Mintaka releases rest on list, index or loosely related pages, where no sentence states the answer.
The small judge of S51, trained without any Mintaka row, scores the review rows with AUROC 0.897 (361 non-decoy rows); accepting at 0.5 it passes 154 rows and 8 are misleading (5.2%, upper 10.0%); among the displayed quotes it passes 126 of 300 with 7 misleading (5.6%).
Reading: the relation-free requirement is not established by FRESH-5 alone; it fails on natural questions with the 4B prompt judge and a learned judge transfers better. The S40 analysis registered on 2026-11-10 20:12 is therefore a test of a rule with one success and one failure.

