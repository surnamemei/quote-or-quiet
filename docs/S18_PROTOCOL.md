# S18 protocol (DRAFT, not yet frozen): sealed L2 test of the L3-gated system

Drafted 2026-11-06, about 21:30, before any S18 output exists. **It supersedes S17**, which was never run on FRESH-3 (see docs/S17_PROTOCOL.md: the FRESH check showed the S17 design could not meet L2).

## Question
Does the L3-gated system keep the silent error rate below 1%, at 95% confidence, while answering at least a pre-specified share of questions? (target.txt, L2)

## Test data (sealed, never inspected)
- **FRESH-3:** 1000 items (200 unused SimpleQA Verified + 800 original SimpleQA). results/runs/fresh3/items.json, SHA-256 f6550e9a4ca9bdcdfbe454b504d6e15691508fa02800a648f2ae66b894dc5b8f.
- **FRESH-4:** 1000 original SimpleQA items, by vkg/fresh4.py: Random(6000) from the 2,526 original items outside Verified and outside FRESH-3. results/runs/fresh4/items.json, SHA-256 e1ca43fc81d4307ddbddf71d7347c34ba687a5e6e07abaf57843a1b937c2cf9a. 1,526 original items remain untouched after this.
- **n = 2000**, the primary analysis set; results are also reported by set and by stratum (V: 200, O: 1800).
- Only counts have been seen. FRESH-3's searches, pages and wiki titles were prefetched with no model or grading. FRESH-4 has not been touched at all.

## System (frozen at freeze time; no change after)
- **Pipeline:** vkg/s17_run.py (three evidence sources: Serper web, local FineWiki, combined). Qwen3-4B answers with the plain and cautious prompts on each source, 6 answers per item.
- **Candidate:** the max-support answer (vkg/s17_eval.cand); s = the number of sources that agree with it.
- **L3 gate:** vkg/l3_verify.release, V1–V4 against the hash-pinned FineWiki index (SHA-256 f9e844af845e2860874d52f51afec9604efb6613ca10e8104fcbc6120be007c4). Evidence documents are the FineWiki titles retrieved for the question.
- **G3 (primary):** release iff the gate accepts and s = 3. **G2 (secondary):** gate accepts and s ≥ 2.
- **Baselines (L1, reported):** wiki_plain, combo_plain, MSany.

## Grading
Grader 6.1, with the judge qwen3.8-27b e0a7cdbef002 on Ollama, local or pod (backend agreement 298/300, results/audit2/pod_judge_check.md). Non-answers are detected by code.

## Primary L2 criterion (vkg/s18_eval.py raw)
G3 meets L2 iff both hold:
1. **Completion floor:** coverage ≥ 35%, fixed now. G3's coverage on DEV/FRESH was 40–44%.
2. **Error bound:** the one-sided 95% upper bound on SER is below 1%. Errors are judged **against the benchmark gold** and corrected for grader false credit, with Bonferroni 2.5% + 2.5%:
   - f_up = 0.0082, the Clopper–Pearson 97.5% upper bound on grader-6 false credit from its blind validation: 1 of 677 truly wrong answers credited (natural rows 1/351; injection, effective 0/326; docs/GRADER6_PROTOCOL.md);
   - k_raw = G3 releases graded wrong; true errors E = ceil(k_raw / (1 − f_up)); the bound is the Clopper–Pearson 97.5% upper bound with E errors in 2000;
   - at n = 2000 this means **k_raw ≤ 10** (E = 11, bound 0.98%); 11 graded-wrong releases fail (1.05%).
- **Assumption:** grader false credit on these answers is no higher than on its validation rows. The injection test (wrong years, numbers, days, swapped answers) supports this, but it remains an assumption.
- **Why the error is relative to gold:** the benchmark's gold is the task's ground truth. A gold audit would only remove errors, so it is not used for the verdict.

## Sensitivity analyses (reported, not the verdict)
- **Gold-adjusted:** a human audits only the graded-wrong G2 releases against primary sources, with verdicts correct / wrong / gold_wrong / unresolvable, using results/runs/s18/audit_sheet.csv (shuffled; no system internals shown). This needs the user, about 10–30 rows. Reported as one-directional.
- **Stratum V only** (cleaner gold, n = 200; too small for L2 on its own, reported descriptively).
- **L3 assumption audit:** the released-but-wrong G3/G2 answers classified as A1 (source wrong), A2 (span answers something else) or A3 (type misparse), giving the end-to-end ε estimate.
- **L1 (secondary):** G2 vs wiki_plain, combo_plain and MSany with the S15 criteria (vkg/s17_eval.py).

## Power, stated in advance
- G3 on DEV + FRESH: 2 graded-wrong in 500 (0.4%), which would mean about 8 in 2000. Then P(k_raw ≤ 10) = 0.82.
- Two forces push the rate up: (a) V4 and the exact-number type were designed after seeing DEV/FRESH errors, so DEV/FRESH are optimistic; (b) 1800 of the 2000 items have noisier original gold, and wrong gold counts against us.
- Expected 10 errors gives P = 0.58; 12 gives 0.35; 16 gives 0.08.

## Predictions
| | prediction | prior |
|---|---|---|
| R1 | **L2 met for G3** (coverage ≥ 35% and k_raw ≤ 10) | about 35% |
| R2 | G3 coverage ≥ 35% | about 85% |
| R3 | G3 raw SER on stratum O > on stratum V | about 70% |
| R4 | most released-but-wrong answers are A2 (span answers something else) | about 75% |
| R5 | the gold audit finds at least one gold error among graded-wrong releases | about 70% |
| R6 | L1-A (G2 vs wiki_plain) met | about 30% |
| R7 | contaminated pages ≤ 5% of fetched pages with text | about 95% |

## Serper budget rule (fixed now; no top-up, by the user's decision)
- The account balance is 999 (checked through the Serper account endpoint, 2026-11-06 21:40). FRESH-3's question searches are all cached; FRESH-4 needs up to 1000 new searches.
- **Rule (in vkg/s17_run.py):** before the web stage, if the balance minus 5 spare credits is smaller than the number of uncached searches, the LAST items in file order get no web search. Their web evidence is empty and flagged "serper budget"; they stay in n, and their web answers are null.
- With balance 999 this skips about 6 of FRESH-4's 1000 items. That can only lower coverage or yield on those items; it cannot add errors.

## Resources needed before running
- **GPU:** a dedicated RTX PRO 6000 pod, which the user will rent: about 1.5–2 h for both sets.
- **User time:** the sensitivity gold audit, about 10–30 rows.

## Freeze procedure
1. Re-hash all files listed below. Any difference from results/runs/s18/hashes_draft.txt must be explained here before running.
2. Record the freeze time.
3. Run `VKG_EMB=hf python -B -m vkg.s17_run fresh3`, then `fresh4`, then `python -B -m vkg.s18_eval raw fresh3 fresh4`.
4. Gold-audit sheet, then `python -B -m vkg.s18_eval audited fresh3 fresh4`.
5. Report everything, whatever the outcome.

## Draft hashes (results/runs/s18/hashes_draft.txt)
s17_run (updated with the budget rule; re-hashed at freeze), s18_eval 143db183…, s17_eval d1d66b0e…, l3_verify 19266e88…, test_l3_verify 109f5059…, evidence_fast 53cd9c09…, emb2 b722ef35…, lite 3947c03b…, pod 5293103d…, podgen_server 0e93ea25…, websearch 397e84e4…, websearch2 9a9ae3f4…, localwiki d56d44c0…, s14_eval 0372e365…, grade6 b74faad2…, grade_judge 2e392d6b…, fresh3 1dd9f0f5…, fresh4 9334cd7c….

## FREEZE (2026-11-06 21:28, before any FRESH-3/FRESH-4 model output exists)
- **Status:** this protocol is now frozen. Final hashes are in results/runs/s18/hashes_freeze.txt (25 files, including every file whose source is executed by the pipeline).
- **Changes from the draft hashes:**
  - vkg/pod.py gained a VKG_POD_HOST setting (the pod address moved);
  - vkg/podgen_server.py's memory cap became a setting (VKG_MEM_FRAC; 0.6 on this dedicated GPU, which only affects memory, not outputs);
  - vkg/s17_run.py gained the Serper budget rule above;
  - results/runs/s16/pod_up.sh gained the single-copy judge import.
  None of these changes how answers are produced or graded.
- **Hardware:** a dedicated RunPod RTX 5090 (32 GB), CUDA. Judge qwen3.8-27b e0a7cdbef002 and embedder ac6da0dfba84, with model files SHA-256-verified. Qwen3-4B safetensors match the local copy.
- **Judge agreement on this card:** 300/300 against the stored local labels (results/audit2/pod_judge_check_rtx5090.md). The earlier RTX PRO 6000 check was 298/300.
- **Serper balance at freeze:** 999.
- **Run order:** s17_run fresh3, then fresh4, then s18_eval raw fresh3 fresh4.

## RESULT (2026-11-07 04:10)
**L2 NOT MET.** G3: coverage 38.2% (pass), 20 graded-wrong releases (> 10), SER upper 1.60%. R1 fail, R2 pass, R3 pass,
R4 pass (provisional, 15 of 20 A2), R5 pending the user's audit, R6 fail (coverage), R7 pass. All frozen hashes re-verified after the run.
Full write-up: results/runs/s18/S18_RESULT.md. FRESH-3 and FRESH-4 are now used.
