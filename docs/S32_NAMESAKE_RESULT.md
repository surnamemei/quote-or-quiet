# S32 result: namesake detector (2026-11-09; plan and design iterations in S32_NAMESAKE_PLAN.md)

Frozen rule: variant D of results/runs/s32/s32_namesake.py used as "withhold if flagged" (sha256 20e9df6b..., after a crash fix that left the design result unchanged).

Design sets (472 frozen releases plus the S31 cell): 17 flagged, 4 gold-wrong (all namesakes: Dobra River, Jordan, Legion, Heat), 13 gold-correct (2.9% of correct).

Test, one run, on the frozen releases of the already reported test sets (secondary analysis; these sets were not used in the design):

| set | releases | gold-wrong | flagged | flagged wrong | flagged correct (share of correct) |
|---|---|---|---|---|---|
| FRESH-5 | 568 | 4 | 0 | 0 | 0 (0.0%) |
| Mintaka test | 620 | 28 | 67 | 5 | 62 (10.5%) |
| PopQA test | 401 | 17 | 37 | 7 | 30 (7.8%) |
| all | 1,589 | 49 | 104 | 12 | 92 (6.0%) |

Pass rule (at least 5 flagged, at least 20% of flagged gold-wrong, at most 5% of correct flagged): **FAIL** on both conditions (11.5% and 6.0%). The rule is not adopted.

The flag is informative (11.5% wrong among flagged against 3.1% among all releases, a 3.7-fold enrichment), but withholding the 104 flagged answers would remove 12 wrong ones at the cost of 92 right ones. The false flags come from two weaknesses of a title-index method: the subject is often a partial name ("Rise" for Rise to Honor, "Paul" for Paul Atreides, "Fallout" for Fallout 4), and generic question words ("largest city", "released") occur on many unrelated pages of the same name (Wyoming, Illinois; Halo, a song). The design sets were too small to show this (17 flags).

Reading: deciding whether a question is ambiguous needs to know what kind of thing the question is about, which the title index and word overlap do not capture. The workable next step is a model-based reading check: for a flagged question, show the reader the namesake pages' first sentences and ask which one the question means, or answer once per page and flag only when the answers differ. That needs GPU time, so it waits until the sealed run is finished.
