# S55: distilling the 27B judge into the small judge (plan, 2026-11-10 23:18, before any S55 output)

Finding that motivates it (docs/S54_LARGER_JUDGE_RESULT.md): the 27B prompted judge is the best quote-sufficiency judge we have (1.1% not 'states' among accepted on the held-out rows, 1.9% misleading on the Mintaka rows), the
trained 0.6B judge is cheaper but weaker on the set it did not see (5.2%), and MiniCheck zero-shot is about as good as the trained judge there. Improvement tested: use the 27B as a teacher on unlabelled candidate quotes.
Silver data: candidate sentences (accepted spans of the releases) from three sets of releases: the Mintaka releases that were not in the 300-release review sample, the FRESH-5 releases, and the web-page candidates of S49;
at most fifteen sentence-form candidates per release, rows whose question occurs in the labelled table excluded, at most 4,000 rows per set. The 27B (same YES/NO prompt, no swap control) labels each row. Student: the same 0.6B model
and LoRA recipe as S51, trained on the labelled training rows of S51 plus the silver rows (YES as 'states', NO as 'not'), 3 epochs. Evaluation: the S51 held-out rows and the Mintaka review rows of S52 (no Mintaka row of the
review sample is in the silver data), against the S51 judge, MiniCheck and the 27B.
Predictions (before any output): on the Mintaka review rows the new student accepts at least 38% of the rows with at most 3% misleading among accepted, and AUROC at least 0.93; on the held-out rows AUROC stays at least 0.98 and
not 'states' among accepted at most 2.2% at an acceptance of at least 75%. If the Mintaka prediction fails, silver labels from a 27B do not close the gap and the 27B itself is the recommended judge.
Limits: the silver labels are the 27B's, not people's; the Mintaka review rows were labelled by language-model reviewers; the same 27B is the teacher and one of the comparisons, so its own numbers are not independent evidence of the student.

## Result (23:33; results/runs/s55/S55_result.md)

Silver rows: 3,368 candidate sentences (Mintaka releases outside the review sample 2,576, FRESH-5 371, web 421); the 27B said YES to 958 (28.4%). Student: 3,656 labelled training rows plus the silver rows, S51 recipe.

| Set | AUROC for 'states' | accepted at 0.5 | measure among accepted |
|---|---|---|---|
| held-out (n=939) | 0.988 | 745 (79.3%) | not 'states' 16 (2.1%, 97.5% upper 3.5%) |
| Mintaka rows (n=361) | 0.911 | 163 (45.2%) | misleading 13 (8.0%, upper 13.3%) |

Against the predictions: Mintaka acceptance at least 38%: met (45.2%). Mintaka misleading among accepted at most 3%: FAILED (8.0%). Mintaka AUROC at least 0.93: FAILED (0.911; the S51 judge had 0.897). Held-out AUROC at least 0.98: met (0.988).
Held-out not 'states' at most 2.2% at an acceptance of at least 75%: met (2.1% at 79.3%).
Reading: distilling the 27B on 3,368 silver rows raised the AUROC on the unseen set a little (0.897 to 0.911) but did not close the gap (8.0% misleading at the default threshold against 1.9% for the 27B itself). As planned, the recommendation is to use the 27B as the judge
where a GPU of about 20 GB is available, and to keep the small judge as the cheap option. No further work on the student.

