# S26: corroboration across distinct pages for the added releases (plan written before running, 2026-11-09)

Correction to docs/NEW_DIRECTIONS_2026-11-09.md: direction 3 (hidden-state probes as the ranking score) was already tested in this project (S5, S7, S7b in docs/REPORT.md): on TriviaQA the 4B probe
(AUROC 0.821) tied with free mean log-probability (0.828); as an answer gate it lowered SER but cost 8 to 13 points of correct answers; at equal coverage it ranked no better than the prompt's own abstention.
I listed it as untested; it is not. It stays low priority; the untested part is only the pairing with the deductive gate and a certified bound.

Direction 7. Hypothesis: an added release (pinned page or title-retrieved page) is more reliable when its answer string also occurs verbatim on a second retrieved page that is not the release page and does not
share its title core; a single page read twice is not corroboration. Data: the 997 pre-veto candidates of S25 (s19, pin, indep on mintaka_dev, popqa_dev, dev), the Phi-4 veto policy, combination rule as in S23 and S25.
Quantities: among releases added beyond the frozen S19 system, wrong and correct counts split by corroborated or not.
Decision rule (fixed now): corroboration is useful if, pooled over pin and indep, the corroborated added releases number at least 40 and at most 3% of them are wrong, while the uncorroborated added releases carry at least half of
the wrong ones. If not, the line stops. Design data only; any further step needs sealed questions.
