# S39: a larger design test for independent title retrieval and the two-source cell (plan, 2026-11-09)

Why: S38 left independent title retrieval inconclusive (72 added, 2 real errors, upper bound 7.2%) and passed the two-source cell on 55 added. Both need more data before a version 2 is frozen.
Data: 1,200 new design questions (results/runs/s39/s39_sample.py): PopQA 200 per popularity tercile and Mintaka generic 600, the next slices of the S21 seeded shuffles (no overlap with any set used so far). Search results from the free-search-mcp pool (prefetched).
Runs (after the S29 sealed run frees the GPU): the frozen pipeline on all 1,200; the independent-retrieval variant (S23 code, unchanged) on the same questions.
Review: every release added by either rule beyond the frozen system, plus 30 random frozen releases and 20 decoys, judged against the facts by two blind reviewers (question and answer only).
Pass rule per rule, fixed now: at least 60 added releases, at most 3% wrong, one-sided 90% upper bound at most 5%. A rule that passes here and on the S29 secondary test goes into version 2, which is frozen and tested once on a new sealed set together with L1 at its coverage.
