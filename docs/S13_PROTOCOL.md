# S13 protocol: open-web search on abstain for the small model

Written 2026-11-06, before any S13 output. User direction: no search API key; the system should just search online.

## Why
In S11, 32% of the 4B's abstentions (64 of 198) have no answer on Wikipedia at all, even with a search that knows the gold. Only the open web can recover those.

## Design (vkg/s13_run.py, vkg/websearch.py)
- **Scope:** only round-0 abstentions of the 4B cautious prompt (FRESH 78, DEV 120), with one web round.
- **Queries:** the question text plus the 4B's own first two queries (S11 prompt).
- **Search:** DuckDuckGo's keyless HTML endpoint, at most one request per about 4 s, cached. Up to 8 result pages are fetched (HTML only, 20 s timeout).
- **Contamination guard** (arXiv 2508.13180):
  - benchmark, dataset and code domains are blocked (huggingface, github, kaggle, arxiv, paperswithcode, openai, openreview, aclanthology, semanticscholar, researchgate, scale, llm-stats);
  - a page is dropped if it contains the question verbatim (normalised whole question, or its first 60 characters) or mentions SimpleQA.
  - The count of dropped pages is logged.
- **Passage:** 120-word chunks ranked by BM25 plus dense fusion, 1500 words, each chunk labelled with its domain.
- **Acceptance:** as in S12, the cautious answer counts only if the plain prompt on the same passage confirms it. "S13 no filter" is logged as a secondary system.
- **Grading:** grader 6. No gold is used by the system.
- **Schedule:** runs after S12 finishes (one GPU job of mine at a time), at idle priority.

## Limits to report
- The web changes over time. The cache in results/cache/web freezes what was seen.
- Pages may be wrong or AI-generated. The guard catches only verbatim leaks, not paraphrased answer keys.
- The web search engine and the exact result pages are not reproducible later. The cache is the record.

## Hashes (SHA-256)
- vkg/websearch.py 9ba2d0471c9a649c28666ad88fa19876658c9f8c0396b1c0712a1ef156e3a2ee
- vkg/s13_run.py c8fa57f1dc11926031de0f4b3a5a52a20b0b40bc946c2eda560353c991164aa9
- vkg/s13_wait.py 0514eb9cfe46755ce7230b90381b368ee30e0c7c947e168f622c8d4b4a3c6511
- vkg/s13_eval.py 7f3baab288aa2d6687d18eca58490861d3cf62d8f7e853310f7e21f4994e543a

## Predictions (pooled FRESH + DEV, 500, against cautious)
- **W1:** correct +4.0 points or more, CI lower bound above 0. The web reaches answers Wikipedia lacks.
- **W2:** SER at most +1.0 point, i.e. accepted web answers have precision of at least about 0.80.
- **W3:** dropped contaminated pages make up at most 5% of fetched pages (descriptive; a high share would be a warning).
- **W4 (L1 check, FRESH):** coverage ≥ 71%, correct ≥ 61% and SER ≤ 5.0%, for S13 alone and for "S12 then S13" (post hoc, secondary). My prior is about 20%.
- **W5 (cost):** logged per searched item (pages, seconds, tokens).

## Decision rule
- **Web search on abstain is kept for the final FRESH-2 confirmation:** W1 and W2 hold.
- **More answers but too many new errors:** W1 holds and W2 fails. Acceptance must then get stricter before any confirmation.

## Incident and amendment (2026-11-06 05:10, before any S13 output was scored or read)
- **What happened:** at item 376 of 500, DuckDuckGo started returning its bot-check ("anomaly") page. Six spaced retries failed, and s13_run stopped with an error, as designed: it never returns an empty result silently.
- **What I did not do:** the bot check was not bypassed.
- **Changes:**
  - the search pace was slowed from one request per 4 s to one per 10 s (vkg/websearch.py, new hash 397e84e4fc19094e0835fa8e0df9729c66dd34dd614e9f2caee0789bfcebac67);
  - a probe sends one query every 30 min, and S13 resumes from item 377 (finished rows are kept) once results come back.
- **Effect on results:** the pace change alters only timing, not results; searches and pages already made are cached.
- **Logs:** results/runs/s13/run_attempt1_blocked.log.
