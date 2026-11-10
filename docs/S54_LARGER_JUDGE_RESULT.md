# S54: a 27B prompted judge as a comparison for the 4B prompt judge and the small trained judge (22:55; results/runs/s54/J27_result.md)

Purpose: a reviewer will ask whether a stronger off-the-shelf judge does the job without any training. Qwen3.8-27B (local, Ollama) was given the same YES/NO prompt as rule R (no swap control) on the S51 held-out rows (939) and on the 361 non-decoy
Mintaka review rows of S52. It was not chosen after seeing results; no prediction was written (this was a comparison added after the audit), so there is nothing to mark as met or failed.

| Set | Judge | accepted | not 'states' (held-out) or misleading (Mintaka) among accepted |
|---|---|---|---|
| held-out (n=939) | 27B prompt | 716 (76.3%) | 8 (1.1%, 97.5% upper 2.2%) |
| held-out (n=939) | 4B prompt | 804 (85.6%) | 71 (8.8%, upper 11.0%) |
| held-out (n=939) | small trained judge (0.6B), 0.5 | 744 (79.2%) | 19 (2.6%, upper 4.0%) |
| Mintaka rows (n=361) | 27B prompt | 162 (44.9%) | 3 (1.9%, upper 5.3%) |
| Mintaka rows (n=361) | small trained judge, 0.5 | 154 (42.7%) | 8 (5.2%, upper 10.0%) |
| Mintaka rows (n=361) | 4B prompt (rule R) | 192 of 300 releases | 46 (24.0%, upper 30.6%) |

Reading: the failure of rule R on Mintaka is mainly a failure of the 4B prompt judge: the same prompt on a 27B model leaves 1.9% misleading on those rows. The small trained judge is between the two and about 45 times
cheaper per row than the 27B (a 0.6B classifier against a 27B generator; the 27B run took 276 s for 1,300 rows on this machine, so the cost is not prohibitive). The programme's constraint of 4B readers
is a choice, not a necessity of the check; with a 27B judge the quote requirement holds on the natural-question set at 45% acceptance. The labels are from language-model reviewers, the 27B belongs to the same model
family (Qwen) as the 4B and the 0.6B but not to the family of the reviewers; the Mintaka rows were selected by the earlier rules. The 27B judge is not used in any earlier result or in the tool.
