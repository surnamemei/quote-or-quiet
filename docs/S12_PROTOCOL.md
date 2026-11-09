# S12 protocol: search-on-abstain v2 (second-chance chunks + entity search + agreement filter)

Written 2026-11-06, before any S12 output.

## Why (from S11, results/S11_search_on_abstain.md)
Of the 198 round-0 abstentions:
- 48 already had the gold in the passage;
- 21 were recovered by S11's search;
- 65 had the gold on some Wikipedia page that S11 did not reach. For 18 of these the page had been fetched, but its answer chunk did not fit the passage; for 47 the page was never found.
- 64 do not have the gold on Wikipedia at all.

S11's late answers were wrong a third of the time (7 of 21).

## Design (vkg/s12_run.py)
Only round-0 abstentions of the 4B cautious prompt are touched (FRESH 78, DEV 120). The model is Qwen3-4B-Instruct-2507, greedy decoding.
- **Round 1, second chance:** the next-best 1500 words of chunks from the round-0 pages (same BM25+dense fusion), excluding chunks already shown.
- **Round 2, entity search:**
  - pages for named entities in the question (quoted titles and capitalised spans, looked up with Wikipedia's "go" search);
  - plus the 4B's own 3 queries (as in S11);
  - up to 8 unseen pages, 1500 words.
- **Acceptance:** the cautious prompt must answer, and the plain prompt on the same passage must give the same answer (normalised tokens equal, or one contained in the other). Otherwise the system moves on, and after round 2 it abstains.
- **Also reported:** "S12 no filter" (the first non-abstaining cautious answer), as a secondary system.
- **Data:** FRESH and DEV as in S11. Grader 6 (P0.1 and P0.2 met). Search is Wikipedia only and no gold is used.
- **Schedule:** runs only after the FRESH-2 build has finished, so the two never compete for the GPU.

## Hashes (SHA-256)
- vkg/s12_run.py 6f87ef89291375016d459fd596173b7966846bf553a13a2334da40867c108136
- vkg/s12_wait.py 2f9e32216d3d6acb699df9dd7026b1da04e4780b13e6ed861226896c079ae380
- vkg/s12_eval.py 0180e97226be3332cdbabdd761bfdef8301ce63aa74e7d12106576fff311226b

## Predictions (pooled FRESH + DEV, 500 items, against cautious)
- **T1:** correct +3.0 points or more, with the paired CI lower bound above 0.
- **T2:** SER at most +0.6 points. Equivalently, accepted late answers have precision of at least about 0.80.
- **T3:** the agreement filter raises late-answer precision over "S12 no filter" by at least 0.10.
- **T4 (L1 check, FRESH):** coverage ≥ 71%, correct ≥ 61% and SER ≤ 5.0%. My prior is about 10%.
- **T5 (cost):** logged per searched item. I expect at most 2 rounds, 8 pages, and 3 generations per round.

## Decision rule
- **Search-on-abstain is worth keeping:** T1 and T2 hold. It then goes into the final FRESH-2 confirmation together with the best answerer.
- **Not worth its errors:** T1 holds and T2 fails.
- **Search on Wikipedia with a 4B is exhausted:** T1 fails. The remaining options are web search (needs the user's API key) and a stronger reader.
