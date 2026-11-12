# Track C, C1: evidence-sensitivity suite (development data; mechanical scoring)

## esuite_v2_infernix_11951_material_only (6 of 3363 prompts; median 90.1 s per request)

| version | context | language | n | correct | errors |
|---|---|---|---|---|---|
| A | long | en | 1 | 0 (0%) | no reply 1 |
| A | short | en | 1 | 0 (0%) | no reply 1 |
| A | short | zh | 1 | 0 (0%) | no reply 1 |
| B | long | en | 1 | 0 (0%) | no reply 1 |
| B | short | en | 1 | 0 (0%) | no reply 1 |
| B | short | zh | 1 | 0 (0%) | no reply 1 |
| all |  |  | 6 | 0 (0%) | no reply 6 |

## esuite_v2_ollama_qwen3_8_27b_material_only (3363 of 3363 prompts; median 0.6 s per request)

| version | context | language | n | correct | errors |
|---|---|---|---|---|---|
| A | long | en | 200 | 178 (89%) | abstained 19, other (unsupported) 2, wrong value from material 1 |
| A | short | en | 200 | 195 (98%) | abstained 4, other (unsupported) 1 |
| A | short | zh | 200 | 180 (90%) | other (unsupported) 11, abstained 9 |
| B | long | en | 200 | 162 (81%) | abstained 25, other (unsupported) 8, wrong value from material 5 |
| B | short | en | 200 | 161 (80%) | abstained 29, wrong value from material 6, other (unsupported) 4 |
| B | short | zh | 200 | 131 (66%) | abstained 61, wrong value from material 5, other (unsupported) 3 |
| C | long | en | 200 | 199 (100%) | guessed 1 |
| C | short | en | 200 | 194 (97%) | guessed 6 |
| C | short | zh | 200 | 197 (98%) | guessed 3 |
| D | long | en | 200 | 193 (96%) | abstained 4, picked one 3 |
| D | short | en | 200 | 195 (98%) | picked one 3, abstained 2 |
| D | short | zh | 200 | 194 (97%) | abstained 4, picked one 2 |
| E | long | en | 121 | 109 (90%) | abstained 10, wrong value from material 2 |
| E | short | en | 121 | 76 (63%) | wrong value from material 39, abstained 6 |
| E | short | zh | 121 | 81 (67%) | wrong value from material 29, abstained 10, other (unsupported) 1 |
| F | long | en | 200 | 180 (90%) | abstained 16, other (unsupported) 3, wrong value from material 1 |
| F | short | en | 200 | 186 (93%) | abstained 11, other (unsupported) 2, wrong value from material 1 |
| F | short | zh | 200 | 182 (91%) | abstained 14, other (unsupported) 4 |
| all |  |  | 3363 | 2993 (89%) | abstained 224, wrong value from material 89, other (unsupported) 39, guessed 10, picked one 8 |

