# Audit of paper/manuscript.md (Abstract, Sections 5.10 to 5.17, Discussion "Scope", Conclusion), 2026-11-10

Read-only audit against docs/S42, S43, S41_RESULT, S48 to S51 and the aggregate result files named in the request. Only discrepancies are listed. Severity: H = a number or claim that is wrong or contradicts another place; M = a failed or unconfirmed prediction left out, or a figure attributed to the wrong rule; L = wording, scope or traceability.

## A. Discrepancies between manuscript and sources

| # | Sev | Manuscript place and text | Source and value |
|---|---|---|---|
| 1 | H | 5.14: "the 601 releases that the frozen system made on FRESH-5" (5.15 reuses the same releases). Same section: "Applied to the 37.2% coverage on FRESH-5". | Section 5.1 of the manuscript: the frozen system released 568 answers on FRESH-5 (37.2%). docs/S22_DEV_FINDINGS.md line 180 and results/runs/s22/combo_fresh5.md: 601 is the "S19 part" of the later combination rule with the format gate (727 releases in all), not the frozen system's 568. docs/S48 itself calls the 601 "releases of the frozen system", so the error originates there. Two populations are mixed; 601/1,526 is 39.4%, not 37.2%. |
| 2 | H | Abstract: "biographies written by a 4B model". 5.10: "4B-written biographies". 5.12: "a closed-book 4B biography". | 5.12 itself, and docs/S37_DECOMPOSITION_PILOT_RESULT.md: closed-book biographies written by Phi-4, which the manuscript treats elsewhere (Section 3 Veto) as a different model from the 4B reader. (docs/S41_RESULT.md and S43 say "4B draft", so the sources disagree with each other.) |
| 3 | M/(b) | 5.10 "Any generator": "passing claims from three generators", but results are given for two. | S42 section 6 E2 row (c), reader answers that disagree with the release: 1 of 21 kept (4.76%), prediction at most 2%, FAILED (on n = 21). Not reported in 5.10. |
| 4 | M | 5.11: "On the 600 development rows W1 left no misleading quote among 492 passing rows". | S42 section 9: 492 rows is the first-span result of F and S and G (0 misleading, upper 0.75%). W1 with later spans keeps a witness for 559 of 600 (93.2%); no misleading count is given for those 559. |
| 5 | M/(b) | 5.10 "Questions built to mislead": the sample "cannot say whether it is above or below 1%"; the second E4 prediction is not mentioned. | S42 E4: "Most wrong releases repeat the original relation's answer" was a prediction; observed 1 of 2, "Not confirmed". Omitted. |
| 6 | L | 5.10 "Questions built to mislead": "We changed the relation of 741 released questions of the second set". | S42 E4 details: 641 sibling questions come from S29 releases; the other 100 (year questions) were "sampled from all S29 questions with a year", not from releases. |
| 7 | L | 5.10 "Any generator": "a true but coarser place than the reference, a country where the gold is a city". | S42 E2: the seven include "Ohio", a state, not a country. |
| 8 | L | 5.11: "By relation the rate was highest for death year (22 of 61), birth place (21 of 168) and author (14 of 96)." | S42 E6: rates are death year 36.1%, author 14.6%, birth place 12.5%; capital 3/8 (37.5%) and office 2/2 (100%) are higher than the last two. The list is ordered by count, not rate, and author outranks birth place by rate. |
| 9 | M/(b) | 5.11 reports 12.5% misleading for Verified, 55 of 100 for Qualified and F's effect without saying these missed their registered ranges. | S42 E6: prediction (a) 1 to 6% FAILED (12.5%); (c) Qualified 5 to 20% FAILED (55%); (d) F leaving at most 1.5% FAILED (4.9%). The manuscript names only the (e) and (f) failures. |
| 10 | M/(b) | Abstract, 5.11 summary and Conclusion: "made the shown quote misleading in 0.2% of fresh releases" (Conclusion gives neither bound nor cost). | S42 section 9 prediction (k), later-span witnesses not worse than first-span, FAILED (2 of 134 against 0 of 883). 5.11 states it; Abstract and Conclusion omit it and the 7% release cost (Conclusion). |
| 11 | L | 5.12: W2 "(12.1% kept, 4.4% false and 3.3% misleading in a blind sample)". | S43 part A: all 181 kept slots were reviewed (plus 40 dropped, 30 decoys); not a sample of the kept slots. |
| 12 | L/(a) | 5.12 limits: "in the first review they looked up only a minority of the claims". | No support in any listed source. S43/S45/S47 say reviewers had web search (plan) and that the recheck forced a lookup with a source URL; no share is given. |
| 13 | M/(b) | 5.13: predictions are not mentioned. | docs/S43 note on part B: person readings of the first run were scored before the predictions were written ("predictions for persons are informed by that run"); the coverage prediction (readings with a witness 60 to 85%) was EXCEEDED at 89.3%. Neither is stated. |
| 14 | L | 5.13: "The first run of the films gave no answer at all". | S43 note: the first run "produced no witness for any film reading"; the reader step had answered 273 of 280 readings. |
| 15 | L/(b) | 5.14: reports only the quote verdict. | docs/S48: the planned truth verdict (prediction: false among kept at most 3%) was not collected; also "frozen display misleading 8 to 20%" and "R keeps 65 to 90%" were met only at the edges (20.0%, 65.0%). Neither is stated. |
| 16 | L/(b) | 5.15: only the failed prediction "at most 3% misleading and at least 88% states" is given. | docs/S49 also: naive display misleading 25 to 50% not met (19.7%); R keeps 30 to 60% exceeded (71.0%). Not stated. |
| 17 | L | 5.16: "the country was wrong for neither reviewer in any of the 55 (upper bound 6.5%)". | docs/S50: "answer false (both) 0 of 55, upper 6.5%". Only the both-reviewer count exists; "neither reviewer" is stronger than the source. |
| 18 | L | 5.17: "Over the experiments of Sections 5.10 to 5.15 ... labelled 4,714 rows". | docs/S51: sources are e6, e7 (5.11), s43, e11, w4, r4, f5 (5.12), e9 (5.13), s48 (5.14), web (5.15). Nothing from 5.10 (E4, S41). Should read 5.11 to 5.15. |
| 19 | L | 5.17: "2.6% of the accepted rows were not 'states' by both reviewers". | results/runs/s51/D_result.md: target is 'states' for both reviewers; the 2.6% are rows that are not 'states' for both, not rows both reviewers called not 'states'. Wording inverts the label. |
| 20 | L | 5.10 "Third state": the 43 of 91 head-of-government quotes were "typically a list line naming the current office holder". | S42 E3 gives only 43 of 91 (47.3%). The list/index-line character comes from the E6 Verified listing, where the named holders are often not current (Maldives 1989, Liechtenstein 1926). Weakly supported. |

## B. Internal inconsistencies between manuscript parts

| # | Sev | Places | Inconsistency |
|---|---|---|---|
| 21 | M | Abstract: "the same check kept 20% of the claims of closed-book drafts" versus 5.12 | The check in 5.12 is rule W4 (sentence judge, swap control, number check, 75% value coverage), not the frame check, subject link and reader of W1 described just before in the Abstract. "Same check" overstates identity. |
| 22 | L | Header comment (lines 3 to 5): "DRAFT v0.3 ... adds Sections 5.10 and 5.11" | Manuscript now contains 5.12 to 5.17, whose numbers trace to S43 to S51 and results/runs/s43 to s51; the header lists only S42/S41, and says 12 added references were checked (not re-verified here). |
| 23 | L | Section 6 "Implications" and Section 7 ("an output state that names what an answer assumes") versus 5.10 | 5.10 reports the Qualified state implemented and measured on real data (81.0% quote holds gold; 47.5% wrong on long-form). The Discussion still writes the state as an untested proposal and does not cite 5.10. |
| 24 | L | 5.10 long-form paragraph | Omits that rule Q on long-form was also predicted to add 3 to 12 points and added 24.1% (360 slots), FAILED (S41_RESULT); only the 47.5% wrong figure is given. |

## C. Source-side notes (not manuscript errors, affect traceability)

- S42 section 8 says 11,148 spans for 2,149 items "5.6 per Verified item"; 11,148/2,149 = 5.19, and 11,148/1,765 = 6.3. 5.11 repeats 5.6.
- results/runs/s44/W4_result.md prints "317 of 1,492 (21.2%)" and s43/E11_result.md "300 of 1,492 (20.1%)": stale denominators from the auto-template. The manuscript uses 1,547 and 20.5% (correct per S43 doc) and 478 of 1,492 (32.0%).
- docs/S41_RESULT.md and S44 text say "4B draft" where S37 says Phi-4 (see finding 2).

## D. Checked and correct (not listed above)

All counts and percentages of Tables 8, 9, 10, the E2 numbers (0 of 3,359, 13 of 954, 12 not cleared), E3 (384, 311, 43 of 91, 268 of 293), E4 (134, 741, 79.4%, 2 of 134, 5.3%, 36 of 132), E6/E7 figures, S41/S43/S44/S45/S47 figures, E9 (250 of 280, 88 of 105, 0 of 250, 1.5%), S48 (195, 60, 22, 1.0%, 94.9%), S49 (213, 8, 24, 73.7%, 61.5%, 0 of 1,118), S50 (55 of 71, 13, 1.8%, 9.7%, 10 of 10) and S51 (4,714, 4,595, 0.988, 79.2%, 2.6%, 8.8%, 7.3%, 11.4%, 9.3%) match the sources, as do the Scope-paragraph and Conclusion figures for 5.11 and 5.12.

24 findings (3 high-priority: 1, 2, 3 plus 1 more medium cluster 4, 5, 9, 10, 13, 21; the rest low), plus 3 source-side notes.
