# S15 protocol: final pre-registered L1 confirmation on FRESH-2 (Qwen3-4B, S14 strict)

Written 2026-11-06 about 10:25, after the S14 scoring and before any FRESH-2 output.

## Data
FRESH-2 is 300 SimpleQA Verified items, drawn with Random(4000) from the 500 indices never used.
- **Item file:** results/runs/fresh2/items.json, SHA-256 80d0c9b1a8bd10f9cd6ce2ea43006675ff50e8d4c2b282a85f06f78c9f42d6ff.
- **Built before any result was seen:** the item file was built before any S12–S14 result existed.
- **Not inspected:** no question, gold or passage in it has been read by me or by any analysis. One item has an empty Wikipedia passage; only the build log's count was seen.

## Pipeline (frozen; nothing was tuned on FRESH-2)
- vkg/s15_run.py: 4B plain and cautious on the Wikipedia passage (as in S8), then the web passage and the web cautious and plain answers (as in S14).
- Decision rules: vkg/s14_eval.py, unchanged (hash 0372e365…).
- Grading: grader 6.1 (b74faad2…). Web search: vkg/websearch.py (397e84e4…).

## Primary system and baselines (fixed now)
- **Primary system:** S14 strict.
- **Secondary system:** S14 strict + format guard. It is reported, but it cannot rescue a failed primary.
- **L1-A baseline:** the 4B plain prompt on the same Wikipedia passage. This is the pre-registered L1 baseline used throughout.
- **L1-B baseline (equal budget):** the 4B plain prompt on the same web passage.

## Criteria (vkg/s15_eval.py; one-sided 95% bounds from paired bootstrap, 10,000 draws, seed 0)
L1 is **met** against a baseline only if all three hold:
- **(a)** SER is at least 50% below the baseline: the upper bound of mean(e_S14 − 0.5·e_base) is below 0;
- **(b)** yield is not lower: the point difference in correct is at least 0, and its lower bound is above −0.03 (a 3-point non-inferiority margin);
- **(c)** coverage is not more than 3 points lower than the baseline's.

## Predictions
| | prediction | my prior |
|---|---|---|
| P1 | **L1-A met** for S14 strict | about 70% |
| P2 | L1-B not met: S14 trades coverage for precision against plain + web | about 85% |
| P3 | SER of S14 strict ≤ 5.0% (point estimate) | |
| P4 (L2) | **not met**: the Clopper–Pearson 95% upper bound on SER stays above 1% (it would need 0 errors in 300) | |
| P5 | contaminated pages ≤ 5% of fetched pages with text | |

A dry run of the scorer on S14's FRESH rows (code check only) gave: L1-A met, L1-B not met.

## Hashes (SHA-256)
- vkg/s15_run.py a643e4537f888ceba324ef7ed456de7ab7bbb8b4c0893951c9b7375535b14f02
- vkg/s15_wait.py 0ed929f383843e7e4b85cb4513b4587eb9e0c742e85ce0a73ab53d51fcb724c4
- vkg/s15_eval.py ffe4481c3910635b400d2f0bb41353bc5543053e2010fc5a136cd50a7adfb369

## Reporting
Whatever the result, it is reported. If L1-A fails on FRESH-2, the FRESH result is reported as not confirmed.

Any L1 claim must state:
- the scope: SimpleQA Verified, English short facts, a 4B model, a Wikipedia retriever plus keyless web search, grader 6.1 (an LLM judge plus code vetoes, validated on 260 blind rows);
- that it does **not** hold at equal budget against a web-enabled plain baseline (if P2 holds).
