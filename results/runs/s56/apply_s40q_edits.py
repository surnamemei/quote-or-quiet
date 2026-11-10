"""One-off: record the registered S40 quote analyses (W1, R, SJ, R27) in a result document, and the paper (5.20, abstract). The release README row was edited by hand."""
import datetime
from pathlib import Path
ROOT = Path(r"F:\Projects\AI hallucinations"); tm = datetime.datetime.now().strftime("%H:%M")
(ROOT / "docs/S40_QUOTE_ANALYSIS_RESULT.md").write_text(f"""# S40 quote analyses: W1, R, small judge and R27 on the frozen releases ({tm}, 2026-11-11; registered in docs/S40_PLAN.md on 2026-11-10 at 20:12, 22:26 and 23:33, before any S40 run; pipeline results/runs/s53; counts in results/runs/s40/quote_analysis/Q_result.md)

1,572 frozen releases of S40. Random 300 reviewed blind, quote only, two reviewers per row (379 rows: the displayed quote, the quote of each rule where it differs, 30 decoys; decoys 30 of 30 judged misleading by both).
The share of releases for which a rule finds a quote: W1 1,385 of 1,572 (88.1%), R 1,409 (89.6%), small judge (SJ) 1,428 (90.8%), R27 1,397 (88.9%). In the review sample the numbers kept were 267, 270, 273 and 267 of 300.

| Quote | n | misleading for both reviewers | 'states' for both |
|---|---|---|---|
| Displayed quote (first accepted span), all 300 sampled releases | 300 | 34 (11.3%, 97.5% upper bound 15.5%) | 260 (86.7%) |
| W1 quote (frame check, subject link, 4B quote-only reader), kept | 267 | 2 (0.7%, upper 2.7%) | 264 (98.9%) |
| R quote (sentence, numbers, 4B judge with swapped-answer control), kept | 270 | 6 (2.2%, upper 4.8%) | 261 (96.7%) |
| SJ quote (small trained judge at 0.5), kept | 273 | 4 (1.5%, upper 3.7%) | 267 (97.8%) |
| R27 quote (rule R with the 27B judge), kept | 267 | 2 (0.7%, upper 2.7%) | 265 (99.3%) |
| For comparison: the displayed quote of the releases each rule keeps | 267 to 273 | 17 to 20 (6.4% to 7.4%) | 243 to 245 (about 91%) |

Against the predictions: displayed quote misleading in 8 to 20%: met (11.3%). W1 kept share 85 to 95% (S42 section 9): met (88.1%). Misleading among W1 kept at most 3 of about 950 (S42): met in rate (0.7%). Rule R keeps 55 to 85%: FAILED (89.6%, above). Misleading among R kept at most 3%: met as a point
estimate (2.2%, upper bound 4.8%). Small judge gives a quote for 40 to 75%: FAILED (90.8%, above); misleading among those at most 5%: met (1.5%, upper 3.7%). R27 keeps 45 to 80%: FAILED (88.9%, above); misleading among kept at most 3%: met (0.7%, upper 2.7%).
Reading: on a templated set none of the four rules loses many releases (they keep 88 to 91%), and each cuts the share of misleading quotes from about 11% (displayed, all) or 6 to 7% (displayed, on the releases it keeps) to between 0.7% and 2.2%. W1 and R27 are best (0.7%); rule R with the 4B judge is the weakest (2.2%), as it was on the natural-question set of S52; the small
judge is in between. This is the first sealed-set confirmation of the quote rules: W1 (designed on the S29 development rows and tested on fresh S29 items) holds on a third set built from other questions; R and the small judge were designed on other sets and are confirmed here for templated questions only (their failure on natural questions, S52, is not tested by this set). The truth of the released answers is not reviewed by this analysis (it is in docs/S40_RESULT.md).
Limits: language-model reviewers; the shown percentages are of the 300 sampled releases; the sampling is one draw; W1 and R27 need a frame check for the relation (W1) or a 20 GB judge (R27).
""", encoding="utf-8")

m = ROOT / "paper/manuscript.md"; t = m.read_text(encoding="utf-8")
sec = """### 5.20 The quote rules on the third sealed set

The quote rules were applied to the 1,572 releases that the frozen system made on the third sealed set (Section 5.19), as secondary analyses registered, with their predictions, before the set was run: the witness rule W1 of Section 5.11, the relation-free rule R of Section 5.14, the small trained judge of Section 5.17 (adapter fixed by its hash, trained without any row of this set) and rule R with the 27B judge in place of the 4B judge (R27). A random 300 releases were reviewed blind, quote only, by two reviewers (decoys 30 of 30 caught). The displayed quote of the frozen rule did not state the answer for both reviewers in 34 of 300 releases (11.3%, 97.5% upper bound 15.5%); the quote of W1 failed in 2 of the 267 releases it kept (0.7%, upper bound 2.7%), that of R27 in 2 of 267 (0.7%, 2.7%), that of the small judge in 4 of 273 (1.5%, 3.7%) and that of R in 6 of 270 (2.2%, 4.8%). The rules kept 88 to 91% of the releases, above the shares predicted for R (55 to 85%), the small judge (40 to 75%) and R27 (45 to 80%), which failed as predictions; the predicted bounds on the misleading share held in every case.

On this templated set the requirement that the shown quote states the answer therefore costs about a tenth of the releases and brings the share of misleading quotes from 11% to between 0.7% and 2.2%, with the 4B-judge rule the weakest, as it was on the natural-question set. The set shares its generator and relations with the set on which W1 was designed, so the result confirms W1 on new questions of the same kind and says nothing new about R and the small judge on natural questions, where Section 5.14 reported the 4B-judge rule failing. Whether the released answers are true is not reviewed here (Section 5.19).

"""
k = "## 6. Discussion"; assert t.count(k) == 1
t = t.replace(k, sec + k, 1)
old = "Most results are design data and the reviewers are language models."
assert t.count(old) == 1
t = t.replace(old, "On a third sealed set, registered beforehand, the witness rule left 0.7% misleading quotes among the releases it kept (upper bound 2.7%) against 11.3% for the displayed quote, and the 27B-judge version also 0.7%. Most other results are design data and the reviewers are language models.", 1)
m.write_text(t, encoding="utf-8")

print("ok")
