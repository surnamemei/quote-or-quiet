# S17 protocol: three-source agreement, confirmation on FRESH-3 (Qwen3-4B)

## Why S17
S15 (FRESH-2, n = 300) did not confirm L1-A. I put the chance of P1 passing at 70% in advance, but I never computed the power. A power analysis after the fact, by bootstrap from the 500 pooled FRESH + FRESH-2 rows, shows how underpowered it was. Criterion (a) needs the one-sided 95% upper bound of mean(e − 0.5·e_base) to be below 0.

| system vs plain (pooled SER) | n=300 | n=500 | n=800 | n=1000 |
|---|---|---|---|---|
| S14 strict (3.6% vs 9.6%) | 0.29 | 0.42 | 0.57 | 0.61 |
| S14 strict + format guard (2.6% vs 9.6%) | 0.65 | 0.84 | 0.95 | 0.98 |

These numbers use FRESH-2 data, so they serve only to size the next test, never as evidence for L1. Lesson recorded: every confirmation from now on states its power before it runs.

## Data (frozen now, before any S17 system exists)
- **FRESH-3:** 1000 items, built by vkg/fresh3.py.
  - **Stratum V (200):** the SimpleQA Verified items never used. They are outside the Random(3000) 500-draw that covers DEV, FRESH and the freezes, and outside FRESH-2's Random(4000) 300.
  - **Stratum O (800):** Random(5000).sample from the original SimpleQA test set, excluding every item that is in SimpleQA Verified (matched by original_index). That leaves 3326 candidates.
- **Source:** the official CSV (openaipublic simple-evals), SHA-256 feee3f7e7db3617e94e8fcf1977b756ec420ef8568f4e0fcbbe0e92e9d5fc032. Verified comes from the local HF cache.
- **Item file:** results/runs/fresh3/items.json, SHA-256 f6550e9a4ca9bdcdfbe454b504d6e15691508fa02800a648f2ae66b894dc5b8f (results/runs/fresh3_hash.txt).
- **Not inspected:** no question or gold in FRESH-3 has been printed or read. Only counts were seen.
- **Caveat:** stratum O has original SimpleQA gold, which is noisier; SimpleQA Verified was created to fix label problems. This hits system and baseline alike, but it adds grading noise. Results are reported pooled and by stratum; the primary analysis is pooled.

## Design history (DEV only; FRESH is a check, not a tuning set)
results/runs/s16/: evidence variants on DEV, scored with the S14 rules (S16_dev_tables_*.md).
- **Evidence:** Serper question-only with 5 results < Serper with 8 results < combined passage (Serper pages + local FineWiki); local FineWiki alone is weak.
- **Errors:** on the combined passage, 11 of plain's 20 errors are shared by every prompt on the same evidence, so same-evidence agreement cannot catch them.
- **Cross-source agreement:** the share of errors falls sharply with the number of independent sources that agree (0/147 errors when all 3 agree, 13/109 at 2, 13/18 at 1; exploration order).
- **Rules tried on DEV:** about 12 in total (S14 strict, switch, 2-of-3, webfirst, web_cautious, plain-if-≥2/≥3 sources, max-support ≥2/≥3, each ± format guard, two majority baselines). The two chosen rules are the simplest of the cross-source family. This disclosure is the guard against selection bias.

## Pipeline (vkg/s17_run.py; nothing tuned on FRESH-3)
For each question, three independent passages:
- **web:** Serper(question), first 8 unblocked pages, web_passage logic from S13;
- **wiki:** local FineWiki Aug 2025 top-5 titles, retrieval2.passage logic;
- **combo:** both page sets in one passage.

Each passage is 1500 words, with the S13 contamination guard and the HF Qwen3-Embedding-0.6B embedder on the pod. Qwen3-4B (pod, batched, greedy, 40 tokens) answers with the frozen PLAIN and CAUTIOUS prompts on each passage, giving 6 answers per item. Grading: grader 6.1, with the judge on the pod (backend agreement with the local judge 298/300, results/audit2/pod_judge_check.md).

## Systems and baselines (vkg/s17_eval.py)
**Support score:** support(a) is the number of the 3 sources with at least one answer that agrees with a. The max-support candidate is chosen (ties: fixed order web_plain, web_cautious, wiki_plain, wiki_cautious, combo_plain, combo_cautious), and s is its support.

- **MS2 (primary for L1):** answer the max-support candidate iff s ≥ 2.
- **MS3 (primary for L2):** answer iff s = 3.
- **L1-A baseline:** wiki_plain, the 4B plain prompt on the Wikipedia passage (the pre-registered type of baseline since S8).
- **L1-B baselines:**
  - combo_plain: the plain prompt on the strongest single passage;
  - MSany: the max-support candidate, always answered. It uses the same evidence and generations as MS2, so it is the equal-budget baseline.

## Criteria
- **L1:** as in S15. One-sided 95% paired bootstrap, 10,000 draws, seed 0.
  - (a) the upper bound of mean(e − 0.5·e_base) is below 0;
  - (b) the correct difference is at least 0 (point estimate) and its lower bound is above −0.03;
  - (c) the coverage difference is at least −0.03.
- **L2:** for MS3, the Clopper–Pearson one-sided 95% upper bound on SER (errors over all 1000 items) is below 1%, which means at most 4 errors.
- **L3:** conformal risk control (vkg/crc.py; Angelopoulos et al., ICLR 2024) on the support score, calibrated on DEV + FRESH (n = 500), alpha ∈ {0.01, 0.05}. The guarantee is E[SER] ≤ alpha for exchangeable test items. The FRESH-3 SER at the calibrated threshold is reported.
  - **Scope:** stratum O comes from the original SimpleQA, not Verified, so exchangeability with the calibration set is not assumed for it. The L3 check that counts is stratum V; the pooled result is reported too.

## Power, stated in advance (bootstrap from DEV only, n = 1000, all criteria at once)
| test | power / probability |
|---|---|
| L1-A: MS2 vs wiki_plain | 0.22 (DEV SER 4.7% vs 10.7%: a 56% reduction, just over the 50% line) |
| L1-B: MS2 vs combo_plain or MSany | about 0 |
| L2: MS3 ≤ 4 errors in 1000 | 0.76 if the DEV rate (0.33%) holds; 0.21 if noisier original gold doubles it |

Stricter MS2 variants were also tried on DEV, after the 12 rules above: format guard, combo-supported, both-prompts, both-prompts + format guard. They reach at most 0.43, so none is adopted. Catching the remaining two-source errors needs a further independent signal, such as another retriever or reader model; that is left for later work.

**Primary targets of S17: L2 (MS3) and L3.** L1 is scored and reported, but its low power is stated here, before any run.

FRESH-3 is not the last untouched set. About 2,526 original SimpleQA items outside Verified remain unused (3326 − 800) and can serve a later L1 confirmation with a stronger system.

## Predictions
| | prediction | prior |
|---|---|---|
| Q1 | L2 met: MS3 has ≤ 4 silent errors in 1000 | about 45% |
| Q2 | L3, stratum V: the test SER at the CRC threshold is ≤ alpha, for both alpha = 0.01 and 0.05 | about 75% |
| Q3 | L1-A met (MS2 vs wiki_plain) | about 25% |
| Q4 | L1-B not met against either baseline | about 95% |
| Q5 | MS3 SER is higher on stratum O than on stratum V (noisier gold) | about 70% |
| Q6 | contaminated pages ≤ 5% of fetched pages with text | about 95% |

## Freeze
The FRESH design check (vkg/s17_run.py on FRESH, 200 items) is reported before the FRESH-3 run, and no rule may change because of it. Code hashes are added at freeze time, before FRESH-3 is generated.

## FRESH design check (2026-11-06 19:48; vkg/s17_eval.py fresh; results/runs/s17/S17_fresh_tables.md)
Coverage / correct / SER (%):

| system | FRESH | DEV |
|---|---|---|
| MS2 | 77.0 / 69.5 / 7.5 | 85.3 / 80.7 / 4.7 |
| MS3 | 46.5 / 45.0 / 1.5 (3 errors in 200) | 49.0 / 48.7 / 0.3 |
| wiki_plain | 65.0 / 55.5 / 9.5 | |
| combo_plain | 85.0 / 71.5 / 13.5 | |
| MSany | 87.0 / 72.5 / 14.5 | |

- **L1:** all comparisons NOT MET on FRESH.
- **L3 (calibrated on DEV only):** at alpha 0.01, test SER is 1.5%; at alpha 0.05, it is 7.5%. Both are above alpha on this one draw. The guarantee holds only in expectation, but this is a warning sign.
- **Reading:** DEV was optimistic. About 16 rules were tried there, which inflates DEV results. At the FRESH rate, MS3 would make about 15 errors on FRESH-3, against at most 4 allowed, so Q1 (L2) is now very unlikely.
- **Decision:** FRESH-3 is **not** run with this design. It stays sealed. Next steps: (1) check whether the 3 MS3 errors on FRESH are real or grading/gold issues; (2) add an independent signal, such as a second reader model or retriever, designed on DEV + FRESH pooled; (3) only then freeze and run.
- **The 3 MS3 errors on FRESH (checked):** Lemaître publication year, 1931 vs gold 1933; first Bassmaster tournament, Beaver Lake vs Lake Mead; Ursa Minor cave, "August 2006" vs August 19, 2006. The first two are real errors that all three sources share. The third is an incomplete date, which grader 6.1 correctly scores as wrong. None is a grading artifact.
