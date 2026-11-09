# How we quantify the result: definitions and current scorecard (2026-11-09)

## Quantities (every result reports the first four; adjudicated and gold-relative versions are both given)
| quantity | definition | role |
|---|---|---|
| SER | wrong definite answers / all questions; one-sided 97.5% Clopper-Pearson upper bound after the false-credit correction E = ceil(k / (1 - 0.0082)) | safety, the L2 target (< 1%) |
| coverage | definite answers (Verified, Derived, Qualified) / all questions | usefulness; L2 needs >= 35% |
| yield | correct definite answers / all questions (and / answerable questions where that is defined) | whether abstention is bought with lost answers (target.txt: yield must not fall) |
| selective risk | wrong definite answers / definite answers, with the same bound | comparison with the calibrated-cascade literature; SER = coverage x selective risk |
| errors at matched coverage | errors of the system and of a baseline cut to the same coverage; ratio and exact binomial test | L1 (<= 0.5 with yield not lower) |
| error budget | errors split into answer judged wrong, gold wrong or stale, ambiguous question, undecided (blind adjudication, strict two-adjudicator rule) | separates system from benchmark |
| guarantee scope | share of definite answers that carry a machine-checked certificate (span V1 to V5, entity slot, derivation), and the failure rate of each assumption (source, mapping, gold, time) | L3 |
| cost | tokens and wall-clock per question; searches per question | deployability |
| prediction record | share of pre-declared predictions that held | whether our own priors are calibrated |
Progress rule: a change counts only if, on sealed questions and with intervals, it moves a point on the risk-coverage plane to lower SER at equal or higher coverage (or higher coverage at equal SER).

## Current values
| | FRESH-5 (SimpleQA) | Mintaka | PopQA | closed A | closed B |
|---|---|---|---|---|---|
| n | 1,526 | 2,000 | 2,100 | 1,500 | 1,500 |
| coverage | 37.2% | 31.0% | 19.1% | 54.2% | 56.9% |
| SER (observed) | 0.26% | 1.40% (adjudicated 0.45%) | 0.81% | 0% | 0% |
| SER upper bound | 0.76% | 2.08% (adjudicated 0.92%) | 1.35% | 0.25% | 0.25% |
| yield (correct / all) | 37.0% | 29.6% | 18.3% | 54.2% | 56.9% |
| yield on answerable | not defined | not defined | not defined | 64.5% (813 of 1,260) | 67.8% (854 of 1,260) |
| selective risk, upper bound | 0.70%, 2.04% | 4.52%, 6.65% (adjudicated 1.45%, 2.95%) | 4.24%, 7.00% | 0% | 0% |
| errors at matched coverage, system vs agreement baseline | 4 vs 9 (p = 0.13) | 28 vs 26 | 17 vs 19 | n/a | n/a |
| L2 (upper < 1%, coverage >= 35%) | met | not met (coverage) | not met | met | met |
Compute on FRESH-5 for the frozen system: about 16.4k prompt tokens and 94 generated tokens per question across the six 4B reads, plus one Phi-4 call and one web search; wall-clock latency has not been measured.
Prediction record: closed-evidence sets 12 of 13 held (A 6 of 6, B 6 of 7).

## Status against the three levels
- L1 (SER at least halved at matched coverage, yield not lower): not established (FRESH-5 point estimate 0.44, not significant; ratios 1.08 and 0.89 elsewhere).
- L2: one real benchmark met (FRESH-5), two synthetic sets met; Mintaka and PopQA not met on coverage.
- L3: every definite answer carries a span certificate by construction; the assumption failure rates are the error budget (system-attributable error 0.44% of releases, benchmark-specific 0.4% to 3%); known open assumptions: source truth, relation, time, mention extraction.
Not yet measured: latency, searches per question in wall-clock terms, human-adjudicated subset, a second real L2 benchmark.
