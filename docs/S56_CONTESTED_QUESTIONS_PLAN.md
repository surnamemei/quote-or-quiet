# S56: contested topics and attribution fidelity (plan, 2026-11-10 23:40, before any S56 output)

Why. For most questions there is no single answer: what is said depends on who says it. The aim for those questions is not a correct answer but two things: no nonsense (nothing stated that no source supports) and no
'calling a deer a horse' (a view attributed to a source or party that does not hold it, or with its stance reversed). That is the quote-sufficiency requirement applied to attribution: the system may report that a party holds
a view only when a quoted sentence says that this party holds that view. It does not assert the view itself.

Design. Topics: 60 English Wikipedia pages (20,000 to 120,000 characters, no qualifier, not lists) whose title contains controversy, debate, criticism of, dispute, opposition to, ethics of and similar words (742 such pages in the title index),
drawn with seed 5601. Statements: Phi-4 (Ollama, greedy, 6 to 8 statements per topic) is given the first 14,000 characters of the page and asked for the main viewpoints held by named parties, each statement naming the party ('Critics argue that ...'), without its own opinion.
Naive display: for each statement, the page sentence with the highest content-word overlap with it (what a citing system would show).
Rule A (frozen now): for each statement the three sentences of the page with the highest content-word overlap (overlap at least 3) are candidates; a candidate is the witness if Qwen3.8-27B (Ollama, temperature 0, quote-only) says YES to 'does this sentence report that this party holds this view: the same party and the same stance, not the opposite and not another party' and NO to the same
sentence with the party flipped (supporters and critics, proponents and opponents, advocates and opponents, defenders and critics, for and against, swapped; a statement with no flippable word has no control and needs only the YES). The statement is kept with its witness sentence; otherwise it is dropped.
Review: a random 300 statements; the naive display sentence and, where different, the witness; 30 decoys (the party flipped in the statement); two blind reviewers, quote only, one verdict: states (the sentence reports that this party holds this view), opposite (it reports the opposite stance or another party's view), not (it does not address it).
Misleading = both reviewers say opposite or not; reversal = both say opposite.
Predictions (before any output): naive display misleading for 20 to 45% of statements, reversed for 3 to 15%; rule A keeps 35 to 70% of the statements; among kept, misleading at most 3% and reversed at most 1%; the 27B says YES to a flipped statement for at most 10% of candidates.
Not measured: whether the viewpoints are the main ones of the topic, whether the page is balanced, whether any view is true. The statement dropped share is reported as the share of generated statements that no sentence of the page supports (a lower bound on nonsense in the draft).

## Result (23:59; results/runs/s56/E12_result.md)

60 topics, 479 statements by Phi-4; 477 had a candidate sentence; rule A kept 207 (43.2%). The first judging run was void (the 27B was called through the raw Ollama interface, returned reasoning text and no YES or NO, so every statement was dropped); it was repeated through the chat
interface with thinking off (the void output is kept as e12_judge_failed_first_run.json). The 27B said YES to 248 of 1,362 candidates and to 8 flipped statements. Blind review of 343 rows (300 statements, 13 differing witnesses, 30 decoys), two reviewers, quote only:

| Sentences | n | misleading for both (opposite or not) | reversed for both (opposite) | 'states' for both |
|---|---|---|---|---|
| Naive display (best-overlap sentence), sampled statements | 300 | 53 (17.7%, 97.5% upper 22.5%) | 1 (0.3%, upper 1.8%) | 230 (76.7%) |
| Naive display, the 135 statements rule A keeps | 135 | 5 (3.7%, upper 8.4%) | 0 (upper 2.7%) | 129 (95.6%) |
| Rule A witness, kept statements | 135 | 0 (0.0%, upper 2.7%) | 0 (upper 2.7%) | 134 (99.3%) |

Against the predictions: naive display misleading in 20 to 45%: just below (17.7%). Naive display reversed in 3 to 15%: FAILED (0.3%; reversals were rare). Rule A keeps 35 to 70%: met (43.2% of all statements). Misleading among kept at most 3%: met (0 of 135, upper bound 2.7%).
Reversed among kept at most 1%: met as a point estimate (0; upper bound 2.7%). The 27B accepting a flipped statement for at most 10% of candidates: met (8 of the candidates of 116 flippable statements).
The decoy check is INVALID: only 16 of 30 flipped-party statements were judged misleading by both reviewers (criterion 27 of 30). The flip changes a generic party word (supporters, critics, in favour of) and many sentences name a person or a body, not the generic party, so a reviewer who sees only the sentence
can accept the flipped statement as well. The reviewers' verdicts on 'opposite' are therefore not validated, and 'no reversal observed' is not evidence of no reversal; what the data show is that reversals were rare in the drafts (1 of 300 for the naive display) and that the common failure was an unsupported or vague statement.
Nonsense, as far as measured here: 272 of the 479 statements (56.8%) have no sentence of the page that the 27B accepts for them, a lower bound on the unsupported content of the draft (the 27B may reject some supported statements; no review of the rejected statements was done).


## Follow-up: reversal control by construction (2026-11-11; results/runs/s56/e12_reversal_control.py, E12b_result.md; cached 27B verdicts, no reviewers, not registered beforehand)

Usable candidates are page sentences that contain the statement's party word (supporters, critics, ...) and not its opposite, so the flipped statement is not reported by them whatever else they say: 152 candidates in 46 statements. The 27B accepted the flipped statement for 6 of 152 candidates (3.9%, 97.5% upper bound 8.4%) and for 3 of 46 statements (6.5%, upper 17.9%); it accepted the original statement for 45 of 152 (29.6%).
Rule A requires NO to the flipped statement, so those acceptances are rejected where a control exists. But only 39 of the 207 kept statements have a flippable party word and hence a control; 168 (81%) are kept on the YES alone. The sample of 135 reviewed kept statements showed no reversal, and the reviewers' 'opposite' verdict was not validated (decoys 16 of 30), so for those 168 the absence of reversals is not established.

## Follow-up 2: party-swap control for the 168 kept statements without a flippable word (plan, 2026-11-11, before any output of it)

Gap. Only 39 of the 207 kept statements have a flippable party word; the other 168 are kept on the judge's YES alone (follow-up 1). Control. For each of the 168: (1) the 27B names the party that holds the view in every statement (all 479; at most 6 words); (2) for each of the 168 a replacement party is taken, with seed 5603, from the parties of other statements of the same topic that share no content word (more than 3 letters) with the original party; (3) the 27B rewrites the statement so the same view is attributed to the replacement party and nothing else changes; (4) the rewritten statement is judged against the kept witness sentence with the same prompt as rule A. A case is usable when the witness sentence contains no content word of the replacement party (so it cannot say that party holds the view). The misattribution is wrong by construction for usable cases.
Reported: usable cases, the share the 27B accepts (YES) with the 97.5% upper bound; and, as a registered remedy (rule A2: also require NO to the party-swapped statement), the share of the 168 that rule A2 would drop.
Predictions: usable at least 100 of the 168; the 27B accepts the party-swapped statement for 3 to 12% of usable cases (upper bound at most 15%); rule A2 drops at most 15% of the 168 beyond rule A. A result above 12% is reported as a failed prediction and the remedy is then the rule.
Not measured: whether the replacement party holds some other view, whether the rewrite changes the view, reviewers (none; this is a mechanical control).

## Follow-up 2 result (2026-11-11 09:41; results/runs/s56/E12c_result.md)

Parties named for 479 statements; a replacement party existed for 163 of the 168; usable (witness sentence has no content word of the replacement party) 136. The 27B accepted the party-swapped statement for 6 of 136 (4.4%, 97.5% upper bound 9.4%). Rule A2 would drop 6 of the 168 (3.6%).
Against the predictions: usable at least 100: met (136). Acceptance 3 to 12%, upper bound at most 15%: met. Rule A2 drops at most 15%: met.
Inspection of the 6 accepted cases (after the count): in 2 the rewrite had left the statement unchanged (the 27B did not swap the party), so they are not misattributions; without them 4 of 134 (3.0%, upper bound 7.5%). Of the 4, one replaces a named MP by 'Critics', one a named board by 'The Swedish' (a truncated party name), two give the view to another group. So the judge accepts a view moved to a party the sentence does not name in about 3 to 4% of cases. Rule A2 (NO to the party-swapped statement required) is adopted for further use; it was not applied to the reviewed sample.
Limits: no reviewers; the replacement party is another party of the same topic, chosen at random, so harder swaps (a closely related party) are not tested; 6 rewrites did not contain the replacement party's name verbatim.
