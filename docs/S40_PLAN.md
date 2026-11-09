# S40: version 2 on a third sealed set (pre-registration, 2026-11-10, before any S40 item is run or opened)

Why: on the S29 sealed set the two-source cell (V2) passed its registered secondary test (3 real errors in 144 added releases, coverage 0.525 to 0.568), but it was evaluated on the same set that led to its acceptance as a secondary hypothesis. A version 2 with the cell rule is frozen here and tested once on new sealed questions.

## Data
- 3,040 questions built offline by results/runs/s40/s40_build.py from the S29 Wikidata candidate pools, same filters, new seed (4040). Every S29 sealed and pilot subject (relation, Wikidata id) and every S29 question string is excluded. Relations: birth_place 800, birth_year 600, death_year 400, director 600, author 500, office 140 (pool exhausted after exclusion); capital 0 (exhausted); founded not used. Strata low 1,866, mid 1,030, high 144.
- Hashes in results/runs/s40/seal_hashes.txt. The item file is read only by the prefetch and the pre-registered run; analysis code prints counts and aggregate results.
- Search results from the free-search-mcp pool, prefetched with the S29 prefetch code.

## Version 2 (frozen now)
- Release rule = the frozen S19 rule, plus the two-source cell in its registered wording (support 2 of 3, Phi-4 agrees, deductive gate passes, the missing source is the Wikipedia reader pair and both its readers abstained). Code: results/runs/s29/s29_v2.py logic applied to the S40 outputs, no other change.
- Independent title retrieval (S23) is added only if it passes S39 under the rule fixed in docs/S39_PLAN.md before S40 is run; if it does, this document gets a dated line before the S40 run saying so, and V2+indep is the primary system with V2 alone reported as well. If S39 is not finished when the S40 run starts, V2 alone is primary.
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

## Order
After S39 finishes (GPU free): prefetch done -> frozen pipeline generation on S40 -> Phi-4 -> alias -> closed-book B0/B1 -> scoring -> review sheets -> blind reviews -> decisions. Version 2 is not changed between now and the run.
