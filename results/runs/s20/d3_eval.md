# D3 frame-match check on used sets (exploratory, post hoc; results/runs/s20/d3_eval.py)

| set | system | released | coverage | wrong | correct | wrong blocked | correct blocked |
|---|---|---|---|---|---|---|---|
| dev (n=300) | G3 V1-V5 | 141 | 0.470 | 1 (0.0033) | 140 |  |  |
| dev (n=300) | G3 V1-V5 + D3-soft | 96 | 0.320 | 0 (0.0000) | 96 | 1 | 44 |
| dev (n=300) | G3 V1-V5 + D3-strict | 41 | 0.137 | 0 (0.0000) | 41 | 1 | 99 |
| dev (n=300) | G3 V1-V5 + Phi-4 veto | 138 | 0.460 | 1 (0.0033) | 137 |  |  |
| dev (n=300) | G3 V1-V5 + Phi-4 veto + D3-soft | 94 | 0.313 | 0 (0.0000) | 94 | 1 | 43 |
| dev (n=300) | G3 V1-V5 + Phi-4 veto + D3-strict | 40 | 0.133 | 0 (0.0000) | 40 | 1 | 97 |
| dev | correct releases by D3 outcome (of 140) | no frame 71; sentence check fails 24; qualifier check fails 26 | | | | | |
| dev | parser coverage among G3 releases | 0.49 | | | | | |
| fresh (n=200) | G3 V1-V5 | 84 | 0.420 | 2 (0.0100) | 82 |  |  |
| fresh (n=200) | G3 V1-V5 + D3-soft | 52 | 0.260 | 0 (0.0000) | 52 | 2 | 30 |
| fresh (n=200) | G3 V1-V5 + D3-strict | 20 | 0.100 | 0 (0.0000) | 20 | 2 | 62 |
| fresh (n=200) | G3 V1-V5 + Phi-4 veto | 83 | 0.415 | 2 (0.0100) | 81 |  |  |
| fresh (n=200) | G3 V1-V5 + Phi-4 veto + D3-soft | 51 | 0.255 | 0 (0.0000) | 51 | 2 | 30 |
| fresh (n=200) | G3 V1-V5 + Phi-4 veto + D3-strict | 19 | 0.095 | 0 (0.0000) | 19 | 2 | 62 |
| fresh | correct releases by D3 outcome (of 82) | no frame 43; sentence check fails 19; qualifier check fails 16 | | | | | |
| fresh | parser coverage among G3 releases | 0.48 | | | | | |
| s18 (n=2000) | G3 V1-V5 | 758 | 0.379 | 15 (0.0075) | 743 |  |  |
| s18 (n=2000) | G3 V1-V5 + D3-soft | 544 | 0.272 | 5 (0.0025) | 539 | 10 | 204 |
| s18 (n=2000) | G3 V1-V5 + D3-strict | 223 | 0.112 | 2 (0.0010) | 221 | 13 | 522 |
| s18 (n=2000) | G3 V1-V5 + Phi-4 veto | 735 | 0.367 | 9 (0.0045) | 726 |  |  |
| s18 (n=2000) | G3 V1-V5 + Phi-4 veto + D3-soft | 532 | 0.266 | 4 (0.0020) | 528 | 5 | 198 |
| s18 (n=2000) | G3 V1-V5 + Phi-4 veto + D3-strict | 221 | 0.111 | 1 (0.0005) | 220 | 8 | 506 |
| s18 | correct releases by D3 outcome (of 743) | no frame 377; sentence check fails 128; qualifier check fails 107 | | | | | |
| s18 | parser coverage among G3 releases | 0.49 | | | | | |