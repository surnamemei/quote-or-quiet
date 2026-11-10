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

## MiniCheck-Flan-T5-Large as an off-the-shelf checker (23:18; results/runs/s54/MiniCheck_result.md)

Weights lytang/MiniCheck-Flan-T5-Large (MIT, 3.1 GB, downloaded on 2026-11-10 with the user's permission into models_external/minicheck-ft5-large; only the model files were fetched, none of the repository's scripts was run; the
checkpoint is a pickled PyTorch file read with the default safe loading of the library). Inference reimplemented from the authors' published code (read, not run): 'predict: ' + document + eos + claim, one decoder step from a zero
start token, softmax over token ids 3 and 209. Document = page title and quote; claim = 'The answer to the question "Q" is A.' AlignScore was not run: its checkpoints are Lightning pickles that need the authors' package. No prediction was written.

| Set | Checker | AUROC for 'states' | accepted | measure among accepted |
|---|---|---|---|---|
| held-out (n=939) | MiniCheck, 0.5 | 0.963 | 749 (79.8%) | not 'states' 31 (4.1%, 97.5% upper 5.8%) |
| held-out | small trained judge, 0.5 | 0.988 | 744 (79.2%) | 19 (2.6%, upper 4.0%) |
| held-out | 27B prompt | | 716 (76.3%) | 8 (1.1%, upper 2.2%) |
| Mintaka rows (n=361) | MiniCheck, 0.5 | 0.890 | 190 (52.6%) | misleading 25 (13.2%, upper 18.8%) |
| Mintaka rows | MiniCheck at 154 accepted | | 154 (42.7%) | misleading 7 (4.5%, upper 9.1%) |
| Mintaka rows | small trained judge, 0.5 | 0.897 | 154 (42.7%) | misleading 8 (5.2%, upper 10.0%) |
| Mintaka rows | 27B prompt | | 162 (44.9%) | misleading 3 (1.9%, upper 5.3%) |

Reading: an untrained 770M checker is close to our trained 0.6B judge on the set neither saw (AUROC 0.890 against 0.897; at equal acceptance 4.5% against 5.2% misleading) and somewhat behind it on the in-domain held-out rows (0.963 against 0.988),
which is where training on the reviewers' labels helps. The trained judge is therefore not a large advance over an existing checker; its contribution is the labelled rows. The 27B prompted judge is the best of all.

