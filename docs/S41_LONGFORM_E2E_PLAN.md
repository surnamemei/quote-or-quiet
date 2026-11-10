# S41: long-form end-to-end on the 50 design biographies (plan, 2026-11-10 09:40, before any S41 run)

Why: S37 measured the decomposition (version 2 slots: about 91-96% faithful, coverage 85%). Its closing note says the truth of the output rests on the verification step, and that the one gap it cannot see (a slot verified as true for the wrong reason) needs an end-to-end test: verify the slots, re-render from verified slots only, and judge every kept statement against the facts. This is a design-set measurement, not a sealed test; nothing here is a claim of the paper.

## Input
results/runs/s37/slots2.jsonl: 1,492 slot claims (subject, question, value, type) from 50 Phi-4 closed-book biographies (drafts.jsonl).

## Verification of one slot (short-form machinery, value as the only candidate)
1. Evidence: local FineWiki top 5 for the slot question (evidence_fast.wiki_build, as in the frozen system). No web search: the search pool is reserved for the S40 prefetch, so the web and combined sources are not used. This is a reduction from three sources to one, stated as such.
2. Support: Qwen3-4B (plain and cautious prompts, 40 tokens, greedy) reads the wiki passage; at least one reader's answer agrees with the value (s12_run.agree), and neither gives a different answer.
3. Deductive gate: l3_checks2.release2(question, value, wiki titles, page text) passes (verbatim typed span in a hash-pinned page).
4. Second reader: Phi-4, cautious prompt on the same passage, agrees with the value. Phi-4 also wrote the drafts (closed book); here it reads evidence, but the correlation is noted.
A slot is kept (Verified) only if 2, 3 and 4 hold. Output is re-rendered from kept slots only (template: question, value, quote).

## Measures
- Retention: kept slots / all slots, overall and by type.
- False-kept rate: every kept statement (question and value only) judged against the facts by two blind reviewers (S36/S38 rubric, default model), plus 20 injected-false decoys (values swapped between kept slots of the same type) and 20 random dropped slots as a contrast. A false kept statement needs both reviewers to say "wrong". Cluster bootstrap by biography for the interval.
- Fidelity: share of kept slots whose value appears in the draft sentence (by construction 100%; reported as a check).

## Predictions (written now)
- Retention 20% to 50% of slots (lower for OTHER and OCCUPATION types, where the typed gate rarely applies).
- False-kept rate at most 2% (both reviewers); decoys at least 18 of 20 caught.
- If the false-kept rate is above 3%, the long-form sealed test is not started; the failure modes are described and the verification revised on this design set.

## Run notes

- 2026-11-10 09:39: the first attempt failed in the reader step with a GPU out-of-memory error. The 4B server had been capped at 0.45 of the GPU; the S19 runs used 0.65. No reader output and no result existed at that point. Second attempt started 09:43 with the cap at 0.65 and with checkpoints for the evidence and reader steps; method unchanged.
- 2026-11-10 09:30 (before any output): Phi-4 runs on the CPU (the same model and prompt, through Ollama with no GPU) so that the GPU is free after the reader step. CPU and GPU arithmetic can differ in rare greedy-decoding ties; this is a design run and the difference is not measured here.
- 2026-11-10 09:58: the second attempt died at 09:55 in the reader step with a connection reset on the local socket (a network tool on the machine changed socket settings at that time). Third attempt: the reader step saves every 120 prompts and retries, and the wrapper restarts the 4B server if it is gone. Prompts and decoding unchanged.
- 2026-11-10 10:12: the verify process held 36 GB of RAM (an embedding table loaded by an import and never used), so a CPU Phi-4 next to it would have left no free memory. This replaces the 09:30 note: after the reader step the process is restarted without the table (results/runs/s41/run_s41d.sh) and Phi-4 runs on the GPU under the lock, as in S29. Evidence and reader outputs are reused from the checkpoints; no S41 result existed when this was decided.

Amendment 2026-11-10 10:20 (before verified.jsonl exists): rule Q of docs/S42_CLAIM_AUDIT_AND_PLAN.md is applied unchanged as a
secondary analysis (results/runs/s41/lf_q.py): a slot that is not kept is Qualified if its value passes the deductive gate. Up to 40
random Qualified slots are added to the blind sheet, drawn after the registered draws so those are unchanged. Predictions: Qualified
adds 3 to 12 points of slots; among reviewed Qualified slots the value is called wrong by both reviewers in at most 15%. The primary
endpoints (retention, false-kept rate, decoys) are not affected.

Run note 2026-11-10 10:27: stage 4 finished at 10:26 (144 s with Phi-4 on the GPU). Slots 1,492; reader support 243; gate 200; kept 147
(retention 9.9%, below the predicted 20 to 50%: that prediction FAILED before review). Rule Q: Qualified 360 (24.1%, above the predicted
3 to 12 points: FAILED), of which 307 had no reader support. Blind sheets built (227 rows: 147 kept, 20 dropped, 20 decoys, 40 Qualified);
four reviewers started 10:27.
