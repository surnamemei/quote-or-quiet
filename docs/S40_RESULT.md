# S40 result: the third sealed set, version 2 run once (06:09, 2026-11-11; plan docs/S40_PLAN.md; aggregates in results/runs/s40/run_fsm/w3_final.md and the scripts' printed tables)

3,040 questions from Wikidata in six relations (birth place 800, director 600, birth year 600, author 500, death year 400, head of government in a year 140; founding year was dropped before the run), sealed on 2026-11-09, run once. Pipeline: the frozen system plus the registered two-source cell
(version 2). The search pool was the free metasearch pool; the prefetch needed 4 passes because of bot-check stops (never bypassed); the Ollama port was changed to 11540 (Windows reserved the old one) and the query gap to 10 to 12 s; all dated in the plan before the run.

| Quantity | Result | Prediction | Outcome |
|---|---|---|---|
| Version 2 coverage | 1,675 of 3,040 (55.1%) | 50 to 66% | met |
| Frozen rule alone | 1,572 (51.7%) | 47 to 60% | met |
| Gain from the two-source cell | 103 releases (3.4 points) | 2 to 6 points | met |
| Gold-relative wrong among version 2 releases | 56 (3.34%) | at most 4% | met |
| L2 (primary): adjudicated errors, corrected 97.5% upper bound over all questions | 10 errors (46 of 56 removed), upper bound 0.65% at coverage 55.1% | at most 22 errors; bound below 1% | MET |
| Validity of the adjudication | decoys called 'answer wrong' by both 12 of 12; gold-matching releases called 'answer wrong' by both 0 of 24 | at least 11 of 12 | valid |
| Truth-relative errors of version 2 (gold hidden) | 1 of the reviewed (director: Patty Jenkins for 'Wonder of Women' where the gold says Clarence Brown) | at most 8 | met |
| Added releases (version 2 cell), truth review | 103 added, 1 wrong for both reviewers (1.0%, upper bound 3.7%) | registered pass rule | passed |
| L1-a (gold-relative SER lower than B0 to B3, exact McNemar, Holm) | B0 84.54%, B1 51.22%, B2 7.66%, B3 5.07% against 1.84%; all Holm-passed; truth-relative robustness passed | met | MET |
| L1-b (non-inferiority to the agreement ablation at equal coverage) | SER difference -0.004 points (upper +0.066, margin +0.25); yield difference +0.004 points (lower -0.888, margin -1) | met | MET |
| Original L1 (at least 50% fewer errors than the ablation) | 1 error against an expected 1.12 | not met | not met, as predicted |
| Rule Q (Qualified state) | 347 questions (11.4 points) | 4 to 10 points | FAILED (slightly over) |
| Rule Q: quoted answer matches the gold | 275 of 347 (79.3%) | 78 to 92% | met |

Reading: on a third sealed set built by the same generator as the second, the registered L2 criterion holds with a bound of 0.65% at 55% coverage, and the revised L1 holds. The set shares its generator, relations and evidence source with the second sealed set (S29), so it replicates the result on new
questions of the same kind and not on a new kind of question. Head-of-government questions are nearly all withheld (2 of 140 released).
Incidents and limits: (1) while checking the item file format for a secondary analysis, three item lines with their gold answers were printed to the console; disclosed in the plan before any run output was read; nothing used them. (2) Ten language-model reviewers did the L2, L1 and version-2 sheets; their web search budgets ran out
partway (most verdicts rest on Wikipedia pages fetched directly) and some shared a scratch folder, so two of them ran another reviewer's build script by mistake; every verdict file was checked afterwards for the right number of rows, matching questions and no blank verdicts, and the version-2 file of one reviewer was checked
against that reviewer's own report. (3) The reviewers are language models; the quote check that applies to every removing verdict is mechanical (the quote must occur in the page): 73 of 77 and 71 of 77 quotes were found for the two L2 reviewers and the rest reverted to 'cannot tell'.
