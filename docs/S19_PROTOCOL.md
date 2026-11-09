# S19 protocol: joint sealed test on FRESH-5 (L2 primary + L1-A co-primary)

**Status: FROZEN 2026-11-07 10:04 (AEST).** Hash list: results/runs/s19/hashes_freeze.txt. Nothing has been run on FRESH-5. Design history: docs/S19_DESIGN.md.

## Common part
- **Test set:** FRESH-5 = all 1,526 remaining original SimpleQA items (official CSV minus SimpleQA Verified minus FRESH-3/4),
  stratum O, order Random(7000). results/runs/fresh5/items.json, SHA-256 d9eec22c1b906ae796dc0377be249229ffec4b64245d6fffaba523cb6396effc
  (vkg/fresh5.py, sealed 2026-11-07 08:42, not inspected). This is the last untouched SimpleQA pool. One run only.
- **Evidence:** web = DuckDuckGo (vkg/websearch.py: question-only query, up to 8 results, 8 pages, one search per 10 s,
  contamination guard: blocked benchmark and code hosts, pages with the question verbatim or mentioning SimpleQA dropped);
  wiki = local FineWiki (Aug 2025) top-5 titles; combo = kept web pages + wiki pages in one 1500-word passage.
  Built by vkg/s17_run.py with VKG_WEB=ddg exactly as for the S19 design rows. Raw DuckDuckGo results and pages were
  prefetched without any model or gold (results/runs/fresh5/prefetch_ddg.py).
  - Rule fixed now: if a DuckDuckGo search keeps failing (for example a bot check, which is never bypassed), vkg/websearch.py
    raises after its retries and the run stops. It is then postponed and resumed later from the caches; no item is skipped
    or dropped from n. A search that succeeds with zero results is valid evidence (empty web passage), as in S14/S15.
- **Models:** Qwen3-4B-Instruct-2507 (HF weights, SHA-256 checked, results/audit2/qwen4b_local_sha256.txt), batched greedy,
  40 new tokens, PLAIN and CAUTIOUS prompts on each passage (vkg/podgen_server.py via vkg/pod.py). Embedder: official HF
  Qwen3-Embedding-0.6B (model.safetensors SHA-256 0437e45c94563b09e13cb7a64478fc406947a93cb34a7e05870fc8dcd48e23fd).
  Phi-4: Ollama digest ac896e5b8b34, cautious prompt on combo, greedy, 40 tokens, num_ctx 24576 (vkg/reader_run.py).
  Judge: grader 6.1, qwen3.8-27b e0a7cdbef002 on Ollama 0.34.4. Everything runs on the user's RTX 5090, the same as the design rows.
- **Grades:** grader 6.1 judge labels (vkg/s14_eval.g6) are produced by vkg/s17_run.py before any scoring. Both scorers then
  run with the judge disabled (OLLAMA_HOST_URL=http://127.0.0.1:9), so every label comes from the stored file.
- **Two primary hypotheses,** each at one-sided 2.5% (Bonferroni): **H1 = L2** for the L2 system (this session),
  **H2 = L1-A** for the tiered system (the Kimi session's section, pasted verbatim below). Everything else is secondary.
- **Gold:** L1-A and all secondary comparisons use gold-relative labels. Only H1's primary endpoint uses blind adjudication.
  The decoy rows on the adjudication sheet check the adjudicator's consistency, and their verdicts are used for nothing else.
- **Order of work:** (1) freeze: hash list written, status set to FROZEN. (2) results/runs/s19/run_test.sh: checks the hashes,
  waits for the FRESH-5 prefetch, takes the GPU lock, generates, judges, runs Phi-4, unloads, releases the lock, re-checks hashes.
  (3) `python -B -m vkg.s19_eval score` (H1 raw + blind sheet) and `tiered.py --s19 --test` (H2). (4) The user fills the sheet
  without the key. (5) `python -B -m vkg.s19_eval final`. (6) Write results/runs/s19/S19_RESULT.md, failures included.

## H1: L2 (this session)
- **System (frozen):** release the 4B's max-support candidate (vkg/s17_eval.cand) only if:
  (i) the L3 gate V1-V4 (vkg/l3_verify) plus the checks V2' whole numbers, V3' VERSION and year-and-month types, V5 unit equals
  the counted noun (vkg/l3_checks2.release2) find a verbatim, typed, period-consistent span in a hash-pinned FineWiki page;
  (ii) all 3 evidence sources support it (support 3); (iii) Phi-4's cautious combo answer agrees with it (vkg.s12_run.agree).
  Otherwise abstain.
- **Rule:** k = graded-wrong releases; E = ceil(k / (1 - 0.0082)) (grader false-credit correction, as S18); pass iff the
  Clopper-Pearson one-sided 97.5% upper bound of E / 1526 is below 1% **and** coverage is at least 35%. At n = 1526: **k ≤ 6**.
- **Primary endpoint: k after blind adjudication.** vkg/s19_eval.py score writes a sheet with every graded-wrong release plus
  twice as many decoys (graded-wrong combo_plain answers on items the system did not release, and graded-correct system
  releases; seed 19), shuffled, showing only question, gold and answer. The key is in a separate file. The user, without the
  key, judges each row against the question and primary sources: **gold wrong / answer wrong / both acceptable / cannot tell**.
  Only "gold wrong" and "both acceptable" remove an error; "cannot tell" keeps it. Hidden errors among graded-correct
  releases stay covered by the false-credit correction. Decoy verdicts are reported (lenient on decoys too = consistent rubric).
- **Secondary endpoint:** the same rule on gold-relative k, always reported next to the primary.
- **Design evidence:**
  | data | coverage | errors | SER |
  |---|---|---|---|
  | S19 DEV, DuckDuckGo evidence (n = 300) | 46.0% | 1 | 0.33% |
  | S19 FRESH, DuckDuckGo evidence (n = 200) | 41.5% | 2 | 1.00% |
  | S18 sets, Serper evidence (n = 2000; post hoc, components chosen on these errors) | 36.7% | 9 | 0.45% |
  Of the 3 design errors, 2 are A2 (span answers something else) and 1 is a probable gold dispute. Of the 9 S18 errors, 4 are
  gold or strict-grading disputes.
- **Predictions (priors before unsealing):**
  | | prediction | prior |
  |---|---|---|
  | P1 | H1 met (adjudicated k ≤ 6, coverage ≥ 35%) | about 60% |
  | P2 | secondary met (gold-relative k ≤ 6) | about 35% |
  | P3 | coverage ≥ 35% | about 85% |
  | P4 | adjudication removes at least 1 system error | about 80% |
  | P5 | at most 1 in 10 decoy_system_correct rows judged "answer wrong" (rubric applied consistently) | about 80% |
  Reasoning: a gold-relative rate of about 0.45-0.6% (design) gives P(k ≤ 6) of about 0.3-0.45; if adjudication removes the
  gold-dispute share (about 40% of errors in S18), the rate is about 0.3%, and P(k ≤ 6) is about 0.8. Stratum O only and
  selection optimism pull it down; hence about 60%.
- **What a result means:** a pass gives L2 for this system on SimpleQA-original questions under adjudicated gold, with the
  L3 theorem holding for every release. A fail is reported as a fail, with the error classes (A1/A2/A3/gold); no post-hoc
  variant is scored as a confirmation.

## H2: L1-A, tiered answering (the Kimi session; pasted verbatim below)
Source: E:\Models\halluc_runs\PREREG_TIERED.md, SHA-256 198708265be2e04dd5c8449daf14881608b1a0d2323804ececd7651b20457573; scorer E:\Models\halluc_runs	iered.py, SHA-256 9cfb2d74e8b0e97220b860c16cf2442c1b822e484448b1bc9931322608a459b5 (run on FRESH-5 as `tiered.py --s19 --test`, judge disabled). The text between the two rules is the file, unchanged.

---

# Pre-registration section: tiered answering (L1-A), for the joint S19 protocol

**Status: FINAL**, numbers from the S19 DEV/FRESH rerun on DuckDuckGo + FineWiki evidence
(`tiered.py --s19`, run with the judge disabled, so every label came from cache; output
`TIERED_S19.md`). The evaluation session pastes this section verbatim into the joint protocol
and hashes `E:\Models\halluc_runs\tiered.py` together with the files it imports.

## System (frozen)

For each question, using the S19 evidence (DuckDuckGo web, local FineWiki, and their combined
passage, built exactly as for S19 DEV/FRESH by `vkg/s17_run.py` with `VKG_WEB=ddg`), with the
frozen prompts and greedy decoding:

1. **Tier 1, the L2 system:** release the 4B's max-support candidate if all of the following hold:
   - the L3 gate V1–V5 releases it (`vkg.l3_checks2.release2`);
   - it has support from all 3 sources (G3);
   - Phi-4 (cautious prompt, combo evidence) answers and agrees with it (`vkg.s12_run.agree`).
2. **Tier 2:** otherwise, answer with the 4B's cautious combo answer if both it and Phi-4's
   cautious combo answer are non-abstentions and agree (`vkg.s12_run.agree`).
3. **Tier 3:** otherwise, "I don't know".

**Code:**
- `tiered.py --s19`, function `system`. No parameter is tuned after this freeze.
- Phi-4: Ollama build digest ac896e5b8b34, `num_ctx` 24576, greedy, at most 40 new tokens.
- The 4B: as in S17/S19.

## Hypothesis (primary, L1-A)

**Claim:** on FRESH-5 (all 1,526 items, sealed), the tiered system meets L1-A against
`wiki_plain` (4B plain on the Wikipedia passage). It is scored gold-relative, without
adjudication, for both systems. Each criterion is tested with a one-sided paired bootstrap at
**2.5%** (Bonferroni split with L2), 10000 draws, seed 0:
- `tiered.py`'s `lo_hi975`: the same procedure as `vkg.s17_eval.lo_hi`, but with bounds bs[250]
  and bs[9749] instead of S15's 5% bounds;
- the test is scored with `tiered.py --s19 --test`. It reads only FRESH-5
  (`results/runs/s19/fresh5_outputs.jsonl`, plus
  `readers/s19fresh5_combo_cautious_phi4.jsonl`), asserts n = 1526, and writes
  `TIERED_S19_FRESH5.md`.

The criteria:
- (a) the upper bound of mean(e − 0.5·e_base) < 0, i.e. SER at most half of `wiki_plain`'s;
- (b) correct diff ≥ 0 (point estimate) and its lower bound > −0.03;
- (c) coverage diff ≥ −0.03.

**Scope, stated plainly:**
- **This is not an equal-budget comparison.** The tiered system uses three evidence sources,
  several 4B generations and a Phi-4 generation per item; `wiki_plain` uses one source and one
  generation.
- The equal-budget comparisons are reported as secondary and are expected to fail:
  - L1-B single pass, against `combo_plain`;
  - L1-B equal generation, against `MSany`.
- Also reported as secondary: the descriptive comparison against the 4B cautious combo
  answer alone.

## Expected results and prior (stated before unsealing)

**Design numbers** (S19 evidence; coverage / correct / SER):

| set | tiered | tier 1 alone | `wiki_plain` | `combo_plain` | 4B cautious combo |
|---|---|---|---|---|---|
| DEV (n=300) | 81.0 / 78.7 / 2.33 | 46.0 / 45.7 / 0.33 | 67.3 / 56.7 / 10.67 | 92.3 / 84.7 / 7.67 | 86.0 / 82.3 / 3.67 |
| FRESH (n=200) | 79.0 / 77.0 / 2.00 | 41.5 / 40.5 / 1.00 | 64.0 / 55.5 / 8.50 | 90.5 / 84.0 / 6.50 | 83.5 / 80.0 / 3.50 |

- **Tier counts:** DEV 138 from tier 1, 105 from tier 2, 57 abstentions. FRESH 83, 75 and 42.
- **L1-A against `wiki_plain`,** with verdicts at the one-sided **2.5%** bounds used for the
  test:
  - DEV: MET. (a) upper −0.0067, (b) +0.220 (lower +0.167), (c) +0.137.
  - FRESH: NOT MET, only because (a)'s upper bound is +0.0050 at n=200. (b) and (c) pass by wide
    margins.
- **Secondary comparisons, both sets: NOT MET,** as expected. L1-B against `combo_plain` and
  `MSany` fails (b) and (c), and so does the comparison against the 4B cautious combo answer.
- The earlier Serper-evidence numbers are in `TIERED.md`. S19's DuckDuckGo evidence is clearly
  stronger: the combo baselines rose about 4–5 points in coverage, while `wiki_plain` barely
  moved.

**Expected on FRESH-5:**
- **Tiered SER about 3%,** not 2%. The variant was chosen from about 10 on Serper design rows,
  and S17's DEV → FRESH drop is the precedent.
- **Coverage about 75–80%,** against `wiki_plain` at about 62–65%.

**Power:** resampling the paired S19 design rows to n = 1,526, with criteria at one-sided 2.5%:
- P(L1-A met) = 1.000 from DEV+FRESH pooled;
- **0.990 from FRESH alone**, the more cautious guide.
- Normal-approximation check on the pooled rows: (a) upper −0.0095 (normal) vs −0.0090
  (bootstrap).

**Conditional prior:** power is not the risk; a shift in distribution is.
- **Criterion (c) is no longer the risk:** the coverage diff is +0.14 to +0.15 on both sets,
  far above −0.03.
- **The binding criterion is now (a),** SER at most half of `wiki_plain`'s.
  - Fixed gold errors on the stratum-O originals would add to both e and e_base, and that hurts
    (a). For example, +2 points of gold noise on both: tiered 3 + 2 = 5% vs 0.5 × (8.5 + 2) =
    5.25%, still a pass, but a thin one.
  - The tiered system's SER rising above about 4% would also fail (a).
- **Web and wiki now overlap more,** since both lean on Wikipedia, so tier 1's "all 3 sources
  agree" is a less independent signal than with Serper. Tier 1 alone still made 1 + 2 errors
  in 500.
- **Prior: P(L1-A met) ≈ 0.85.** That is 0.99 power, discounted for selection optimism and for
  possible gold noise and distribution shift on the stratum-O originals.

## Reporting

- **Main table:** coverage, correct, SER and the SER upper bound (Clopper–Pearson 95%) for the
  tiered system, tier 1 alone, `wiki_plain`, `combo_plain`, `MSany` and 4B cautious combo.
- **Tier counts:** releases from tier 1, from tier 2, and abstentions.
- **L1 verdicts:** for each criterion, the estimate, the bound and pass/fail.
- **Failures are reported as failures,** with no post-hoc variants.

---

## Frozen files
results/runs/s19/hashes_freeze.txt (written by results/runs/s19/make_hashes.sh at the freeze): every module of the vkg package, the FRESH-5 items, two_reader.py, run_test.sh, this protocol, the embedder weights, tiered.py and PREREG_TIERED.md. run_test.sh refuses to run if any of them changed, and re-checks them after the run.
