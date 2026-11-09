# Direction 1, first look: how much of the residual error could question resolution remove? (2026-11-09; my reading, not blind; existing data, no run)
Data: the 29 system errors kept by the strict two-adjudicator rule on the Mintaka test set for the combination system (docs/S22_DEV_FINDINGS.md; list in results/runs/s22/mintaka_test_adj_result_strict.md). Classes below are my reading of each row.
| class | n | rows | what would fix it |
|---|---|---|---|
| ambiguous question, adjudicated | 9 | all-time scorer, who led Germany after Hitler, Baftas start, BCS 2008, North Carolina 2016, first Patternist book, youngest president, first video game, Grammy 2017 | state the criterion or time point ("by publication date", "as of 1945") |
| scope ambiguity (my reading) | 1 | most Oscar nominations "for his performances" | state the scope |
| answer acceptable but more specific, coarser or not the gold's wording | 5 | Statue of Liberty copper, Gutzon Borglum, Greek Dark Ages, La Higuera, 14th century | a gold-side fix, not a system fix |
| cannot tell (gold defect or both defensible) | 6 | Lee Morgan, Streep birth year, first pharaoh, Super Bowl host city, Swift Grammys, Cleopatra dynasty | gold audit |
| clear system error | 8 | blues harp, Japan Senate, Franco-Dutch war years, Pizarro, dribbling, Game Boy designer, Thor films, Parma population | none of the above: the span is in a pinned page but answers a different relation or part of it |
Reading. Stating the criterion or scope would convert at most 10 of 29 (34%) into checkable statements; at 1,005 releases that moves SER from 1.45% (29 of 2,000) to about 0.95% (19 of 2,000), whose corrected upper bound
is still above 1% (the allowance at n = 2,000 is 10 errors). Eight errors (28%, 0.8% of releases) are genuine failures of the mapping assumption: the span is verbatim and typed but is not the answer to the asked relation
("1678" for a range of years, "Senate" for the Japanese chamber's name, "9" for a film count). The gate checks type, not relation. A relation-level check is the open hole; the L3 fork's conditional-truth judge failed on it (docs/L3_SUMMARY.md), so it is not a cheap fix.
Consequence for direction 1: worth building as an output state (it makes the paper's Qualified claim real on real data), but it cannot by itself bring a coverage-raising variant under the 1% bound.
