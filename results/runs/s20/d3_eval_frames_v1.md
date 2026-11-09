# D3 frame-match check on used sets (exploratory, post hoc; results/runs/s20/d3_eval.py)

| set | system | released | coverage | wrong | correct | wrong blocked | correct blocked |
|---|---|---|---|---|---|---|---|
| dev (n=300) | G3 V1-V5 | 141 | 0.470 | 1 (0.0033) | 140 |  |  |
| dev (n=300) | G3 V1-V5 + D3-soft | 110 | 0.367 | 1 (0.0033) | 109 | 0 | 31 |
| dev (n=300) | G3 V1-V5 + D3-strict | 49 | 0.163 | 0 (0.0000) | 49 | 1 | 91 |
| dev (n=300) | G3 V1-V5 + Phi-4 veto | 138 | 0.460 | 1 (0.0033) | 137 |  |  |
| dev (n=300) | G3 V1-V5 + Phi-4 veto + D3-soft | 108 | 0.360 | 1 (0.0033) | 107 | 0 | 30 |
| dev (n=300) | G3 V1-V5 + Phi-4 veto + D3-strict | 48 | 0.160 | 0 (0.0000) | 48 | 1 | 89 |
| dev | correct releases by D3 outcome (of 140) | no frame 71; sentence check fails 18; qualifier check fails 16 | | | | | |
| dev | parser coverage among G3 releases | 0.49 | | | | | |
| fresh (n=200) | G3 V1-V5 | 84 | 0.420 | 2 (0.0100) | 82 |  |  |
| fresh (n=200) | G3 V1-V5 + D3-soft | 64 | 0.320 | 0 (0.0000) | 64 | 2 | 18 |
| fresh (n=200) | G3 V1-V5 + D3-strict | 23 | 0.115 | 0 (0.0000) | 23 | 2 | 59 |
| fresh (n=200) | G3 V1-V5 + Phi-4 veto | 83 | 0.415 | 2 (0.0100) | 81 |  |  |
| fresh (n=200) | G3 V1-V5 + Phi-4 veto + D3-soft | 63 | 0.315 | 0 (0.0000) | 63 | 2 | 18 |
| fresh (n=200) | G3 V1-V5 + Phi-4 veto + D3-strict | 22 | 0.110 | 0 (0.0000) | 22 | 2 | 59 |
| fresh | correct releases by D3 outcome (of 82) | no frame 43; sentence check fails 16; qualifier check fails 7 | | | | | |
| fresh | parser coverage among G3 releases | 0.48 | | | | | |
| s18 (n=2000) | G3 V1-V5 | 758 | 0.379 | 15 (0.0075) | 743 |  |  |
| s18 (n=2000) | G3 V1-V5 + D3-soft | 602 | 0.301 | 5 (0.0025) | 597 | 10 | 146 |
| s18 (n=2000) | G3 V1-V5 + D3-strict | 260 | 0.130 | 2 (0.0010) | 258 | 13 | 485 |
| s18 (n=2000) | G3 V1-V5 + Phi-4 veto | 735 | 0.367 | 9 (0.0045) | 726 |  |  |
| s18 (n=2000) | G3 V1-V5 + Phi-4 veto + D3-soft | 590 | 0.295 | 5 (0.0025) | 585 | 4 | 141 |
| s18 (n=2000) | G3 V1-V5 + Phi-4 veto + D3-strict | 259 | 0.130 | 2 (0.0010) | 257 | 7 | 469 |
| s18 | correct releases by D3 outcome (of 743) | no frame 377; sentence check fails 95; qualifier check fails 67 | | | | | |
| s18 | parser coverage among G3 releases | 0.49 | | | | | |