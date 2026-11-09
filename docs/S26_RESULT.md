# S26 result: corroboration across distinct pages (2026-11-09; design data; rule in docs/S26_PLAN.md fixed before running)
Added releases beyond the frozen S19 system, pooled over pin and indep on mintaka_dev, popqa_dev, dev (Phi-4 veto policy), split by whether the answer string also occurs verbatim on a second retrieved page with a different title core:
| | wrong | correct | wrong rate |
|---|---|---|---|
| corroborated | 6 | 42 | 12.5% |
| not corroborated | 12 | 80 | 13.0% |
Per set and variant: results/runs/s25/corroborate.md. Rule (at least 40 corroborated releases, at most 3% wrong, uncorroborated carry at least half the wrong): not met; the line stops.
Reading. Corroboration does not separate the added errors: they are as likely to be echoed by a second page as the correct answers. Together with S23 (independent retrieval) and S25 (larger veto),
every evidence-side filter tried on the added releases left the error rate between 6% and 21%; the added errors survive agreement of all readers, a larger veto and a second page, so they are not evidence failures.
