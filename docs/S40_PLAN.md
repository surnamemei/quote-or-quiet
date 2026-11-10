# S40: version 2 on a third sealed set (pre-registration, 2026-11-10, before any S40 item is run or opened)

Why: on the S29 sealed set the two-source cell (V2) passed its registered secondary test (3 real errors in 144 added releases, coverage 0.525 to 0.568), but it was evaluated on the same set that led to its acceptance as a secondary hypothesis. A version 2 with the cell rule is frozen here and tested once on new sealed questions.

## Data
- 3,040 questions built offline by results/runs/s40/s40_build.py from the S29 Wikidata candidate pools, same filters, new seed (4040). Every S29 sealed and pilot subject (relation, Wikidata id) and every S29 question string is excluded. Relations: birth_place 800, birth_year 600, death_year 400, director 600, author 500, office 140 (pool exhausted after exclusion); capital 0 (exhausted); founded not used. Strata low 1,866, mid 1,030, high 144.
- Hashes in results/runs/s40/seal_hashes.txt. The item file is read only by the prefetch and the pre-registered run; analysis code prints counts and aggregate results.
- Search results from the free-search-mcp pool, prefetched with the S29 prefetch code.

## Version 2 (frozen now)
- Release rule = the frozen S19 rule, plus the two-source cell in its registered wording (support 2 of 3, Phi-4 agrees, deductive gate passes, the missing source is the Wikipedia reader pair and both its readers abstained). Code: results/runs/s29/s29_v2.py logic applied to the S40 outputs, no other change.
- Independent title retrieval (S23) is added only if it passes S39 under the rule fixed in docs/S39_PLAN.md before S40 is run; if it does, this document gets a dated line before the S40 run saying so, and V2+indep is the primary system with V2 alone reported as well. If S39 is not finished when the S40 run starts, V2 alone is primary.
- Dated 2026-11-10 01:05, still before any S40 run: the S40 chain (results/runs/s40/run_s40.sh) starts when S39's generation ends, before S39's review can be done, and it does not run the independent-retrieval generation. So V2 alone is the primary system for S40. If independent retrieval passes S39, it is tested in a later sealed run, not added to S40.
- Dated 2026-11-10 04:10, still before any S40 run: the search prefetch stopped at 706 of 3,040 questions on repeated bot-check failures (the code never bypasses them). The chain was stopped before it took the GPU lock; the prefetch is resumed with cool-downs (30 minutes, raised to 2 hours at 05:00 after the first pass added only 37; at 09:15, after three passes of about 36 each, the gap between queries was raised from 2 s to 20 s and the cool-down set to 1 hour; same search pool and code otherwise) (results/runs/s40/prefetch_loop.sh) and the chain now waits for its completion marker. No other change.
- Dated 2026-11-10 14:30, still before any S40 run: the prefetch loop and the chain script died together at about 14:20 (the shell could not fork: 'Resource temporarily unavailable'). 1,316 of 3,040 queries were cached; the last pass had added 359 in 8,500 s. Both were restarted unchanged (same scripts, same pool). No rule or parameter changed.
- Dated 2026-11-10 14:35, still before any S40 run: the gap between prefetch queries was changed from 20 s to a random 10 to 12 s (fsm_prefetch40.py reads FSM_GAP_RANGE; prefetch_loop.sh sets it), at the user's request, to shorten the wait. The cooldown after a bot-check stop stays at one hour and bot checks are still never bypassed. Same search pool and code otherwise.
- Dated 2026-11-10 15:05, still before any S40 run: Windows now reserves TCP ports 11437 to 11536, so the local Ollama server could no longer bind its port 11535 ('forbidden by its access permissions'). The chain script run_s40.sh uses port 11540 for Ollama instead (infrastructure only; models, prompts, code and options unchanged). The 4B server stays on 18000.
- No rule was added for the S29 failure modes (later officeholder for a past year, namesake popes); they are reported, not fixed, to keep the test honest.

## Endpoints (same protocols as S29)
1. L2 (primary): adjudicated errors of version 2 (two blind reviewers with gold shown, quote check on removing verdicts, removal needs both; at least 11 of 12 decoys valid). L2 holds if the corrected one-sided 97.5% Clopper-Pearson upper bound over all 3,040 questions is below 1% at coverage of at least 35%.
2. L1-a: version 2 gold-relative SER lower than B0, B1, B2, B3 (closed-book prompts from docs/CRITERIA_REVISION_L1.md), exact McNemar one-sided, Holm.
3. L1-b: non-inferiority to the agreement-score ablation at exactly version 2's coverage (edge interpolation), truth-relative errors from a blind review with gold hidden (S36 rubric, decoys), margins +0.25 points SER and -1 point yield, bootstrap 10,000.
4. Original L1 (50% fewer errors than the ablation) reported; prediction not met.
5. Secondary: the frozen S19 rule alone on the same outputs (coverage and errors), to measure the cell's gain on new data.

## Predictions (written now)
- Version 2 coverage 0.50 to 0.66; frozen rule alone 0.47 to 0.60; gain from the cell 2 to 6 points.
- Gold-relative wrong at most 4% of version 2 releases; adjudicated errors at most 22 (L2 met); truth-relative errors of version 2 at most 8.
- L1-a met; L1-b met; original L1 not met.
If any prediction fails it is reported as failed.

## Secondary analyses added 2026-11-10 10:20 (still before any S40 run; from docs/S42_CLAIM_AUDIT_AND_PLAN.md)
Version 2 and the five endpoints above are unchanged. Two rules are applied to the same outputs afterwards and reported separately.
- Rule Q (Qualified state). A question that version 2 does not release is Qualified if its max-support candidate passes the deductive gate. The output is the page title and the quoted sentence, with the cross-check that failed; the system asserts the quote, not the answer. Reported: count, share of Qualified items whose quoted answer matches the reference answer, overall and by relation. On S29 (post hoc, frozen rule as base): 384 Qualified (11.4 points), 81.0% match, 47% for questions with a year. Predictions for S40: Qualified adds 4 to 10 points on top of version 2; match 78 to 92% (S40 has fewer questions with a year: 4.6% against 11.9%).
- Rule T (time frame). A released answer to a question that names a year is moved to Qualified unless the quoted sentence holds that year or a year range that covers it. Designed on S29's one wrong release, so post hoc there: it moves 9 of the 11 releases on year questions (8 match the reference, 1 is the wrong one). Prediction for S40: at most 10 releases moved; they are listed with their review verdicts.

## Order
After S39 finishes (GPU free): prefetch done -> frozen pipeline generation on S40 -> Phi-4 -> alias -> closed-book B0/B1 -> scoring -> review sheets -> blind reviews -> decisions. Version 2 is not changed between now and the run.

Run note 2026-11-10 10:19 (before any S40 run): s40_run.py (phi4 and alias stages only), s40_score.py, s40_v2.py and
s40_closed_judge.py now import the no_retrieval2 stub first. These stages do no retrieval, and without the stub each
loaded the 37 GB embedding table into RAM. The stub raises on any use of vkg.retrieval2, so no output can change. The
gen stage is untouched and still loads the table, as in S19 and S29.
