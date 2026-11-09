# S14 protocol: web corroboration for every answer, and the equal-budget baseline (Qwen3-4B)

Written 2026-11-06 about 06:55, after S13's results and before any S14 output.

## Why (from results/S13_web_search_on_abstain.md)
- **SER is the one remaining gap.** S13 met the coverage and correct targets on FRESH (84% / 78%) but SER was 6.0% against the 5.0% target.
- **Where the errors come from:** 4.0 points are round-0 (Wikipedia) answers, which S13 never checks.
- **Coverage to spare:** there is now plenty of coverage to trade for lower SER.
- **Fair comparison:** L1 asks for equal budget, so a baseline that also gets the web is needed.

## Design (vkg/s14_run.py)
- **Scope:** all 500 FRESH+DEV items (not only abstentions).
- **Web passage:** built exactly as in S13: the question plus the 4B's first two queries, DuckDuckGo, up to 8 pages, the contamination guard, then 1500 words of BM25+dense fusion. For S13's 198 abstentions this reuses S13's cache.
- **Generations:** the cautious prompt and the plain prompt, both run on the web passage.
- **If DuckDuckGo shows its bot check,** the run waits 30 min and retries; the check is never solved or bypassed.

## Systems (vkg/s14_eval.py; no gold used)
| system | rule |
|---|---|
| web_plain | the plain prompt on the web passage for every item. This is the **equal-budget baseline**. |
| **S14 strict (primary, chosen now)** | A round-0 answer is kept only if the cautious or the plain web answer agrees with it (the `agree` rule from S12); otherwise abstain. If round 0 abstained, apply the S13 rule: the web cautious answer, if the web plain answer agrees. |
| S14 lenient (secondary) | A round-0 answer is dropped only if the web cautious answer is a *different* answer. |
| S14 strict + format guard (secondary) | Also abstain when the question asks for a full date (or month and year) and the answer lacks those parts. This uses the question and answer only. |

Grading is by grader 6.1, with non-answers detected by code.

## Hashes (SHA-256)
- vkg/s14_run.py dadae134b8d10672d5651c0e145d6e30302ad3e5ae63403837199504999837b3
- vkg/s14_wait.py db8a3ea133355160022c7588ef1de57d0519a93bc4cc02bb9a4ad19b1d147285
- vkg/s14_eval.py 0372e36505cb367fe7dc059f660f1add7dae4293e600c8239d87f953100caf39
- vkg/websearch.py 397e84e4fc19094e0835fa8e0df9729c66dd34dd614e9f2caee0789bfcebac67 (10 s pace)
- vkg/grade6.py b74faad218132b83c986bcb52e70044ea995dc9de4863a990b948acad023638e (6.1)

## Predictions
| | prediction | my prior |
|---|---|---|
| X1 (L1-A, FRESH, against the pre-registered plain-4B baseline) | S14 strict: coverage ≥ 71%, correct ≥ 61%, SER ≤ 5.0% | about 60% |
| X2 (pooled) | S14 strict SER ≤ 4.0% (no worse than cautious) **and** correct ≥ cautious + 10 points | |
| X3 (L1-B, FRESH, equal budget against web_plain) | S14 strict SER ≤ 0.5 × web_plain SER **and** correct not lower than web_plain's | about 15% |
| X4 (descriptive) | the format guard lowers SER and costs at most 0.5 points of correct (pooled) | |
| X5 | dropped contaminated pages ≤ 5% of fetched pages with text | |

For X3, coverage is reported, because "equal coverage" will not hold exactly.

## Decision rule
- **X1 holds:** S14 strict goes to the final FRESH-2 confirmation (300 untouched items; web search needed there too). The confirmation will be pre-registered separately, with both baselines, before any FRESH-2 output is read.
- **X1 fails:** no confirmation run. I write up where the gap is.
- **X3:** reported either way. If it fails, any L1 claim must say the baseline lacked web access.
