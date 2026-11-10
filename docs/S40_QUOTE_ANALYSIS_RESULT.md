# S40 quote analyses: W1, R, small judge and R27 on the frozen releases (09:15, 2026-11-11; registered in docs/S40_PLAN.md on 2026-11-10 at 20:12, 22:26 and 23:33, before any S40 run; pipeline results/runs/s53; counts in results/runs/s40/quote_analysis/Q_result.md)

1,572 frozen releases of S40. Random 300 reviewed blind, quote only, two reviewers per row (379 rows: the displayed quote, the quote of each rule where it differs, 30 decoys; decoys 30 of 30 judged misleading by both).
The share of releases for which a rule finds a quote: W1 1,385 of 1,572 (88.1%), R 1,409 (89.6%), small judge (SJ) 1,428 (90.8%), R27 1,397 (88.9%). In the review sample the numbers kept were 267, 270, 273 and 267 of 300.

| Quote | n | misleading for both reviewers | 'states' for both |
|---|---|---|---|
| Displayed quote (first accepted span), all 300 sampled releases | 300 | 34 (11.3%, 97.5% upper bound 15.5%) | 260 (86.7%) |
| W1 quote (frame check, subject link, 4B quote-only reader), kept | 267 | 2 (0.7%, upper 2.7%) | 264 (98.9%) |
| R quote (sentence, numbers, 4B judge with swapped-answer control), kept | 270 | 6 (2.2%, upper 4.8%) | 261 (96.7%) |
| SJ quote (small trained judge at 0.5), kept | 273 | 4 (1.5%, upper 3.7%) | 267 (97.8%) |
| R27 quote (rule R with the 27B judge), kept | 267 | 2 (0.7%, upper 2.7%) | 265 (99.3%) |
| For comparison: the displayed quote of the releases each rule keeps | 267 to 273 | 17 to 20 (6.4% to 7.4%) | 243 to 248 (90% to 92%) |

Against the predictions: displayed quote misleading in 8 to 20%: met (11.3%). W1 kept share 85 to 95% (S42 section 9): met (88.1%). Misleading among W1 kept at most 3 of about 950 (S42): met in rate (0.7%). Rule R keeps 55 to 85%: FAILED (89.6%, above). Misleading among R kept at most 3%: met as a point
estimate (2.2%, upper bound 4.8%). Small judge gives a quote for 40 to 75%: FAILED (90.8%, above); misleading among those at most 5%: met (1.5%, upper 3.7%). R27 keeps 45 to 80%: FAILED (88.9%, above); misleading among kept at most 3%: met (0.7%, upper 2.7%).
Reading: on a templated set none of the four rules loses many releases (they keep 88 to 91%), and each cuts the share of misleading quotes from about 11% (displayed, all) or 6 to 7% (displayed, on the releases it keeps) to between 0.7% and 2.2%. W1 and R27 are best (0.7%); rule R with the 4B judge is the weakest (2.2%), as it was on the natural-question set of S52; the small
judge is in between. This is the first sealed-set confirmation of the quote rules: W1 (designed on the S29 development rows and tested on fresh S29 items) holds on a third set built from other questions; R and the small judge were designed on other sets and are confirmed here for templated questions only (their failure on natural questions, S52, is not tested by this set). The truth of the released answers is not reviewed by this analysis (it is in docs/S40_RESULT.md).
Limits: language-model reviewers; the shown percentages are of the 300 sampled releases; the sampling is one draw; W1 and R27 need a frame check for the relation (W1) or a 20 GB judge (R27).
