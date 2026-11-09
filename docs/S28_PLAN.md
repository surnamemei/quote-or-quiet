# S28: a small trained checker for "does this span answer this question" (plan written before any training, 2026-11-09)

Gap. After agreement, the span gate (type check, verbatim in a pinned page) and a veto, the residual errors are of two kinds (docs/S27_RESOLUTION_ANALYSIS.md): ambiguous questions (about a third; a question-resolution state would handle them)
and relation-mapping errors (about 28% of the kept Mintaka errors, 0.8% of releases): the span is verbatim and has the right type but answers a different relation or part of it ("1678" for "between what years", "Senate" for the
Japanese chamber's name, "9" for a film count). The gate does not check the relation; a larger veto (S25) and a second page (S26) did not catch them; a conditional-truth judge (L3 fork) failed on hand-false items.
Idea. Train a small model on exactly this decision: input (question, the sentence containing the span, the span), output: does the sentence state the answer to this question with this span. It is a post-processor on the output, as proposed.

Training data (no gold from any test set):
- real text: the SimpleQA design pool (S18 sets, dev, fresh; 2,500 questions, retrieved pages already stored): positives are gold spans inside their sentences; hard negatives are other typed spans (other years, other names, other numbers) from the same sentence or page;
- synthetic: closed-evidence worlds from results/runs/s24/gen_closed.py with new seeds, negatives built the same way (another date or person in the same document), plus unanswerable questions.
Model: LoRA on Qwen3-4B-Instruct-2507, or a small encoder if that is too heavy; GPU, one job under the lock.
Evaluation (design data, post hoc): the combination-system releases of Mintaka test (63 graded wrong, 8 of them clear relation errors, 942 correct), FRESH-5 pinned additions (10 wrong, 149 correct) and the DEV added releases (18 wrong, 122 correct), scored by the checker.
Decision rule (fixed now): the checker is useful if at a threshold that keeps at least 95% of the correct releases it flags at least 50% of the wrong releases pooled over these three sets and at least 5 of the 8 clear relation errors. The 27B veto flagged 2 of 18 added wrong
releases (S25); that is the bar to beat. If not met, the learned-checker line stops. Any further step needs sealed questions.
