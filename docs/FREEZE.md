# Freeze record (written 2026-11-05 00:42 BEFORE the held-out run)

Code hashes (sha256):
```
dfb8b9b22cc2aceb36332a74c7cb8d0b5ae3c0318b9504aadb57489dcea95bea  vkg/systems.py
bda61f873cda2afefcc09fa8b2315284e5a85791af95242cc00eed594b2ad9ad  vkg/tasks.py
10767d35d1b4e588c1b0a1d8537982ba84828c07d3622857158da87f36aaf680  vkg/llm.py
009d49d469022c8e87422be601f8836ca89f9c5a0fbaf0f05936b55e72fa4088  vkg/metrics.py
```
Systems frozen: B0_raw, B1_abstain, VKG_v2 (checker = same model), VKG_v2x (checker = qwen3-vl:8b-instruct).
Model under test: qwen3.8-27b (Qwen3.8-27B, UD-Q5_K_M, Ollama). Held-out samples: SQuAD2 seed 1000 and FaithEval seed 1000
(both disjoint from dev seed 0), synthetic seed 1001. Each run once; no code change afterwards.

## Predictions written before seeing held-out results (dev-based)
P1. squad2: VKG_v2 strict SER is lower than B1_abstain by >= 3 points (dev: 7.3).
P2. squad2: VKG_v2 yield is lower than B1_abstain by <= 8 points (dev: 5.3). If larger, the gain is mostly abstention.
P3. faitheval: VKG_v2 strict SER lower than B1_abstain (dev: 6.3 points).
P4. synthetic: gains concentrate in the formal family (code execution), not in verification.
P5. VKG_v2x (smaller checker) is no better than VKG_v2.
Any prediction that fails is reported as failed. Residual unanswerable error on SQuAD2 is expected to stay >= 10%.

---
# Freeze 2 (2026-11-05 01:18) — matched-coverage control, written BEFORE the run
Added `b2_strict` (a more cautious single-call prompt, no verifier) to vkg/systems.py. Existing systems unchanged (only an added function).
```
39493d823923019cec6f14444c7afafc1c28fb1e131b0ca40c95aedd39711844  vkg/systems.py
```
Run: SQuAD2 seed 2000 (excludes dev seed 0), systems B1_abstain, B2_strict, VKG_v2. One run.
P6. B2_strict lowers strict SER vs B1 but loses yield; VKG_v2 is NOT dominated by B2 (no B2 point with both SER <= VKG_v2's and yield >= VKG_v2's).
If P6 fails, the verifier's contribution over a cautious prompt is not demonstrated and SUMMARY.md must say so.

Correction (01:19): the freeze-2 hash above was of a file with a syntax error; no run executed with it. Corrected hash, still before any run:
```
7f22d4bad5eb1a568f91647df4dfd024479d6e0d2edac1cdadf3763ebe7eb21d  vkg/systems.py
```

---
# Freeze 3 (2026-11-05) - matched-coverage control on FaithEval and synthetic, written BEFORE the runs
Code unchanged since freeze 2 (hashes re-checked: systems.py 7f22d4ba..., tasks.py bda61f87..., metrics.py 009d49d4..., llm.py 10767d35...).
Runs (one each, systems B1_abstain, B2_strict, VKG_v2): FaithEval seed 2000 excluding seed 0 and 1000; synthetic seed 2001. Model qwen3.8-27b Q5_K_M.
Predictions:
P7. FaithEval: VKG_v2 strict SER is lower than B2_strict by less than 3 points (verifier adds little over a cautious prompt, as on SQuAD2).
P8. Synthetic: VKG_v2 SER is lower than B2_strict by >= 10 points, because B2 has no code route for formal items (this is the code route, not verification).
P9. Synthetic closed_conf: B2_strict and VKG_v2 both leave >= 20% of contradictory passages answered silently.
Failed predictions are reported as failed.

---
# Freeze 4 (2026-11-05) - generator bug found BEFORE any freeze-3 result existed; supersedes freeze 3's P9
Found while inspecting the 10 residual silent errors on synthetic closed_conf (held-out seed 1001): the contradiction sentence read
"The official registry filing says that it ..." with no named organization. The sentences are shuffled, so "it" bound to whichever
sentence came before. Counting items where the antecedent is the question's organization: 17 of 30 well-posed (seed 0), 13 of 30 (seed 1001).
On seed 1001 all 10 VKG_v2 silent errors on closed_conf are ill-posed items (gold "conflict" not recoverable from the text); on the 13 well-posed
items VKG_v2 qualified 13/13 and B1_abstain 12/13. So the earlier claims "about 1/3 of contradictory passages are still answered silently" and the
pronoun-loosening of the conflict prompt were fitted to an ill-posed benchmark. All earlier synthetic closed_conf numbers (seeds 0 and 1001) are
biased and must not be used for conflict claims; other synthetic families are unaffected (their generator code is unchanged).
Fix in vkg/tasks.py (one line): the registry sentence now names the organization. Hashes before any new run:
```
e006321d038688f20e860a8e98e12b3931fc08e7e4c12a20c90efb54865b18d7  vkg/tasks.py
7f22d4bad5eb1a568f91647df4dfd024479d6e0d2edac1cdadf3763ebe7eb21d  vkg/systems.py   (unchanged)
009d49d469022c8e87422be601f8836ca89f9c5a0fbaf0f05936b55e72fa4088  vkg/metrics.py   (unchanged)
```
Runs: FaithEval seed 2000 (exclude 0, 1000), synthetic seed 2001 (fixed generator), systems B1_abstain, B2_strict, VKG_v2. P7 and P8 stand as written in freeze 3.
P9 (replaces old P9). With well-posed conflicts, closed_conf: VKG_v2 qualifies >= 90% of the 30 contradictory passages and B1_abstain >= 80%,
i.e. the verifier's conflict check will show little advantage over B1 on this synthetic family.

## Freeze 3/4 scoring (2026-11-05, after the runs; numbers from results/runs/b2ctrl_faitheval_*_s2000_n300 and b2ctrl_synthetic_*_s2001_n300)
- P7 pass: FaithEval strict SER VKG_v2 9.7% vs B2_strict 11.3%; difference -1.7 pts, paired CI [-4.7, +1.3] (includes 0). B1_abstain 20.7%.
- P8 pass: synthetic strict SER VKG_v2 0.3% vs B2_strict 14.0%, difference -13.7 pts, CI [-17.7, -9.7]. B2 is identical to B1 on every synthetic item (B2 only changes passage prompts) and the whole gap sits in the formal family (code route: formal errors 41/60 -> 1/60, over-abstain 7/60). Yield +22.0 pts, CI [+12.9, +30.2], again from the formal family.
- P9 (new) pass but uninformative: with well-posed conflicts, B1, B2 and VKG_v2 all qualify 30/30 contradictory passages. The synthetic conflict family is now at ceiling and cannot separate systems; harder contradictions are needed (FaithEval 'inconsistent' is the harder real test: strict SER on conflicts B1 8.7%, B2 7.3%, VKG_v2 6.7%).

---
# Freeze 5 (2026-11-05 08:58) - open-world run on SimpleQA Verified, written BEFORE the run
Reuse: SimpleQA Verified (Google, arXiv 2509.07968) is an existing public benchmark (HF google/simpleqa-verified); only a loader was added. Prior work on abstention training
(Chen et al. 2510.17733; 2601.20126; Abstain-R1 2604.17073) is NOT repeated here.
Added: tasks.simpleqa, run.py suite option, vkg/grade_open.py (two fixed graders: strict string match, lenient token containment; no LLM judge).
Hashes:
```
7f22d4bad5eb1a568f91647df4dfd024479d6e0d2edac1cdadf3763ebe7eb21d vkg/systems.py
83cfee08bcf51bd748f0d8a88809479695ab69b8ca1cfc9976dcc5b535b0dc0e vkg/tasks.py
009d49d469022c8e87422be601f8836ca89f9c5a0fbaf0f05936b55e72fa4088 vkg/metrics.py
10767d35d1b4e588c1b0a1d8537982ba84828c07d3622857158da87f36aaf680 vkg/llm.py
e3a839a1a39f0316321622908e6e5ac0567485d1b70f49f166317e3d229e4458 vkg/grade_open.py
a5f7b0e27bf05dc6629551123c6d508a881d7b700c8762fc38d202f413efcdf7 vkg/run.py
```
systems.py, metrics.py, llm.py unchanged since freeze 2/4 (see earlier hashes). Run: seed 3000, n=500 random questions, model qwen3.8-27b Q5_K_M, systems B0_raw, B1_abstain, VKG_v2 (open route = 5-sample self-consistency, need 4). One run.
Known limits: SimpleQA Verified is public since 2025, so contamination in training data is possible; the Qwen3.8 cutoff is not stated. Graders can misgrade paraphrases: strict = upper bound on errors, lenient = lower bound.
Predictions:
P10. B0_raw attempts >= 95% of questions and its strict-wrong rate is >= 60% of all questions.
P11. B1_abstain lowers the strict-wrong rate versus B0_raw by >= 15 points (paired CI excludes 0), while its strict-correct rate drops by <= 8 points.
P12. VKG_v2 lowers the strict-wrong rate versus B1 by >= 3 points, and its precision (strict-correct / attempted) is higher than B1's, while its strict-correct count falls (self-consistency also abstains on correct answers).
P13. Even the best system answers wrongly on >= 25% of the questions it attempts (strict bound), i.e. open-world hallucination is reduced, not removed.

## Freeze 5 scoring (after the run; results/runs/openworld_simpleqa_qwen3.8-27b_s3000_n500.*, graded with vkg/grade_open.py)
- P10 pass: B0_raw attempted 100%, strict-wrong 95.6% of all questions (22/500 strict-correct).
- P11 pass: B1 strict-wrong 18.4% vs 95.6% (paired -77.2 pts, CI [-80.8, -73.4]); strict-correct 4.4% -> 1.8% (-2.6 pts).
- P12 pass, with a caveat: VKG_v2 vs B1 strict-wrong -16.6 pts (CI [-19.8, -13.4]); precision 25.0% vs 8.9%, but VKG_v2 attempted only 12 questions (3 correct), so its precision has a very wide interval. Strict-correct fell from 9 to 3 questions.
- P13 pass: of attempted answers, strict-wrong is 91% for B1 (94/103) and 75% for VKG_v2 (9/12).
Grader check: a random read of 24 B0 answers showed genuinely different entities, dates and numbers (no formatting artifacts). Known gaps: gold strings with an "acceptable range", and number words ("two" vs 5), are not matched by either grader, so the strict-wrong figures are slight overestimates; lenient and strict differ by 0.4 pts for B0.

---
# Freeze 6 (2026-11-05 09:27) - retrieval-grounded open-world runs on SimpleQA Verified, written BEFORE the runs
Prior-work check done first (REUSE_MAP): no published Wikipedia-retrieval baseline for SimpleQA Verified with small open models was found; general RAG-abstention work exists
(GRACE 2601.04525; GRAB-RAG 2608.22228: misleading retrieved context is the main failure mode). SimpleQA Verified is designed for parametric knowledge, so this is a different measurement.
Added: vkg/retrieval.py (live en.wikipedia.org API, keyword query, BM25 over 120-word chunks, top chunks up to 900 words; on-disk cache results/cache/wiki), tasks.simpleqa_rag (modes search / oracle), run.py suites.
Settings fixed a priori; only a 40-question dev check (seed 9999) of title recall and a 12-question smoke run were done; the keyword-fallback (10->6->4->3 terms) was added after seeing 4 empty searches on that dev set. Dev title recall@5 (gold Wikipedia page in top 5): 17/31 exact, 20/31 near.
Hashes:
```
7f22d4bad5eb1a568f91647df4dfd024479d6e0d2edac1cdadf3763ebe7eb21d vkg/systems.py
a4753d5710b6f8a2131289a11ece5b52fc951aab62d6e86b523e30ed8454e6cc vkg/tasks.py
009d49d469022c8e87422be601f8836ca89f9c5a0fbaf0f05936b55e72fa4088 vkg/metrics.py
10767d35d1b4e588c1b0a1d8537982ba84828c07d3622857158da87f36aaf680 vkg/llm.py
e3a839a1a39f0316321622908e6e5ac0567485d1b70f49f166317e3d229e4458 vkg/grade_open.py
c9786f9dcc75f0c5bd5f3be3bc1fba4ab97e9e473d04df17c97378b16beb4d74 vkg/run.py
4476ab616f43191ea6557f4e466e4bcfd0883c89a159ed59041e2c6aeb0412ec vkg/retrieval.py
```
Runs, one each: same 500 questions as the closed-book run (seed 3000). search = retrieval over live Wikipedia with no gold information; oracle = the dataset's own Wikipedia source pages (upper bound, not deployable; questions without a Wikipedia source are skipped).
Systems: B0_raw (answers with passage, no abstain option), B1_abstain, B2_strict, VKG_v2 (verbatim-quote verifier + incompatibility check, same-model checker). Model qwen3.8-27b Q5_K_M.
Note: a non-"answer" status (unknown or conflict) counts as not attempted in grade_open; Wikipedia content is live and may differ from the 2025 gold; both effects can lower correct counts.
Predictions:
P14. search: B1_abstain strict-correct >= 20% of all questions (closed-book was 1.8%).
P15. oracle B1 strict-correct exceeds search B1 by >= 8 points (retrieval, not reading, is the bottleneck).
P16. search: B0_raw strict-wrong >= 10% of all questions (it answers from memory when the passage lacks the fact), and each of B1, B2, VKG_v2 lowers it by >= 3 points (paired CI excludes 0).
P17. search: VKG_v2 minus B2_strict is within +-3 points on strict-wrong and within +-5 points on strict-correct (verifier again not shown to beat a cautious prompt).
P18. search: every system still answers wrongly on >= 3% of all questions (strict bound), i.e. retrieval does not remove silent errors.

## Freeze 6b (2026-11-05 09:48) - incident before any result existed
The first launch hit Wikipedia HTTP 429 (retry-after 44 s). vkg/retrieval.py then returned empty results after 4 short retries, which would have produced empty passages and understated retrieval. I killed the job; no results file was written or read. Fix: requests are serialized, >= 1 s apart, honour Retry-After, and raise after 8 failures (a failed fetch can no longer look like "nothing found"). Retrieval settings, systems and predictions P14-P18 are unchanged.
New hash: 97c59ae14ab6b896de132e228a237bc12e0c94f93a40a55194723cf277a129dc  vkg/retrieval.py  (other files as in freeze 6).
Plan: prefetch all passages first (slow, rate-limited), then run the four systems on cached passages.

## Freeze 6c (2026-11-05 10:11) - sample size reduced before any result existed
Wikipedia throttles this client to roughly 8-12 requests per minute, so 500 questions would need 4-5 more hours of prefetching. Decision made before any model output on retrieval: use the first 300 questions of the same seed-3000 sample (verified: random.Random(3000).sample(range(1000),300) is a prefix of the 500-sample). The closed-book comparison is recomputed on those same 300 ids from the existing run. Everything else, including predictions P14-P18, is unchanged.

## Freeze 6d (2026-11-05 10:40) - retrieval backend changed before any result existed
Cause of the multi-hour estimate: Wikipedia's API/REST endpoints throttled this client to ~10 requests/minute (HTTP 429, retry-after ~44 s; measured by inter-arrival gaps of cached files: ~1.7 s per request, then a ~44 s stall every ~10 requests). It was a rate limit, not a bug in the harness.
Change: vkg/retrieval.py now uses en.wikipedia.org/w/index.php, which was not throttled in probes (12/12 raw pages, 8/8 searches at ~1 s). Search = same Wikipedia search engine via its HTML page; page text = raw wikitext cleaned to text (infobox fields kept as "key: value"; convert, date, lang, nowrap and list templates rendered; cites/navboxes/refs/files dropped; table cells kept as text). The cleaner first deleted every template and lost values such as "{{convert|900|ft|m}}"; fixed after checking one dev page (Getty Center). Dev pages used for these checks: Getty Center, Sam Manekshaw, Horizons (Epcot) (all from the seed-9999 dev sample, not the seed-3000 test sample).
Known limits of the cleaner: units stay abbreviated ("ft"), complex tables are flattened, some templates carrying values are dropped. These can lower correct counts; they cannot raise them.
Hashes (before runs):
```
e758be08014fbba9996a30851f36b2d39a5b549c55c8181951efeeb39b3a03e9 vkg/retrieval.py
a4753d5710b6f8a2131289a11ece5b52fc951aab62d6e86b523e30ed8454e6cc vkg/tasks.py
7f22d4bad5eb1a568f91647df4dfd024479d6e0d2edac1cdadf3763ebe7eb21d vkg/systems.py
```
Sample (first 300 of seed 3000), systems and predictions P14-P18 unchanged. The older API cache entries are unused.

Freeze 6e (2026-11-05 10:56): one page fetch failed transiently after 8 attempts (the page loads normally when retried), so the client now makes 12 attempts with backoff up to 60 s. Cached progress kept. New hash: 85bcccd902b3eee821c008ac7cc89cba15b3da0d72b61dc49d263999d10e65f5 vkg/retrieval.py

## Freeze 6 scoring (after the runs; 300 questions, seed 3000; results/runs/openworld_simpleqa_rag_*_n300 and openworld_simpleqa_oracle_*_n251)
- P14 pass: search retrieval, B1_abstain strict-correct 32.7% of all questions (closed-book on the same 300: 1.0%).
- P15 pass: on the 251 questions that have an oracle page, B1 strict-correct is 56.6% with the oracle pages vs 37.8% with live search (+18.8 pts).
- P16 pass: B0_raw (with passage) strict-wrong 55.0%; B1 -42.7 pts (paired CI [-48.3,-37.3]), B2_strict -43.3 [-49.0,-38.0], VKG_v2 -45.0 [-50.7,-39.3].
- P17 pass as written (point estimates inside the bands): VKG_v2 minus B2_strict strict-wrong -1.7 pts (CI [-3.3,-0.3]), strict-correct -3.0 pts (CI [-5.0,-1.3]). The wrong-answer interval excludes 0, so VKG_v2 removes a few more wrong answers than B2 but loses more correct ones (search: 89 vs 98 correct and 26 vs 31 wrong across both evidence conditions).
- P18 pass: lowest strict-wrong share is VKG_v2's 10.0% of all questions (search) and 17.9% (oracle).
Incidents and changes before the runs: see freeze 6b-6e (Wikipedia throttling, backend change, cleaner fix). Page-text cleaning can only remove information, so coverage and correct counts are lower bounds on what a perfect cleaner would give.

---
# S2 dev protocol (2026-11-05 11:43) - written BEFORE measuring variants
Goal: raise the share of questions whose gold answer is present in the passage (evidence coverage) without touching the 300 test ids.
Dev set: 150 SimpleQA Verified questions drawn with seed 4000 from the 700 ids outside the test sample (first 300 of seed 3000). Measured by vkg/dev_retrieval.py.
Variants: A baseline (frozen), B larger passage budget, C more pages, D hybrid BM25 + qwen3-embedding:0.6b (reciprocal-rank fusion), E query rewrite by the generator + hybrid + 10 pages.
Decision rule (ROADMAP): adopt the best variant only if its dev coverage beats A by >= 10 points and its mean passage length stays <= 1600 words; otherwise keep A and report coverage as corpus-limited.
Prediction: coverage A ~40%; best variant 50-55%; none above 70% (a share of answers is in non-Wikipedia sources or flattened tables).

---
# Corrections after the independent audit (2026-11-05 12:30); full report in docs/AUDIT.md. I re-checked items 1-3 myself.
1. FaithEval seed 2000 (freeze 3/4) was NOT disjoint from earlier samples: the run used --exclude-seed 1000 only, so 26 items repeat dev seed 0 and 22 repeat held-out seed 1000 (48 of 300). On the 252 clean items the VKG_v2 minus B2 conclusion is unchanged (-1.6 pts, audit CI [-5.2, +2.0]). The earlier sentence "excludes seed 0 and 1000" is withdrawn.
2. The page-cleaner fix in freeze 6d used two TEST questions' pages (Getty Center = sqa-3343, Horizons = sqa-323) while calling them dev pages; the seed-9999 dev sample code was not saved. No gold answer was tuned to, but it is a protocol violation. Sensitivity: results/open_world_tables.md recomputes the search run without those two ids; no number moves by more than 0.4 pts.
3. The strict and first lenient graders miss correct SimpleQA answers (gold ending in ".", "(acceptable range)", hyphens, number words, date order/abbreviations). The repaired grader (vkg/grade_open.py: repaired / grade_v3, unit-tested on 20 audit cases; 25 sampled new credits all correct by eye; 34 remaining B1 wrong rows read, about 6 are false negatives such as omitted middle names) was added AFTER seeing results. Strict numbers are now labelled upper bounds on wrong answers; the repaired numbers are the best estimate. All open-world tables are regenerated by vkg/analyze_open.py into results/open_world_tables.md.
4. P9 (freeze 4) was written after inspecting seed-1001 results, so it is not a blind prediction. P5 passes on silent-error rate only (VKG_v2x has higher SQuAD2 yield, +5.3). P12's precision gain (3/12 vs 9/101) is not significant (Fisher p=0.12). P17 and P18 depend on the grader: under the repaired grader VKG_v2 minus B2 wrong is -0.3 pts (CI [-1.7,+0.7]), so P17's "removes a few more wrong answers" reading is not supported.
5. B0_raw abstention is detected by regex, so refusals written as text count as answers (54 of 60 held-out synthetic open_fict B0 "errors" say the entity does not exist). B0 rows are reference only; the synthetic B0 SER of 49.3% is inflated by about 18 points.
6. The oracle condition uses the dataset's gold source URLs. It is an upper bound for retrieval, not a deployable system, and the oracle table must say so.

---
# Freeze 7 (2026-11-05 13:25) - S2 retrieval variant E on the 300 test ids, written BEFORE building or scoring test passages
S2 dev result (150 SimpleQA Verified questions outside the test ids, seed 4000; gold string present in passage, repaired matcher): A baseline 48.7%, B bigger budget 52.7%, C more pages 54.7%, D hybrid BM25+embedding 56.0%, E generator-written queries + hybrid + 10 pages 75.3% (mean 1,573 words). Old matcher: 40.7 / 44.7 / 45.3 / 48.0 / 64.7. Decision rule from the S2 protocol (+10 points over A, <= 1,600 words) is met by E only.
Variant E = tasks.simpleqa_rag(mode="hybrid"): baseline keyword search (top 5) plus search for up to 3 queries written by qwen3.8-27b from the question alone (no gold), up to 10 pages, 120-word chunks scored by BM25 and qwen3-embedding:0.6b fused by reciprocal rank, 1,500-word passage.
Run: first 300 of the seed-3000 sample (the same 300 as the baseline retrieval run), systems B0_raw, B1_abstain, B2_strict, VKG_v2, model qwen3.8-27b Q5_K_M, graded by the repaired grader (best estimate) and strict (upper bound on wrong), tables by vkg/analyze_open.py. Single run.
Hashes:
```
7f22d4bad5eb1a568f91647df4dfd024479d6e0d2edac1cdadf3763ebe7eb21d vkg/systems.py
62cb9fb7796e95d936192cb5aca3ac146cd79cc8bcd153d155c94e1f4690e092 vkg/tasks.py
85bcccd902b3eee821c008ac7cc89cba15b3da0d72b61dc49d263999d10e65f5 vkg/retrieval.py
f2a39fc44b639e71e07fdfe9d15d35815397aab2b22bc2e284b0d0e038181323 vkg/retrieval2.py
0c2d1ea03f36cb0644ef8b2e5d98f261d49022ecb795f367f922a54a30004b14 vkg/run.py
0579f162d7e3e35f0b3f0354a9b4666dd0082403612549b8acebb8777725e790 vkg/grade_open.py
a4c1734a332455bd5a7fc36b9368be7e6cdb890e96e77996285cba70742df190 vkg/analyze_open.py
10767d35d1b4e588c1b0a1d8537982ba84828c07d3622857158da87f36aaf680 vkg/llm.py
```
Baseline for comparison (repaired grader, search retrieval, same 300): B1 correct 40.0%, wrong 5.0%; evidence coverage 48.7%; B1 correct when the evidence has the answer 118/146 (80.8%).
Predictions:
P19. Test evidence coverage (repaired matcher) of variant E is >= 62% (dev gain was +26.6 points; I expect part of it not to transfer).
P20. B1_abstain correct (repaired) >= 45% of all questions.
P21. B1_abstain wrong (repaired) <= 8% of all questions: more evidence must not raise silent errors by more than 3 points.
P22. VKG_v2 minus B2_strict (paired, repaired): correct <= -2 points with CI upper bound below 0; wrong within +-2 points.
P23. Among questions whose passage contains the answer, B1 is correct on >= 75% (longer, noisier passages must not cut reading accuracy much below the 80.8% baseline).
Any failed prediction is reported as failed.

## Freeze 7 scoring (2026-11-05 14:59); numbers from results/open_world_tables.md (vkg/analyze_open.py), repaired grader, 300 test questions, variant E vs baseline search retrieval
- P19 pass: evidence coverage 212/300 = 70.7% (baseline 48.7%; dev had predicted gain +26.6, test gain +22.0).
- P20 pass: B1_abstain correct 58.7% (baseline 40.0%; paired difference +18.7 pts, CI [+14.0, +23.7]).
- P21 pass: B1_abstain wrong 6.3% (baseline 5.0%; paired +1.3 pts, CI [-1.0, +3.7], not significant).
- P22 pass as written: VKG_v2 minus B2_strict correct -5.3 pts (CI [-8.0, -3.0]); wrong -1.7 pts (CI [-3.3, -0.3]), inside the +-2 band.
- P23 pass: among questions whose passage contains the answer B1 is correct on 174/212 = 82.1% (baseline 118/146 = 80.8%).
Note: vkg/analyze_open.py was extended after the freeze-7 hash (it only produces tables; the answers come from the frozen run). Grader false negatives are still present (docs/GRADER_VALIDATION.md): wrong counts are upper bounds.

---
# Corrections after the second audit (2026-11-05 17:07); see docs/AUDIT2.md and the matching block at the top of results/SUMMARY.md
TriviaQA duplicates made S6a's "disjoint" claim false (67 of 500 test rows in training); S6a was rerun as S6a-clean (docs/S6A_CLEAN_PROTOCOL.md). Plain-baseline regex misses, S5 tallies, S6b "nearly matches" and R4 wording corrected in SUMMARY. All earlier S5/S6a/S6b scoring lines that conflict with these corrections are superseded by them.

---
# Freeze S7b (2026-11-05): evidence-sufficiency probe as an answer gate
Protocol and predictions: docs/S7B_PROTOCOL.md, written before the run. vkg/s7b_gate.py SHA-256 dc1c25240d16fd87d20edd0f61cb3585048117e7ce04cee76104e71311552505. Inputs frozen: S7 features, S6b outputs, 27B freeze-7 run.

## Freeze S7b scoring
- P1 fail as worded: gate+plain SER 4.7% on SimpleQA-E (predicted 6-13%; better than predicted).
- P2 pass: plain@matched minus cautious SER +1.0 pts [-1.3, +3.3].
- P3 fail: gate+cautious minus cautious SER -3.0 [-5.0, -1.3] (in range) but yield loss 8.3 pts (bound 6).
- P4 pass: SQuAD2 gate+plain SER 14.3%.
- P5 pass: FaithEval unanswerable gate+plain SER 33.3%.
- P6 partial: gated 27B B1 SER 4.0% (bound 4.5%) pass; correct loss 13.3 pts (bound 5) fail.
- Decision rule: SER reduction significant, yield loss above 5 pts -> not useful as an add-on at T50.
Post hoc (labelled in results/S7b_evidence_gate.md): threshold sweep; manual reading of the 12 residual errors (7 likely grader false negatives).

---
# Freeze S8 (2026-11-05): code-only answer-vs-passage check
Protocol, predictions and amendments: docs/S8_PROTOCOL.md (all before any fresh answer). Hashes: vkg/support_check.py 368aec29...bc3f43; vkg/s8_eval.py 7db42572640f162cb164dc10b42b81942e4f42040b1180953689ca0032bb7e72 (checked unchanged at scoring); vkg/s8_fresh.py and vkg/s8_wait.py in results/runs/s8/hashes_before_build.txt. Fresh run 20:07-21:47.

## Freeze S8 scoring (FRESH, n=200, frozen graders)
- F1 (strict detector, secondary): plain SER -21.0 pts, correct -2.5; inflated by non-answers (Amendment 1).
- F1' pass: plain (cleaner detector) SER 14.0% -> 11.5%, -2.5 [-5.0, -0.5], correct -2.5.
- F2 pass: cautious SER -0.5, correct -0.5.
- F3 pass: 27B B1 SER 0.0, correct -1.0.
- F4' pass: plain+check vs cautious: correct +2.5, SER +2.5.
- F5' fail: 5 of 10 removed real answers graded wrong (predicted >= 75%).
- F6 (manual, one rater): all 5 removed graded-correct answers are truly correct; removed graded-wrong: 4 real errors, 1 missed denial. Cautious+check kept 17 graded-wrong: 10 grader misses, 6 real errors (5 with the gold in the passage), 1 gold/source conflict.
- Decision rule (revised): formally met. Substantive reading: no useful error separation on fresh data (results/S8_answer_check.md).

---
# Freeze S9 (2026-11-05): certificate-constrained answering
Protocol and predictions: docs/CERT_PROTOCOL.md (before any full run). Hashes checked unchanged at scoring: vkg/cert_gen.py 1e2c9343629669f1a49f703f9be82d4203ebaea1e776f0de96aa27883db52cbe; vkg/cert_eval.py 8ba0900fa89f645341006ddcba72887c3d2e8f0bcd3f81d00398245315377e34. Runs 21:48-21:55.

## Freeze S9 scoring
- C1 pass: 776/776 certificates verified.
- C2 fail: FRESH SER 11.0% vs cautious 9.0% (+2.0 [-1.0, +5.0]); correct +1.5.
- C3 fail: SimpleQA-E SER 11.0% (bound 7.0%); correct 54.7% (half passes).
- C4 fail: SQuAD2 SER 33.3% (bound 18.0%); correct among answerable 88.7% (half passes).
- C5 fail: FaithEval +25.0 pts vs cautious (bound ±10).
- C6 pass: compute mode 2/300.
- Decision rule: not useful. Manual reading of FRESH errors in results/S9_certificates.md (about 5.5% real vs 3.5% cautious).

---
# Freeze grader 5 (2026-11-05): LLM judge with the SimpleQA Verified prompt
Protocol and criteria: docs/GRADER5_PROTOCOL.md (before any judge call). Hashes there; scoring script vkg/grader5_eval.py 0c84921cd95d159a8b3dc255987fd73204c09563be31830b2ef2ae636f69b6f5 (written before any judge output was read).

## Grader 5 scoring
- J1 fail: false credit 5/82 on V2 (bound 4).
- J2 pass: misses 1/150.
- J3 pass: V1 false credit 3/73 (4.1%), misses 2/167 (1.2%).
- J4: 17 answered rows judged NOT_ATTEMPTED.
- Decision: judge rejected as primary grader; v4 stays primary; judge regrade reported as a lower bound on SER (results/grader5/GRADER5_RESULT.md).

---
# Freeze grader 6 (2026-11-05): judge + completeness veto
Protocol, hashes, criteria: docs/GRADER6_PROTOCOL.md (before any V3 judge output; labels hashed before reading). vkg/grade6.py 05b24d6b... and vkg/grader6_eval.py ed6ab68a... unchanged at scoring.

## Grader 6 scoring (V3, 260 blind rows)
- K1 pass: false credit 0/196 (bound 3.0%).
- K2 pass: misses 0/64 (bound 5.0%).
- K3: no veto fired; judge alone also 0/0; v3 and v4 4 misses each. V3 turned out easy (4 of 200 grader-wrong rows were really correct).
- Decision: grader 6 adopted as primary grader for new runs (v4 beside it); past predictions keep frozen graders. Regrade in results/grader6/regrade6.md.

---
# Freeze S10 (2026-11-05): code-generated reading curriculum
Protocol and predictions: docs/S10_PROTOCOL.md (before training). Scoring-script crash fix recorded there (a67af159...).

## S10 scoring
- R1 pass as scored (synthetic SER 0.0% vs 16.3%), fail after correcting a number-word matching artifact (gap 5.7 pts < 10).
- R2 fail: FRESH+SimpleQA-E pooled SER +0.4 [-0.8, +1.6].
- R3 pass on intent: SQuAD2 SER +0.7; correct +4.6 (a gain; fails only if "within 3 points" is read as two-sided).
- R4 fail: FaithEval SER +11.7 [+7.3, +16.3].
- R5 pass: coverage +1.2.
- Decision: not useful (in-distribution learning only; harms counterfactual passages). results/S10_reading_curriculum.md

---
# Freeze S11 (2026-11-05/06): search-on-abstain for the 4B
Protocol and predictions: docs/S11_PROTOCOL.md (before the run). vkg/s11_eval.py 21fecbb7... unchanged at scoring.

## S11 scoring (grader 6; pooled FRESH + DEV = 500)
- S1 pass (borderline): recovery 12/39 = 31%.
- S2 fail: SER +1.4 [+0.4, +2.4] (bound +1.0); new-answer precision 0.67.
- S3 fail: correct +2.8 [+1.6, +4.4] (bound 3).
- S4 fail: FRESH coverage 62%, correct 58%, SER 4.0% (L1 not reached).
- S5: 1.9 rounds, 6.6 pages, 19 s per searched item.
- Decision: direction not confirmed as specified. Post-hoc breakdown of abstentions in results/S11_search_on_abstain.md (24% evidence already present, 11% recovered by search, 33% on Wikipedia but missed, 32% not on Wikipedia).

## S12 scoring (grader 6 frozen; 6.1 sensitivity; pooled FRESH + DEV = 500)
| | prediction | result | verdict |
|---|---|---|---|
| T1 | correct ≥ +3.0, CI lower bound > 0 | +4.2 [+2.6, +6.0] | pass |
| T2 | SER ≤ +0.6 | +1.0 [+0.2, +2.0] (6.1: +0.8) | fail |
| T3 | filter precision gain ≥ 0.10 | −0.01 | fail |
| T4 | L1 on FRESH | coverage 64.5%, correct 60.5%, SER 4.0% | fail |
| T5 | cost | 2 rounds, 6.6 pages, 11.4 s | pass |

Decision: not worth its errors. Grader 6.1 amendment: docs/GRADER6_PROTOCOL.md.

## S13 scoring (grader 6.1; pooled FRESH + DEV = 500)
| | prediction | result | verdict |
|---|---|---|---|
| W1 | correct ≥ +4.0, CI lower bound > 0 | +23.4 [+19.8, +27.2] | pass |
| W2 | SER ≤ +1.0 | +2.2 [+1.0, +3.6] | fail |
| W3 | contaminated ≤ 5% | 1.1% | pass |
| W4 | L1 on FRESH | 84.0 / 78.0 / 6.0 (SER over 5.0) | fail |
| W5 | cost | 28 s, 7.9 pages per searched item | logged |

Decision: acceptance must get stricter before confirmation.

## S14 scoring (grader 6.1)
| | prediction | result | verdict |
|---|---|---|---|
| X1 | FRESH L1-A | 75.5 / 72.5 / 3.0 | pass |
| X2 | pooled | SER 3.4, correct +18.0 vs cautious | pass |
| X3 | equal-budget L1-B | SER 3.0 ≤ 3.5, but correct −9.0 vs web_plain | fail |
| X4 | format guard | SER −0.6, correct ±0 | pass |
| X5 | contamination | 0.7% | pass |

Decision: S14 strict goes to the FRESH-2 confirmation.

## S15 (FRESH-2 confirmation), scored 2026-11-06 15:45
Frozen files are unchanged (hashes in docs/S15_PROTOCOL.md checked after the run). Outcome: L1-A not met, L1-B not met. FRESH-2 is now used; it cannot serve as an untouched test set again.

## FRESH-3 sealed (2026-11-06 18:35)
1000 items (200 unused SimpleQA Verified + 800 original SimpleQA not in Verified), results/runs/fresh3/items.json, SHA-256 f6550e9a4ca9bdcdfbe454b504d6e15691508fa02800a648f2ae66b894dc5b8f. Not inspected. Reserved for the S17 confirmation (docs/S17_PROTOCOL.md).

## FRESH-4 sealed (2026-11-06 21:25)
1000 original SimpleQA items (not in Verified, not in FRESH-3), results/runs/fresh4/items.json, SHA-256 e1ca43fc81d4307ddbddf71d7347c34ba687a5e6e07abaf57843a1b937c2cf9a. Not inspected. Reserved with FRESH-3 for the S18 L2 test (docs/S18_PROTOCOL.md, draft).

## S18 run on FRESH-3 + FRESH-4 (2026-11-07 04:10)
Both sets were used once, for the frozen S18 protocol: L2 NOT MET (results/runs/s18/S18_RESULT.md). They cannot serve as untouched test sets again. 1,526 original SimpleQA items remain untouched.

# FRESH-5 (sealed 2026-11-07 08:42, before any S19 output)
1,526 items: ALL remaining original SimpleQA items (official CSV minus Verified minus FRESH-3/4), stratum O, order Random(7000).
results/runs/fresh5/items.json, SHA-256 d9eec22c1b906ae796dc0377be249229ffec4b64245d6fffaba523cb6396effc (vkg/fresh5.py).
Not inspected. Reserved for the joint S19 test (docs/S19_DESIGN.md, Decisions). This is the last untouched SimpleQA pool.
