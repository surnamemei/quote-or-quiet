# S42 E1: what the frozen system does with each baseline answer (S29 sealed set, n = 3,359)

Rows: the baseline's own outcome against the reference answer. Columns: the frozen system's outcome on the same question.

## B0 raw model, closed book

| baseline outcome | n | Verified, matches gold | Verified, gold mismatch cleared by review | Verified, gold mismatch not cleared | Verified, wrong (both reviewers) | Unresolved |
|---|---|---|---|---|---|---|
| wrong | 2582 | 1295 (50.2%) | 34 (1.3%) | 16 (0.6%) | 1 (0.0%) | 1236 (47.9%) |
| right | 680 | 393 (57.8%) | 2 (0.3%) | 0 (0.0%) | 0 (0.0%) | 285 (41.9%) |
| no answer | 97 | 23 (23.7%) | 0 (0.0%) | 1 (1.0%) | 0 (0.0%) | 73 (75.3%) |

Of the baseline's 2582 gold-wrong answers: replaced by a verified answer that matches gold 1295 (50.2%), turned into Unresolved 1236 (47.9%), released with a gold mismatch 51 (1.98%; 34 cleared by review, 16 not cleared, 1 wrong for both reviewers). Not cleared or wrong: 17 of 2582, one-sided 97.5% upper bound 1.05%.
Of the baseline's 680 gold-right answers: kept as Verified 393 (57.8%), lost to Unresolved 285 (41.9%), released with a gold mismatch 2.

## B1 raw model + abstention prompt

| baseline outcome | n | Verified, matches gold | Verified, gold mismatch cleared by review | Verified, gold mismatch not cleared | Verified, wrong (both reviewers) | Unresolved |
|---|---|---|---|---|---|---|
| wrong | 1729 | 812 (47.0%) | 23 (1.3%) | 13 (0.8%) | 1 (0.1%) | 880 (50.9%) |
| right | 644 | 368 (57.1%) | 1 (0.2%) | 0 (0.0%) | 0 (0.0%) | 275 (42.7%) |
| no answer | 986 | 531 (53.9%) | 12 (1.2%) | 4 (0.4%) | 0 (0.0%) | 439 (44.5%) |

Of the baseline's 1729 gold-wrong answers: replaced by a verified answer that matches gold 812 (47.0%), turned into Unresolved 880 (50.9%), released with a gold mismatch 37 (2.14%; 23 cleared by review, 13 not cleared, 1 wrong for both reviewers). Not cleared or wrong: 14 of 1729, one-sided 97.5% upper bound 1.35%.
Of the baseline's 644 gold-right answers: kept as Verified 368 (57.1%), lost to Unresolved 275 (42.7%), released with a gold mismatch 1.

## B2 standard RAG

| baseline outcome | n | Verified, matches gold | Verified, gold mismatch cleared by review | Verified, gold mismatch not cleared | Verified, wrong (both reviewers) | Unresolved |
|---|---|---|---|---|---|---|
| wrong | 232 | 1 (0.4%) | 32 (13.8%) | 13 (5.6%) | 1 (0.4%) | 185 (79.7%) |
| right | 2939 | 1710 (58.2%) | 4 (0.1%) | 4 (0.1%) | 0 (0.0%) | 1221 (41.5%) |
| no answer | 188 | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) | 188 (100.0%) |

Of the baseline's 232 gold-wrong answers: replaced by a verified answer that matches gold 1 (0.4%), turned into Unresolved 185 (79.7%), released with a gold mismatch 46 (19.83%; 32 cleared by review, 13 not cleared, 1 wrong for both reviewers). Not cleared or wrong: 14 of 232, one-sided 97.5% upper bound 9.92%.
Of the baseline's 2939 gold-right answers: kept as Verified 1710 (58.2%), lost to Unresolved 1221 (41.5%), released with a gold mismatch 8.
