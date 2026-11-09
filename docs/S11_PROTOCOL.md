# S11 protocol: search-on-abstain for the small model

Written 2026-11-05, before any S11 output. This is the decisive direction check for L1 and H2 in docs/CHECKPOINTS.md.

## Idea
target.txt Goal A: when evidence is insufficient the system should look for more, and say "unknown" only if that fails. An abstention may mean "not found yet" rather than "not knowable". Prior work: FLARE, DRAGIN and SeaKR trigger retrieval on uncertainty; Search-R1 (2503.09516) trains search agents. Here the trigger is the model's own abstention, and the searcher is the small model itself.

## Design (vkg/s11_run.py)
- Model: Qwen3-4B-Instruct-2507, bf16, greedy decoding.
- Round 0: the existing 4B cautious answer on the existing passage (FRESH from S8; DEV SimpleQA-E from S6b).
- If round 0 abstains (code non-answer detector), there are up to 2 more rounds:
  - the 4B writes 3 new Wikipedia queries from the question alone;
  - MediaWiki full-text search, keeping at most 6 pages not seen before (seen = the round-0 page titles);
  - chunk ranking as before (`retrieval2.passage`, 1500 words);
  - the 4B cautious prompt on the new passage.
  - The loop stops at the first non-abstaining answer.
- Items answered at round 0 are never touched.
- Search backend: Wikipedia only; no general web search; no gold used by the system.
- Sets: FRESH (200; 78 round-0 abstentions) and DEV SimpleQA-E (300; 120 abstentions).
  - FRESH has been used in S8, S9 and grader 6, so it is no longer pristine.
  - The final L1 confirmation is reserved for FRESH-2 (CHECKPOINTS P0.5).
- Grader 6 (primary), via the judge on the new answers.
- "Recoverable": the gold string (dataset `matches`) appears in a passage the loop fetched. This uses the gold for analysis only.
- Cost is logged: rounds, pages, prompt and generated tokens, seconds.

## Hashes (SHA-256)
- vkg/s11_run.py 172226547b5ef864864fa1593024b2246d15cba3a3e9a8a7234b944fcf761708
- vkg/s11_wait.py 00716c7ceaaabdc0ba6c02c06d40477eb0294f1beb695b5f3a8a42936f6240c2
- vkg/s11_eval.py 21fecbb7074a095278273508b898eef9a8dbfeb5e7cb7490249c2098f41cb1ef

## Baselines (grader 6)

| set | system | coverage | correct | SER |
|---|---|---|---|---|
| FRESH | plain (the L1 baseline) | 71.0 | 61.0 | 10.0 |
| FRESH | cautious (round 0) | 61.0 | 57.0 | 4.0 |
| DEV | plain | 74.0 | 61.0 | 13.0 |
| DEV | cautious | 60.0 | 56.0 | 4.0 |

## Predictions
- **S1 (H2.b):** recovery rate at least 30% among recoverable abstentions (pooled).
- **S2:** pooled SER, S11 minus cautious, at most +1.0 point. Equivalently, new answers have precision of at least about 70%.
- **S3:** pooled correct-answer gain of at least 3 points, with the paired CI lower bound above 0.
- **S4 (L1 on FRESH, the strict target):** coverage ≥ 71%, correct ≥ 61% and SER ≤ 5.0%. My prior is about 15%: only 78 abstentions are available, and 16 or more must become correct with at most 2 new errors.
- **S5 (cost):** mean extra cost per searched item reported; I expect at most about 2 rounds and 12 pages.

## Decision rule
- **Direction confirmed:** S2 and S3 hold (more correct answers without materially more silent errors).
- **L1 reached on FRESH:** S4 holds as well (to be confirmed on FRESH-2).
- **Direction rejected:** S3 fails, meaning searching again does not recover answers for the small model.
