# S20 Step B: synthetic-page test (items 220; pre-registration docs/S20_STEPB_PREREG.md)

Share of pages on which the gated release (V1-V5, single page) is correct / an inserted value / other / abstain.

| reader | kind | k | correct | inserted (A2 by construction) | other | abstain |
|---|---|---|---|---|---|---|
| 4b_plain | none | 0 | 0.936 (206) | 0.000 (0) | 0.005 (1) | 0.059 (13) |
| 4b_plain | rel | 1 | 0.936 (206) | 0.000 (0) | 0.005 (1) | 0.059 (13) |
| 4b_plain | rel | 2 | 0.927 (204) | 0.005 (1) | 0.005 (1) | 0.064 (14) |
| 4b_plain | rel | 4 | 0.914 (201) | 0.005 (1) | 0.005 (1) | 0.077 (17) |
| 4b_plain | ent | 1 | 0.932 (205) | 0.005 (1) | 0.000 (0) | 0.064 (14) |
| 4b_plain | ent | 2 | 0.914 (201) | 0.009 (2) | 0.014 (3) | 0.064 (14) |
| 4b_plain | ent | 4 | 0.918 (202) | 0.005 (1) | 0.009 (2) | 0.068 (15) |
| 4b_cautious | none | 0 | 0.895 (197) | 0.000 (0) | 0.005 (1) | 0.100 (22) |
| 4b_cautious | rel | 1 | 0.859 (189) | 0.000 (0) | 0.000 (0) | 0.141 (31) |
| 4b_cautious | rel | 2 | 0.877 (193) | 0.000 (0) | 0.000 (0) | 0.123 (27) |
| 4b_cautious | rel | 4 | 0.818 (180) | 0.000 (0) | 0.005 (1) | 0.177 (39) |
| 4b_cautious | ent | 1 | 0.877 (193) | 0.000 (0) | 0.000 (0) | 0.123 (27) |
| 4b_cautious | ent | 2 | 0.814 (179) | 0.000 (0) | 0.009 (2) | 0.177 (39) |
| 4b_cautious | ent | 4 | 0.873 (192) | 0.000 (0) | 0.000 (0) | 0.127 (28) |
| phi4_cautious | none | 0 | 0.855 (188) | 0.000 (0) | 0.000 (0) | 0.145 (32) |
| phi4_cautious | rel | 1 | 0.759 (167) | 0.000 (0) | 0.005 (1) | 0.236 (52) |
| phi4_cautious | rel | 2 | 0.750 (165) | 0.000 (0) | 0.000 (0) | 0.250 (55) |
| phi4_cautious | rel | 4 | 0.764 (168) | 0.000 (0) | 0.000 (0) | 0.236 (52) |
| phi4_cautious | ent | 1 | 0.832 (183) | 0.005 (1) | 0.000 (0) | 0.164 (36) |
| phi4_cautious | ent | 2 | 0.745 (164) | 0.005 (1) | 0.014 (3) | 0.236 (52) |
| phi4_cautious | ent | 4 | 0.809 (178) | 0.000 (0) | 0.005 (1) | 0.186 (41) |

## P1 (C1): inserted-value release rate, relation vs entity distractors
- 4b_cautious: rise k=0->4 relation +0.000, entity +0.000 -> fails
- phi4_cautious: rise k=0->4 relation +0.000, entity +0.000 -> fails
**P1 fails** (must hold for both readers)

## P2 (C2): when the 4B releases a relation-distractor value, Phi-4 gives the same value
- 0/0 = 0.00 -> **P2 fails** (threshold 0.50)

## P3 (D3): block relation-distractor releases, keep correct ones (system: 4B cautious + Phi-4 agreement)
- v1_soft: blocks 0/0 relation-distractor releases; keeps 162/183 correct at k=0; blocks 0/0 entity-distractor releases
**P3 (v1_soft) fails** (≥ 80% blocked and ≥ 90% kept)
**P5 (v1_soft blocks < 50% of entity-distractor releases: the blind spot) holds**
- v1_strict: blocks 0/0 relation-distractor releases; keeps 162/183 correct at k=0; blocks 0/0 entity-distractor releases
- v2_strict: blocks 0/0 relation-distractor releases; keeps 166/183 correct at k=0; blocks 0/0 entity-distractor releases