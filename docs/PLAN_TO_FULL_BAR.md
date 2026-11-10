# Plan to a full bar (2026-11-11)

Objective: for the question types in scope, a person who re-checks a released statement against its quote is not misled: no statement without support (nonsense) and no statement credited to a source or party that does not say it (calling a deer a horse). Measured by the tracker in docs/PROGRESS_TRACKER.md (16 gates, 48 criteria; bar = criteria met / 48; run `python -B results/progress.py`). The bar is full at 48 of 48. Now 15 of 48 (31%).

What a full bar means: for each gate's population, the 97.5% upper bound of the misleading or wrong share is at or below the gate's threshold, on registered, unseen data, checked by people as well as by language models, and the same holds when the system is put on the drafts of at least three other models. What it does not mean: that released statements are true (the page can be wrong), that every question is answered (the system stays silent when it has no quote), that other languages or sources outside the tested kinds are covered, or that the base model is changed. 'Applied to existing models' means the checker is placed after any model and releases only the statements it can quote.

Standard procedure for every gate (no deviations): (1) write the registration with predictions in docs/ before any output; (2) draw or seal the sample, with the minimum size in the tracker; (3) run once with frozen rules; (4) two blind reviewers see only the quote, plus 30 decoys (valid when at least 27 of 30 are caught); (5) report counts and the 97.5% Clopper-Pearson bound; (6) a failed prediction is written as failed; a rule changed after a failure counts as a new design and needs a new unseen sample; (7) update results/progress.json and run the script. Sample sizes: a bound of 3% with no error needs about 125 reviewed items, with one error about 190; the minimums in the tracker (250) leave room for two or three errors.

## Order of work
Stage 1 (G3, G4, G5, G6; 12 criteria; compute only):
- G3: freeze rule R27 (27B judge) and run it once on a fresh natural-question set (new draw from Mintaka and PopQA releases, 300 reviewed). Pass if at most 3 misleading in 300 reviewed or the bound is otherwise at most 3%.
- G4: the coverage floor is the hard part. Options registered in advance: the Qualified state (answer plus quote when the sources disagree) counted as coverage, and a larger page pool. If coverage stays under 35% the gate is reported as not reachable for natural questions and the objective is restricted to templated questions plus quote-backed statements.
- G5: rerun the per-reading rule on 250 new readings (new ambiguous names), registered.
- G6: freeze the revised chain rule with the 27B judge, run on 150 fresh two-hop items.
Stage 2 (G8 to G11; 12 criteria; compute plus reviewers):
- G8: draw 50 organisation, event and science pages, grounded drafts, rule W4 unchanged, 300 reviewed claims.
- G9, G10: rule A2 (the swap control) as frozen rule; stronger decoys (named party swapped for a closely related party, reversed stance written by hand-made templates); 250 reviewed kept statements by reviewers who see the page context of each party.
- G11: rule R27 on web pages that are not Wikipedia, 250 reviewed.
Stage 3 (G12, G13; 6 criteria):
- G12 needs two people (not language models) and 180 rows; the sheet exists. Nothing replaces this.
- G13: HHEM (needs permission to download) and AlignScore (needs the authors' package and a pickle checkpoint; only with permission and in isolation); compare at equal acceptance on the held-out rows.
Stage 4 (G14 to G16; 9 criteria):
- G14: drafts from at least three other models (for example two open models of other families and one API model), sealed run of 250 releases each; the answer-error bound and the quote bound per model.
- G15: 1,000 mixed queries through tool/qoq_service.py; no release without a quote that was checked as present; report latency.
- G16: someone else runs the release repository.

## Risks to say now
G4 may not be reachable; G12 and G16 depend on other people; G14 needs a decision about which API models may be used (cost and data). If any gate is shown unreachable, the bar cannot be filled and the claim is restricted to the gates that pass; that restriction is the result, not a failure to report.
