# S39 result (plan docs/S39_PLAN.md; 2026-11-10)

1,200 design questions (PopQA 600 by popularity tercile, Mintaka 600), free-search-mcp pool. Frozen S19 system: 323 releases (coverage 0.27).

Blind review (results/runs/s39/s39_sheet.py, s39_unblind.py): every release added beyond the frozen system, 30 random frozen releases and 20 injected-false decoys; question and answer only, two reviewers per row (default model), S38 rubric; an error needs both reviewers to say "wrong".
- Decoys called wrong by both: 20/20 (valid). Random frozen releases called wrong: 0/30 (by either reviewer: 0).

| rule | added | gold-wrong | wrong (both) | rate | one-sided 90% upper | pass (>= 60, <= 3%, upper <= 5%) |
|---|---|---|---|---|---|---|
| independent title retrieval (S23 combination) | 124 | 19 | 0 | 0.0% | 1.8% | **PASS** |
| two-source cell V2 (registered wording) | 30 | 5 | 1 | 3.3% | 12.4% | fail (too few added; 1 error) |
| two-source cell V2b (any missing source) | 33 | 5 | 1 | 3.0% | 11.3% | fail |

- All 19 gold-wrong independent-retrieval releases were judged correct (or correct for one reading of an ambiguous question) by both reviewers: the gold labels of PopQA and Mintaka miss valid answers (for example several works sharing one title, or dated "most awards" counts).
- The one cell error: "first player to hit 50 home runs in one season" answered Willie Mays (Babe Ruth).

Decisions under the plan:
- Independent title retrieval passes S39. It was not part of the S29 secondary test, and S40 runs without it (docs/S40_PLAN.md, line dated 01:05), so it goes to a later sealed run as its own pre-registered test.
- The two-source cell adds too few releases on this set to meet the 60-release minimum, and its point estimate is just above 3%. It stays in version 2 on the strength of the S29 test (3/144 wrong, upper 4.6%), as frozen in docs/S40_PLAN.md before S39 was reviewed; the S39 numbers are reported alongside. Pooled over S38 (0/55, broader cell definition), S29 (V2, 3/144) and S39 (V2, 1/30): 4 errors in 229 added releases.
