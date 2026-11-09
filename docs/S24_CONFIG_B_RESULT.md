# S24 configuration B result (2026-11-09; sealed set closed_test2, seed 303, 1,500 items, single run)

Configuration B: Phi-4 plain and cautious readers, Qwen3.8-27B veto, specifications by Phi-4; everything else the frozen harness (hashes verified after the
run). Raw: results/runs/s24/alt/closed_test2_score.md.

| item type | n | correct definite answer | left Unresolved | wrong definite answer |
|---|---|---|---|---|
| lookup, unique or qualified name | 630 | 526 | 104 | 0 |
| tenure | 240 | 32 | 208 | 0 |
| computed age | 240 | 226 | 14 | 0 |
| namesake, list per entity | 150 | 70 | 80 | 0 |
| fact not in the corpus | 240 | 0 | 240 (correct) | 0 |
| all | 1,500 | 854 (56.9%) | 406 | **0** |

Output-level L2 (k <= 6, coverage >= 35%): met; k = 0, corrected 97.5% upper bound 0.246%.
Predictions (written before the set was generated): six of seven held. L2 met (0.7) yes; no wrong Verified or Derived (0.55) yes; completion 45 to 65% (0.7) yes, 56.9%;
within 8 points of configuration A's 54.2% (0.65) yes, +2.7; compute_age >= 85% (0.8) yes, 226 of 240 = 94.2%; tenure <= 20% (0.85) yes, 13.3%;
namesake Qualified-ok between 10% and 45% (0.7) **no**, 70 of 150 = 46.7%.
Reading. With other models in the reader and veto roles the rules produced again no wrong definite answer, and completion moved by 2.7 points, so on this
corpus the guarantee machinery does not depend on the 4B. Configuration B reads tenure and namesake questions somewhat better and is otherwise equal.
