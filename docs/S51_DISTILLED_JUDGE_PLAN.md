# S51: a labelled quote-sufficiency table and a small judge (plan, 2026-11-10 21:56, before any S51 training output)

Limit to remove: the 'does the quote state the answer' decision rests on a prompted 4B model. About 4,700 two-reviewer labels exist from S42 to S49 (E6, E7, S43, E11, W4, R4, F5, E9, S48, S49 web).
Table (results/runs/s51/d_build.py): question, answer, page title, quote, two labels (states / incomplete / not); local only (it holds benchmark questions and third-party text).
Model: Qwen3-Embedding-0.6B with a classification head, LoRA r=16, 3 epochs, lr 2e-4, bf16. Target: 'states' (both reviewers) against not 'states'. Rows where the reviewers disagree are left out.
Split: by question (group hash mod 5 = 0 is the test set), fixed before training. The 4B prompt judge (the YES/NO prompt of rule R, without the swap control) is run on the same test rows.
Metrics on the test set: AUROC for 'states'; at the 4B judge's acceptance rate, the share of accepted rows that are not 'states'; the same at the small judge's threshold that matches the 4B acceptance;
and the small judge's threshold that keeps the not-'states' share among accepted at most 3%, with its acceptance rate.
Predictions (before any output): AUROC at least 0.90; at matched acceptance the small judge's not-'states' share among accepted is no higher than the 4B judge's; the small judge reaches
at most 3% not-'states' among accepted at an acceptance rate of at least 50%. If it does, it can replace the 4B prompt in the tool at a fraction of the cost; if not, the dataset is still the result.
Limits: the labels come from language-model reviewers; the rows were selected by the earlier rules (kept, frozen display, decoys), so the distribution is not that of all candidate quotes; five of the ten sources
share the Wikipedia domain; the test questions are disjoint from the training questions but not from the training templates.

## Result (22:04; results/runs/s51/D_result.md; local data only)

Table: 4,714 rows, 4,595 with agreed labels ('states' 3,635, 'incomplete' 311, 'not' 649). Training 3,656 rows, test 939 rows (153 questions groups hash mod 5 = 0 removed from training), 'states' share of the test 80.1%.
Training took 253 s on the GPU (LoRA on the 0.6B embedding model).

| Judge | AUROC | Accepted, and not 'states' among accepted |
|---|---|---|
| Small judge (0.6B), threshold 0.5 | 0.988 | 744 (79.2%), 19 not 'states' (2.6%, 97.5% upper 4.0%) |
| 4B prompt judge (YES/NO) | 0.798 (binary output) | 804 (85.6%), 71 not 'states' (8.8%, upper 11.0%) |
| Small judge at the 4B acceptance rate | | 804 (85.6%), 59 (7.3%, upper 9.4%) |
| Small judge, at most 3% not 'states' | | 756 (80.5%), 22 (2.9%, upper 4.4%) |

Checks against the easy-negative and leakage worries: restricted to rows whose answer string occurs in the quote (830 rows, 85% 'states') the AUROC is 0.988; for quotes that do not occur in the training
rows (713 rows) 0.989; for both together (648 rows) 0.987. By source the not-'states' share among accepted is highest on the web pages (4 of 35, 11.4%) and on W4 (5 of 54, 9.3%), 0 on S48, F5 and E9.
Predictions: AUROC at least 0.90: met (0.988). At matched acceptance the small judge is no worse than the 4B judge: met (7.3% against 8.8%). At most 3% not 'states' among accepted at an acceptance of at least 50%:
met (2.9% at 80.5%). Limits: labels from language-model reviewers; the rows were selected by earlier rules, so this is not the distribution of all candidate quotes; the 4B judge is the prompt of rule R without the
swap control and with a binary output, so its AUROC is not comparable to a score; the small judge was not used inside the tool or in any earlier result. The numbers of the paper's earlier sections do not depend on it.

