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
