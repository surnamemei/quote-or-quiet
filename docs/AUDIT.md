# Independent audit (2026-11-05)

Scope: results/SUMMARY.md, docs/FREEZE.md, docs/PROTOCOL.md, vkg/*.py, results/runs/*.jsonl. No LLM, no GPU, nothing under vkg/ or the docs edited.
All scripts are in `results/audit/` (run with `python -B`; `common.py` holds the loaders, `a0`..`a11` the checks; `passages.pkl` is a cache of the rebuilt SimpleQA passages, built from the on-disk Wikipedia cache with the network patched off).
Reproduction method: every number was recomputed from the raw jsonl rows (system, id, kind, status, answer, gold), using the project's own `matches/norm` for SQuAD/FaithEval/synthetic/SimpleQA, plus a re-implementation of the paired bootstrap (`metrics.paired_bootstrap_delta`, B=2000, seed 0) and of `grade_open.main`'s CI.
Side note: a new file `results/runs/s3_signals_raw.jsonl` and `docs/S3_PROTOCOL.md` appeared while I was working. They are outside SUMMARY.md and were not audited; my scripts skip that file.

Headline: the arithmetic in SUMMARY.md is almost entirely correct. The serious problems are (1) the string graders mark many correct SimpleQA answers wrong, which distorts the retrieval-section conclusions (not the ranking of systems), (2) one dataset-hygiene claim is false (FaithEval seed 2000 is not disjoint), (3) test-set items were used as "dev" pages when tuning the retriever's page cleaner, and (4) B0_raw numbers on synthetic/SQuAD are inflated by a regex abstention detector.

---------------------------------------------------------------------------------------------------

## 1. Mismatches (file, claimed, recomputed)

Verified exact (matching the stated rounding): every cell of the held-out SQuAD2 / FaithEval / synthetic tables and paired CIs; the B2 control tables for SQuAD2/FaithEval/synthetic; the n=500 closed-book table and its paired CIs; the n=300 search table; the n=251 oracle table; the closed-book-on-300 line; the dev numbers behind P1-P3 (7.3 / 5.3 / 6.3); P4 (40 errors removed, 38 formal); per-family synthetic counts; the 13/30 and 17/30 well-posed counts from freeze 4 (reconstructed: 13 on seed 1001, 17 on seed 0, 16 on seed 2001); VKG_v2 qualified 13/13 well-posed and B1 12/13 on seed 1001; the manual-check count of 19 residual FaithEval errors. Stored `outcome` equals re-classification with the current `metrics.classify` and `tasks.matches` on all 16 jsonl files (0 differences; no grader drift). No row has a run-time exception masked as an abstention (trace == ["error"]: 0 rows).

Real discrepancies:

| # | where | claimed | recomputed | severity |
|---|---|---|---|---|
| M1 | SUMMARY L72 (b2ctrl synthetic, VKG_v2 minus B2/B1, strict SER) | -13.7 pts, CI -17.7..-9.7 | -13.7, harness-style CI [-18.0, -10.0] (this is what the run's own .md prints: [-0.180, -0.100]); numpy-percentile CI [-17.7, -10.0]. The upper end -9.7 is not reproducible; -17.7..-9.7 is the CI of the *held-out seed 1001* line (-13.3). | low (copy error) |
| M2 | FREEZE P8 scoring | yield +22.0, CI [+12.9, +30.2] | .md: [+13.8, +31.0]; numpy percentile [+13.7, +30.1] | low |
| M3 | SUMMARY L71 / FREEZE P7 (FaithEval VKG_v2 minus B2, strict SER) | -1.7, CI [-4.7, +1.3] | -1.7, harness method [-5.0, +1.3]; numpy [-4.7, +1.3] | low. Different bootstrap implementations are mixed across the document (the SQuAD2 VKG-minus-B2 CI uses the harness method and matches exactly). |
| M4 | SUMMARY L71 "Unanswerable questions answered silently: B1 32.7%, B2 15.3%, VKG_v2 12.7%" | labelled "answered silently" | those are strict (silent + false_conflict) rates. Silent-only: B1 30.7, B2 13.3, VKG 12.7. | low (mislabel) |
| M5 | SUMMARY held-out tables, column definitions | SQuAD column "silent error on unanswerable" = silent only (B1 20.0; strict would be 22.0). FaithEval column "unanswerable" = strict (B1 26.0, VKG_v2x 22.0; silent-only 25.3 and 21.3). | the two tables use different definitions for the analogous column | low |
| M6 | FREEZE P13 "B1 strict-wrong 91% (94/103)" | 94/103 | `grade_open` gives 92/101. The 103 comes from `classify`, which counts 2 B1 rows with status "answer" and an empty answer string as answered silent errors; `grade_open` treats them as abstentions. Ratio is 91% both ways. | trivial, but shows two inconsistent attempt definitions |
| M7 | FREEZE P17 "89 vs 98 correct and 26 vs 31 wrong across both evidence conditions" | | 89 vs 98 correct is the "evidence contains the answer" condition only (VKG_v2 vs B2_strict); across both conditions it is 91 vs 100 (strict+lenient) or 87 vs 96 (strict). 26 vs 31 wrong is both conditions (with `analyze_rag`'s grade, which counts lenient2-correct answers as wrong). Mixed bases in one sentence. | low |
| M8 | SUMMARY L3 "Every number is read from the named file" | | The SimpleQA tables are not in any .md file; they come from running `grade_open` on the jsonl. The .md files print `classify`-based numbers (e.g. B1 closed-book silent errors 94 = 18.8% vs 18.4% in SUMMARY). | low (provenance) |
| M9 | SUMMARY L112 "gold answer appears in the passage for only 42% (search) / 68% (oracle)"; "when evidence lacks the answer B1 answers wrongly on 24 (14%)" | | Reproduces with the stated matcher (127/300, 170/251; 100/127; 147/173 abstain; 24 wrong). But the matcher misses whole classes (see section 5), so these are wrong in substance: see "open-world numbers under better graders" below. | **high (see §5)** |

### Open-world numbers: three graders side by side (all recomputed)
`strict` = project `matches`; `lenient` = token containment (SUMMARY text mentions it but never prints it); `lenient2` = added after the first retrieval results (union with the other two; its docstring says "extra column"). "wrong" = attempted and not correct under that grader (hi = strict, lo = lenient or lenient2). "att" counts status=answer with non-empty answer.

Closed-book, n=500 (SUMMARY: 100/4.4/95.6/4.4 ; 20.2/1.8/18.4/8.9 ; 2.4/0.6/1.8/25.0 all reproduce)

| system | att | correct strict / lenient / lenient2 | wrong hi / lo(len) / lo(len2) | precision strict / len2 |
|---|---|---|---|---|
| B0_raw | 100.0 | 4.4 / 4.8 / 5.8 | 95.6 / 95.2 / 94.2 | 4.4 / 5.8 |
| B1_abstain | 20.2 | 1.8 / 1.8 / 2.2 | 18.4 / 18.4 / 18.0 | 8.9 / 10.9 |
| VKG_v2 | 2.4 | 0.6 / 0.6 / 0.8 | 1.8 / 1.8 / 1.6 | 25.0 / 33.3 |

Search retrieval, n=300 (SUMMARY reproduces for the strict column)

| system | att | correct strict / lenient / lenient2 | wrong hi / lo(len) / lo(len2) | precision strict / len2 |
|---|---|---|---|---|
| B0_raw | 90.3 | 35.3 / 36.7 / 41.3 | 55.0 / 53.7 / 49.0 | 39.1 / 45.8 |
| B1_abstain | 45.0 | 32.7 / 34.0 / 38.7 | 12.3 / 11.0 / 6.3 | 72.6 / 85.9 |
| B2_strict | 43.7 | 32.0 / 33.3 / 38.0 | 11.7 / 10.3 / 5.7 | 73.3 / 87.0 |
| VKG_v2 | 39.0 | 29.0 / 30.3 / 34.3 | 10.0 / 8.7 / 4.7 | 74.4 / 88.0 |

Oracle pages, n=251

| system | att | correct strict / lenient / lenient2 | wrong hi / lo(len) / lo(len2) | precision strict / len2 |
|---|---|---|---|---|
| B0_raw | 95.6 | 60.2 / 64.9 / 74.1 | 35.5 / 30.7 / 21.5 | 62.9 / 77.5 |
| B1_abstain | 78.5 | 56.6 / 61.4 / 69.3 | 21.9 / 17.1 / 9.2 | 72.1 / 88.3 |
| B2_strict | 76.1 | 55.0 / 59.4 / 67.3 | 21.1 / 16.7 / 8.8 | 72.3 / 88.5 |
| VKG_v2 | 67.3 | 49.4 / 54.2 / 60.2 | 17.9 / 13.1 / 7.2 | 73.4 / 89.3 |

Closed-book on the same 300: B1 correct 1.0 / 1.0 / 1.7, wrong 19.7 / 19.7 / 19.0; VKG_v2 0.7 / 0.7 / 1.0, wrong 2.3 / 2.3 / 2.0. Search on the 251 oracle questions: B1 strict-correct 37.8 (lenient2 45.0).

Adding two further grader repairs of my own (`a10_fixedgrader.py`: strip accents and punctuation before token matching, which fixes golds ending in "." and hyphen/space variants, and drop the parenthetical "(acceptable range ...)" from the gold string) gives, for correct (strict-type) / wrong-hi, and then correct / wrong-lo with lenient+lenient2 added:

| condition | system | correct hi-grader | wrong hi | correct incl. len+len2 | wrong lo |
|---|---|---|---|---|---|
| search n=300 | B0_raw | 39.3 | 51.0 | 43.0 | 47.3 |
| | B1_abstain | 37.0 | 8.0 | 40.3 | 4.7 |
| | B2_strict | 36.7 | 7.0 | 39.7 | 4.0 |
| | VKG_v2 | 32.7 | 6.3 | 36.0 | 3.0 |
| oracle n=251 | B0_raw | 68.5 | 27.1 | 77.7 | 17.9 |
| | B1_abstain | 64.9 | 13.5 | 72.9 | 5.6 |
| | B2_strict | 62.5 | 13.5 | 70.5 | 5.6 |
| | VKG_v2 | 56.2 | 11.2 | 63.3 | 4.0 |
| closed-book n=500 | B1_abstain | 2.0 | 18.2 | 2.2 | 18.0 |

Evidence coverage with the repaired matchers: search 149/300 = 49.7% (SUMMARY 42%), oracle 200/251 = 79.7% (SUMMARY 68%). Split by that coverage, B1 on "evidence lacks the answer" (n=151 search): 143 abstain, 2 correct, **6 wrong (4%)**, against SUMMARY's "24 wrong (14%)"; on "evidence has the answer" (n=149): 119 correct, 22 abstain, 8 wrong. Even with the unrepaired split, 13 of the 24 "wrong when evidence lacks" are right under `lenient2` (15 correct of 173).

---------------------------------------------------------------------------------------------------

## 2. Prediction re-score (from raw files, wording of docs/FREEZE.md)

| P | wording (short) | recomputed | verdict | wording / interpretation flags |
|---|---|---|---|---|
| P1 | squad2 held-out: VKG_v2 strict SER lower than B1 by >= 3 pts | B1 12.0, VKG 5.7: -6.3 [-9.3,-3.7] | pass | "strict SER" is not defined in FREEZE; SUMMARY defines it (silent + false conflict, all items). Under plain SER the gap is -5.0, still pass. |
| P2 | yield drop <= 8 pts | 94.7 -> 86.0 = -8.7 [-12.8,-4.6] | **fail** (correctly reported) | |
| P3 | faitheval: VKG_v2 strict SER lower than B1 | 17.0 -> 9.3 | pass | no yield exists on FaithEval, so this cannot separate "better evidence use" from "abstains more" |
| P4 | synthetic: gains concentrate in formal | 50 -> 10 errors, 38 of the 40 removed are formal (38 -> 0) | pass | "concentrate" is undefined; 95% is clearly concentrated. Held-out synthetic was run with the buggy closed_conf generator; the 38/40 split is unaffected. |
| P5 | VKG_v2x (smaller checker) is no better than VKG_v2 | strict SER worse on SQuAD2 (9.0 vs 5.7, paired +3.3 [1.0,5.7]) and FaithEval (13.7 vs 9.3, +4.3 [2.3,6.7]); equal on synthetic (3.3 vs 3.3) | pass on SER only | "better" is ambiguous. On SQuAD2 yield VKG_v2x is **better** (91.3 vs 86.0, paired +5.3 [1.3,9.6]). SUMMARY says "worse on both real suites" without mentioning that it wins on yield, so v2x is a different trade-off point, not dominated. |
| (unnumbered) | residual SQuAD2 unanswerable error stays >= 10% | 10.0% (15/150) | pass, exactly on the boundary | |
| P6 | B2 lowers strict SER vs B1 but loses yield; VKG_v2 not dominated by B2 | B2 7.7 / yield 88.0; VKG 8.3 / 90.7; B1 14.7 / 96.7 | pass (literal) | B2 has SER <= VKG's but yield < VKG's, so not dominated. Paired VKG-B2: SER +0.7 [-2.3,+3.7], yield +2.7 [-1.4,+7.1]: both inside noise, as SUMMARY says. |
| P7 | FaithEval: VKG_v2 strict SER lower than B2 by < 3 pts | -1.7 [-5.0 or -4.7, +1.3] | pass | Ambiguous: "lower by less than 3" is also satisfied by a lower point estimate whose CI includes 0 (as here), and arguably by VKG being higher. |
| P8 | synthetic: VKG_v2 SER lower than B2 by >= 10 pts | 14.0 vs 0.3 = -13.7 [-18.0,-10.0] | pass | B2 and B1 rows are identical on all 300 items (B2 only changes passage prompts and, with the fixed generator, closed items are at ceiling), so this is a B1 comparison. Formal 41/60 -> 1/60 is the whole gap. |
| P9 (new, freeze 4) | with well-posed conflicts, VKG_v2 qualifies >= 90% of the 30, B1 >= 80% | B1 30/30, B2 30/30, VKG 30/30 | pass, uninformative | **Not a blind prediction.** It was written after the author had inspected seed-1001 results (13 well-posed items: VKG 13/13, B1 12/13 = 92%), so the thresholds were set from the same generator family's held-out outcome. Original P9 (>= 20% left silent, would have failed) was dropped, with disclosure. |
| P10 | B0 closed-book attempts >= 95% and strict-wrong >= 60% | 100% and 95.6% | pass | |
| P11 | B1 lowers strict-wrong vs B0 by >= 15 pts (CI excludes 0), strict-correct drops <= 8 | -77.2 [-80.8,-73.4]; correct -2.6 | pass | |
| P12 | VKG_v2 lowers strict-wrong vs B1 by >= 3, precision higher, strict-correct count falls | -16.6 [-19.8,-13.4]; precision 25.0% (3/12) vs 8.9% (9/101); correct 9 -> 3 | pass, point estimates only | "precision higher" is not significant: Fisher exact p = 0.12, Clopper-Pearson 95% for VKG [5.5%, 57.2%] overlaps B1 [4.2%, 16.2%]. |
| P13 | even the best system answers wrongly on >= 25% of attempts (strict bound) | B1 92/101 = 91%, VKG_v2 9/12 = 75% | pass | "best system" is undefined; passes for either. Under my repaired grader VKG is 8/12 = 67%. |
| P14 | search B1 strict-correct >= 20% of all | 32.7% | pass | (lenient2: 38.7%) |
| P15 | oracle B1 strict-correct exceeds search B1 by >= 8 pts | matched 251: 56.6 vs 37.8 = +18.8 | pass | Denominators differ in the SUMMARY tables (n=251 vs n=300); the matched comparison is only in FREEZE. Gap persists under every grader (lenient2: 69.3 vs 45.0). Also: oracle is an upper bound for *retrieval*, not for answers (gold answer absent from 20% of oracle pages even with repaired matcher), so "retrieval, not reading, is the bottleneck" is partly confounded by page-selection/cleaner. |
| P16 | search: B0 strict-wrong >= 10%; each of B1, B2, VKG_v2 lowers it by >= 3 pts (CI excludes 0) | B0 55.0; -42.7 [-48.3,-37.3]; -43.3 [-49.0,-38.0]; -45.0 [-50.7,-39.3] | pass | trivially satisfied (B0 has no abstain option). |
| P17 | search: VKG_v2 minus B2 within +-3 on strict-wrong, +-5 on strict-correct | -1.7 [-3.3,-0.3]; -3.0 [-5.0,-1.3] | pass as written | The bands apply to point estimates only. Under the repaired grader the wrong-answer difference is -0.7 [-2.0,+0.7] (CI includes 0) and correct -4.0 [-6.3,-2.0], so the SUMMARY sentence "removes a few more wrong answers than a cautious prompt" is grader-dependent. |
| P18 | search: every system answers wrongly on >= 3% of all (strict bound) | min is VKG_v2 10.0% (search), 17.9% (oracle) | pass | Margin evaporates on lower bounds: lenient2 4.7%, repaired-grader lower bound 3.0% (search). It is a statement about the strict bound only. |

Net: 17 of 18 pass as worded, P2 fails (reported). Weak spots: P5 (partly), P9 (not a blind prediction), P12 (not significant), P17 and P18 (grader-dependent).

---------------------------------------------------------------------------------------------------

## 3. Train/test hygiene

Identifiers regenerated from `tasks.*` and compared with the ids in the jsonl files (they match exactly for every seed).

| suite | pair | overlap (ids) | note |
|---|---|---|---|
| SQuAD2 | 0 vs 1000 | 0 | but 47 SQuAD paragraphs are shared; 52 of 300 held-out items share a context paragraph with a dev item (questions differ) |
| SQuAD2 | 0 vs 2000 | 0 | 58 shared paragraphs, 67 items |
| SQuAD2 | 1000 vs 2000 | **3** (squad_ans-56e16182e3433e1400422e2a, squad_ans-5729fc3d1d0469140077969d, squad_unans-5a7b359f21c2de001afe9dd2) | matches the 3 admitted in SUMMARY |
| FaithEval | 0 vs 1000 | 0 | 16 identical question texts with different contexts (the dataset itself repeats questions) |
| FaithEval | **0 vs 2000** | **26** (11 unanswerable, 15 inconsistent) | **FREEZE 3/4 says "exclude 0 and 1000". Not true.** |
| FaithEval | **1000 vs 2000** | **22** (7 unanswerable, 15 inconsistent) | |
| synthetic | 0 / 1001 / 2001 | ids are index-based, so id overlap is meaningless; by content: the 30 `open_real` items are byte-identical in every seed (dev, held-out and control share them); 2 `closed_ans` questions coincide between 1001 and 2001 (different passages); everything else is disjoint | |
| SimpleQA | test = first 300 of Random(3000).sample(range(1000),300) | prefix property verified (first 300 of the n=500 sample equals the n=300 sample); the rag ids equal the expected 300; closed-book ids equal the 500 sample | OK |

**FaithEval seed 2000 cause.** The b2ctrl FaithEval run was executed as `--seed 2000 --exclude-seed 1000` (regenerating that command reproduces the 300 ids exactly, and nothing else does). But `tasks.faitheval` only supports one exclusion seed, and `faitheval(150, 1000)` with no exclusion is not the held-out sample (the held-out sample was drawn with seed 0 excluded), and seed 0 was not excluded at all. Result: 48 of 300 (16%) of the seed-2000 items were previously used (26 dev + 22 held-out). Effect on the conclusion: on the 252 clean items B1 20.6, B2 11.9, VKG_v2 10.3 strict SER; VKG minus B2 -1.6 [-5.2,+2.0]; B2 minus B1 -8.7 [-12.7,-5.2]. Same qualitative result, so P7 and the "verifier not shown to beat B2" statement survive, but the freeze text is wrong and the reuse of dev items biases the control slightly toward systems tuned on dev (on the 26 dev-overlap items: B1 15.4, B2 3.8, VKG_v2 3.8).

**SimpleQA dev leakage into the test sample (retriever tuning).** FREEZE 6d says the page-cleaner checks used dev pages "Getty Center, Sam Manekshaw, Horizons (Epcot) (all from the seed-9999 dev sample, not the seed-3000 test sample)". Two of the three pages belong to **test** questions: sqa-3343 ("According to Wikipedia, how many feet above sea level is the Getty Center?") and sqa-323 ("How many years was the attraction Horizons at EPCOT sponsored by General Electric?") are both inside the 300 test ids. The sampling code for "seed 9999" is not stored; if it was `Random(9999).sample(range(1000), 40)` (the pattern used elsewhere), 9 of those 40 dev questions are test questions, including exactly those two (Manekshaw, sqa-854, is not). The cleaner fix for `{{convert|900|ft|m}}` was made after looking at the Getty Center page, i.e. a test question's source page. Effect is small (2/300 items; B1/B2/B0 answer 900 for the Getty item and are graded wrong by the strict grader anyway, VKG_v2 abstains) but it violates the stated protocol, and the "4 empty searches" that triggered the keyword fallback were seen on a dev set that probably overlaps the test set by about 22%. ROADMAP S2 repeats "the seed-9999 dev set" as allowed for tuning, so the overlap should be checked before S2 is run.

Other hygiene facts:
- Code hashes in FREEZE match the files now on disk for systems.py (7f22d4ba), tasks.py (a4753d57, freeze 6), llm.py, metrics.py, run.py (c9786f9d), retrieval.py (85bcccd9, freeze 6e). `grade_open.py` is now 501bc728, not the freeze-5/6 hash e3a839a1 (lenient2 added; disclosed in S3_PROTOCOL, not in FREEZE.md). `grade`/`lenient` outputs reproduce every SUMMARY number, so the SUMMARY tables are unaffected.
- tasks.py/systems.py changed after the freeze-1 held-out runs (freezes 2, 4, 5, 6). The changes (b2_strict, the registry-sentence fix, simpleqa loaders) do not alter SQuAD2/FaithEval item generation; I confirmed regenerated SQuAD2/FaithEval ids and synthetic questions/gold match the jsonl. The held-out synthetic seed 1001 run used the buggy generator (disclosed).
- LLM cache keys ignore the model digest/quantization; VKG_v2's first call and B1's call share one cache entry (same prompt, T=0, seed 0), so B1 and VKG_v2 rows are paired by construction. That makes paired CIs tighter but is legitimate.

---------------------------------------------------------------------------------------------------

## 4. Circularity

- Gold labels: no LLM output enters any gold. Synthetic gold is generator code (but see ill-posed items below), SQuAD2/FaithEval/SimpleQA gold is dataset-supplied. `systems.py` never reads `item.gold` or `item.meta` (grep: no "gold" in the file). Graders are string functions (`matches`, `lenient`, `lenient2`, status-based classification). No LLM judge in any headline number. OK.
- `results/MANUAL_CHECK_faitheval_residuals.md` is a one-rater (the author, an LLM) labelling with no gold. It is correctly labelled "not a statistic", but SUMMARY uses it to say "about 9 look true ... the false-claim rate is lower than the SER". That sentence rests on an LLM's unaudited world knowledge; treat it as anecdote (n=19, one rater).
- Checker independence: `vkg_v2` uses the generating model as its own support checker (acknowledged); the checker never sees gold.
- Retrieval, search mode: the query is built from the question text only (`keywords(question)`), ranking is BM25 against the question; `urls`/`answer` are only read in oracle mode. No gold leak in code. The leakage is process-level: the retriever's design was tuned against dev items that include two test questions (see §3).
- Oracle mode uses the dataset's gold source URLs. It is labelled "upper bound, not deployable" in docs/FREEZE.md (freeze 6) and in the `tasks.simpleqa_rag` docstring, but **not** in results/SUMMARY.md (the oracle table is only titled "oracle pages", with the sentence "the dataset's own Wikipedia source pages") nor in the oracle .md meta ("oracle Wikipedia source pages"). The SUMMARY text "even with the oracle pages" treats it as a ceiling; I recommend adding "upper bound, uses gold source URLs, not deployable" in the SUMMARY table heading and the run meta. It is also not a true ceiling: 20% of oracle passages still lack the answer under the repaired matcher (cleaner flattening, truncation to 900 words, live pages differing from the 2025 gold), and 49 of the 300 questions (16%) have no Wikipedia source, so oracle numbers are on a self-selected 251 (the n=300 search table and n=251 oracle table sit side by side in SUMMARY with different denominators; the matched-251 search numbers are only in FREEZE).
- `analyze_rag` coverage uses gold by design (analysis only, not in any system input). Fine.
- Dev decision rules (S2) use gold-in-passage on dev ids only; fine as long as the dev/test overlap issue above is checked.
- Bias that is not circularity but looks similar: all three grader repairs are applied after seeing results (lenient2 was added after the first retrieval results). It is reported as an extra column, which is acceptable, but the graders were never validated on a sample larger than 24 B0 closed-book answers, which is the condition where grader misses are rarest (95% of those answers are wrong anyway).

---------------------------------------------------------------------------------------------------

## 5. Metric and grader bugs

### 5.1 String graders mark a large share of correct SimpleQA answers wrong (material)
Both `matches`/`norm` and `lenient` keep "." in tokens and require the gold string to appear verbatim. Consequences, all confirmed on the rows:
1. Gold ending in a full stop (12 of 300 test items, 10 of the 251 oracle items, 19 of 500) never matches an answer without the period: sqa-3038 "Washington High School.", sqa-3171 "Los Feliz Grammar School.", sqa-1366 "University of Southern California.", sqa-2710 "Maternal uncle.", sqa-1025, sqa-4226, sqa-1164, sqa-39 "Gvulot." (answer "Gvulot"/"Kibbutz Gvulot"), sqa-538, sqa-342. Strict and lenient both fail (lenient token "school." != "school"), and lenient2 only rescues numeric golds.
2. "(acceptable range: ...)" golds (32 of 300, 27 of 251, 52 of 500: about 10% of the benchmark) can only match if the model copies the parenthetical; only lenient2 repairs them.
3. Hyphen/space variants (sqa-2449 "Soldani-Benzi" vs "Soldani Benzi"), number words (sqa-2916, 3998, 2799: "three", "four", "two") and date reorderings (lenient only).
4. Trailing "km"/"m" units are handled only by lenient.
Net effect on the oracle table: B1 strict-correct 56.6% but 64.9% with punctuation/range repaired and 72.9% with all lenient variants; strict-wrong 21.9% becomes 13.5% (hi) or 5.6% (lo). In the 30-row random oracle sample below, 7 correct answers were marked wrong.
FREEZE 5 lists the gaps as "acceptable range" and "number words" and estimates the effect at 0.4 pts, which is true only for B0 closed-book; with retrieval the effect is 4-9 pts. SUMMARY's phrase "strict-wrong (all questions)" should be read as an upper bound that is badly loose here (it was not labelled as one next to the headline number "10-12% of all questions still get a wrong answer").
The lenient bounds are not clean lower bounds either:
- `lenient` ignores single-letter tokens: gold "F Major" accepts "G major" (sqa-3296, B0 closed-book).
- `lenient2` compares only the numbers in the gold: gold "Sony Alpha 1" accepts "Canon EOS-1D X" (sqa-788, B0 closed-book, counted correct); gold "Zanele Muholi: African Women Photographers #1" accepts the partial title; gold 137 (range 135-139) accepts the hedge "more than 137" (sqa-2608). So lenient2 over-credits a little.

### 5.2 B0_raw abstention detection by regex inflates B0 error rates
`b0_raw` marks an answer as unknown only if `UNKNOWN_RE` matches. Answers such as "None", "nothing", "The passage does not provide this information", "The Battle of Calmarith did not take place; it is a fictional event" stay `status=answer` and become `silent_error`.
- Held-out synthetic, B0_raw `open_fict`: 60 silent errors, of which 54 explicitly say the entity does not exist or is fictional. Overall synthetic B0 SER 49.3% includes ~18 pts of this artefact (about 31% after removing them; the same on seed 0: 48 of 58). 
- Held-out SQuAD2, B0_raw: 15 of 140 silent errors are "None"/"nothing"/"passage does not provide"; B0 "silent error on unanswerable" 90.7% would be about 80.7% if those count as abstentions.
- SimpleQA retrieval: B0_raw hedges counted as attempts: 9 (search), 5 (oracle), e.g. sqa-1121 and sqa-2657 in the oracle sample.
B0 is a reference row, not the baseline for any claim, but the B0 numbers in the SUMMARY tables and "B0 attempted >=95%" (P10, closed-book only) deserve a footnote.

### 5.3 Answerable items and `conflict`
`classify`: answerable + `conflict` -> `false_conflict`. It is counted in strict SER and not in SER, not in `over_abstain`, and not in yield (not correct). On SQuAD2 there are only 2 such rows (B1 1, VKG_v2x 1 on seed 1000), so this is immaterial there. On the open-world grader, `conflict` is lumped with abstentions (3 rows each in rag/oracle), as FREEZE notes. Abstention is handled consistently as "no silent error" everywhere, with these exceptions: (a) status=answer with empty answer is a silent error in `classify` and an abstention in `grade_open` (2 B1 rows, closed-book); (b) the SQuAD2 table column "silent error on unanswerable" excludes false conflicts while the headline "strict SER" includes them (see M5).

### 5.4 Abstention-for-free and the lack of a yield metric on FaithEval
SER (silent or strict) rewards abstaining, so a system that always says "unknown" scores 0. FaithEval has no answerable items, so VKG_v2's FaithEval SER gain over B1 (-7.7) cannot be told apart from extra abstaining; the only protection is the B2 control (same SER range, no better). On the inconsistent items VKG_v2 qualifies fewer conflicts than B1 (74.7% vs 90.7% on seed 1000; 72.0% vs 90.7% on seed 2000) and converts the rest to `unknown`, which the metric scores as safe. SUMMARY gives the FaithEval "inconsistent" error column but not this drop in conflict detection.

### 5.5 Bootstrap
- `paired_bootstrap_delta` and `grade_open.ci` take the 2.5th and 97.5th percentiles at indices int(0.025*B) = 50 and int(0.975*B) = 1950 of 2000 sorted values (0-indexed 1949 would be the exact 97.5th); the effect is below 0.3 pt. Not a bug that changes any conclusion.
- Resampling unit is the item (id), paired by id across systems; ids are unique per system in all files. FaithEval has duplicate questions and shared contexts across items (16 duplicate question texts between seeds 0 and 1000), SQuAD2 paragraphs are shared; resampling at item level ignores that clustering, so CIs are a little narrow (the code docstring says "cluster = original question", but no clustering is done).
- Different CI implementations are mixed in the write-up (M1-M3).
- `yld` returns NaN for FaithEval and the run reports print `+nan`; harmless.
- Multiplicity: ~18 predictions and many CIs, none corrected; nothing near a decision boundary is claimed significant on a single CI, except possibly the VKG-vs-B2 retrieval wrong-answer difference, which does not survive the repaired grader (§2, P17).

### 5.6 Synthetic generator
Reconstructing the old bug: the antecedent of "it" is the question's organization in 17/30 (seed 0), 13/30 (seed 1001) and 16/30 (seed 2001) closed_conf items, matching FREEZE 4. With the fix, all three systems qualify 30/30, so the family is at ceiling and cannot separate systems. The 30 `open_real` items are the same in every seed, so dev and held-out share 10% of the synthetic yield denominator; B1 silent error on open_real-24 ("How many squares are on a chessboard?" -> "204") repeats in both runs. One real VKG formal error is a rounding (`int(...)` on 85% of 5612, gold 4770.2, answer 4770, formal-21 seed 2001); it is a genuine error, not a grader miss.

### 5.7 Smaller grader issues on answerable SQuAD2 items (yield slightly understated)
Gold "the Treaty on the Functioning of the European Union" vs answer "Treaty on the Functioning of the European Union" (squad_ans-5726c002708984140094d073, seed 2000, all of B1/B2/VKG graded silent_error); "silica" vs gold ["oxides of silicon","silicon"] (squad_ans-571a53d410f8ca1400304fe6, seed 1000, B1/VKG/v2x). Paired across systems, so negligible for comparisons.

---------------------------------------------------------------------------------------------------

## 6. Spot check (30 random rows per suite, seeded shuffle over all systems; `a8_spot.py`)

| suite | rows | misgraded | details |
|---|---|---|---|
| heldout SQuAD2 (seed 11) | 30 | 0 | One B0 "None" answer (…cf76001a686e5f, "Which committees do not reflect the balance of parties across Parliament?") counted as silent error; this is the B0 regex artefact (§5.2). All answerable "correct"/unanswerable "silent_error" rows were consistent with gold. Extra rows found by targeted scan: squad_ans-5726c002708984140094d073 (b2ctrl) and squad_ans-571a53d410f8ca1400304fe6 (heldout) graded wrong though correct. |
| heldout FaithEval (seed 12) | 30 | 0 detected | status-only grading (no gold text); I could not verify unanswerable-vs-answerable labels without the passages (not stored in the jsonl). Several "silent error" answers (Indianapolis, The Carpenters, 1789, Toby Gad, XK) look factually right from general knowledge, consistent with the author's own note that FaithEval counts them as unfaithful rather than false. |
| heldout synthetic (seed 13) | 30 | 0 | Three B0_raw `open_fict` rows (open_fict-25, -45, -54) say the entity does not exist yet are scored silent_error (§5.2). formal-45 VKG_v2 `over_abstain` (35% of 7796, code samples disagreed) is a real abstention. |
| SimpleQA closed-book (seed 5) | 30 | 0 | B1 sqa-1018 "20 June 1900" vs "June 14, 1900" and B0 rows are truly wrong; sqa-646 (B1 over-abstain) fine. |
| SimpleQA search (seed 6) | 30 | 2 | sqa-2449 (B0/B1/B2/VKG: "Soldani Benzi" vs "Soldani-Benzi", correct answer marked wrong); sqa-2662 (B1 "1" vs gold "1 km": strict wrong, lenient correct); sqa-3017 (B0 "not mentioned") and sqa-8/-598/-2503 etc. are right. |
| SimpleQA oracle (seed 8) | 30 | **7** | correct answers marked wrong by the strict grader: sqa-39 (VKG_v2 "Gvulot" vs "Gvulot."), sqa-2506 (VKG_v2 "105" vs "105 km (range)"), sqa-646 (VKG_v2 "December 17, 2015" vs "17 December 2015"), sqa-2551 (B1 "175" vs range), sqa-1174 (VKG_v2 "121" vs range), sqa-3998 (B2 "four" vs "4"), sqa-2916 (VKG_v2 "three" vs "3"). Two B0 rows, sqa-1121 and sqa-2657, say the text does not contain the information but are counted as attempts. |

Total across the 180 spot-checked rows: 9 gradings I would overturn (all in the two SimpleQA retrieval runs), plus 6 B0 rows whose answer text is a refusal or non-answer (3 synthetic, 2 oracle, 1 SQuAD2) that the regex counted as answers.

---------------------------------------------------------------------------------------------------

## 7. Overall confidence per headline claim

| # | claim (SUMMARY.md) | verdict | reason |
|---|---|---|---|
| H1 | Held-out: VKG_v2 lowers strict SER vs B1 on SQuAD2 (-6.3) and FaithEval (-7.7) | **HOLDS** | numbers and CIs reproduce exactly; frozen code; disjoint from dev by id |
| H2 | The SQuAD2 gain costs yield (-8.7, P2 fails) | **HOLDS** | reproduces; correctly reported as a fail |
| H3 | The verifier is not shown to beat one cautious prompt on SQuAD2/FaithEval ("adds nothing measurable") | **HOLDS** (as "not shown"), with a power caveat | VKG-B2 CIs are about +-3 pts on n=300, so they cannot exclude a 2-3 pt effect; "adds nothing" should read "not distinguishable". FaithEval control reused 48 earlier items (conclusion unchanged on the 252 clean ones). |
| H4 | The attributable gain is code execution on formal tasks (41/60 -> 1/60) | **HOLDS** | reproduces; but it is a comparison of tool use vs no tool, which SUMMARY already says |
| H5 | Synthetic held-out SER 16.7 -> 3.3, "formal 63.3 -> 0.0" | **WEAKENED** | formal part reproduces; the overall synthetic SER is biased by the generator bug (disclosed). All 10 VKG_v2 residual errors are on ill-posed items. B0 synthetic row inflated by regex artefact (54 of 60 open_fict "errors" are refusals). |
| H6 | Closed-book SimpleQA: B0 correct ~4.4%, B1 wrong 18.4%, VKG_v2 refuses 97.6% with yield 0.6% | **HOLDS** | all reproduce; the repaired grader moves correct by <= 1 pt in this condition |
| H7 | "Its stated certainty carries almost no information" (precision 8.9% vs 4.4%) | **WEAKENED** | B1's attempted set has a 2x lift over the base rate (9/101 vs 22/500), VKG_v2's 3/12 = 25% (CI 5-57%, p=0.12 vs B1). Small and imprecise, but not "almost none". |
| H8 | Retrieval is a large gain (B1 correct 1.0% -> 32.7%; wrong 19.7% -> 12.3%) | **HOLDS** (understated) | the gain is larger under repaired graders (correct 37-40%, wrong 5-8%) |
| H9 | Evidence coverage is the limit: answer in passage for 42% (search) / 68% (oracle) | **WEAKENED** | with repaired matchers 50% / 80%. Direction survives (half the questions have no usable evidence), the numbers are 8-12 pts too low. |
| H10 | "When the evidence lacks the answer, B1 abstains on 85% and answers wrongly on 14%" | **WRONG as stated** | strict-grader artefact. Under the project's own `lenient2` 13 of the 24 are correct; under repaired coverage and graders B1 abstains on 143/151 (95%) and is wrong on 6 (4%). SUMMARY itself says the 14% "overstates ... by an amount I have not measured"; it is roughly a factor of 3. |
| H11 | "10-12% of all questions still get a wrong answer under the best retrieval system" | **WEAKENED** | 10.0-12.3% reproduces under strict grading, but is 6.3-8.0% (hi) and 3.0-4.7% (lo) after grader repair |
| H12 | VKG_v2 "removes a few more wrong answers than a cautious prompt but costs about twice as many correct ones" (retrieval) | **WEAKENED** | reproduces under strict (-1.7 wrong, -3.0 correct); under the repaired grader wrong -0.7 [-2.0,+0.7] (not significant) and correct -4.0 [-6.3,-2.0]. Safer reading: the verifier costs correct answers and has no demonstrated wrong-answer benefit over B2. |
| H13 | Oracle table (B1 56.6% correct, 21.9% wrong; VKG 17.9% wrong) | **WEAKENED** | reproduces as strict; strict-wrong is overstated by ~8 pts, and the table is not labelled as using gold source URLs / an upper bound in SUMMARY |
| H14 | Hygiene: held-out and control samples are disjoint from dev (FaithEval seed 2000 excludes 0 and 1000) | **WRONG** for FaithEval seed 2000 (26 + 22 reused items); SQuAD2 and SimpleQA test sampling **HOLD** | see §3. Retriever cleaner fix used two test-question pages as "dev" pages (small effect, protocol violation). |
| H15 | Predictions P1-P18 scored honestly (only P2 fails) | **HOLDS**, with flags | all reproduce; P5 passes on SER only (v2x wins SQuAD2 yield), P9 is post hoc, P12 precision difference is not significant, P17/P18 are grader-dependent |
| H16 | "Every number is read from the named file"; FREEZE hashes | **WEAKENED** | SimpleQA tables are not in any named file (grade_open output was not saved); grade_open.py hash differs from freeze; three CI endpoints (M1-M3) do not reproduce exactly |

### Suggested fixes for the author (not applied)
1. Fix the graders before reporting any retrieval number: strip trailing punctuation and accents, treat hyphen as space, compare the gold's text outside the parenthetical, parse "acceptable range", map number words; apply to all systems; re-state coverage, P14-P18 and §"Where the limit is". Report strict/repaired side by side. Validate the new grader on >= 100 rows read by eye.
2. Label the oracle condition as an upper bound that uses gold source URLs in SUMMARY and in the run meta; put the matched-251 search numbers beside it.
3. Correct FREEZE 3/4 (FaithEval seed 2000 reuses 26 dev and 22 held-out items) or rerun with a real multi-seed exclusion; give the S2 and S3 dev sets an explicit stored id list and test it against the 300 test ids before use (the seed-9999 sample appears to overlap by ~9 items, including Getty Center and Horizons).
4. Make `b0_raw` abstention detection consistent (or drop B0 from the headline tables, or add an "refusal in text" flag); same for the 2 empty-answer rows (`classify` vs `grade_open`).
5. Fix M1-M7 (copied CI, mislabelled "answered silently", mixed strict/silent columns, P13/P17 bases) and use one bootstrap implementation.
6. Soften "adds nothing measurable" to "no difference detectable at n=300 (CI +-3 pts)" and "almost no information" to "a 2x lift on a few attempts".
