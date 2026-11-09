# S19 design re-measurement on DuckDuckGo evidence (results/runs/s19/design_eval.py)

| set | system | coverage | correct | SER | errors |
|---|---|---|---|---|---|
| dev (n=300) | wiki_plain | 0.673 | 0.567 | 0.1067 | 32 |
| dev (n=300) | combo_plain | 0.923 | 0.847 | 0.0767 | 23 |
| dev (n=300) | combo_cautious | 0.860 | 0.823 | 0.0367 | 11 |
| dev (n=300) | MSany | 0.943 | 0.850 | 0.0933 | 28 |
| dev (n=300) | G2 V1-V4 | 0.587 | 0.573 | 0.0133 | 4 |
| dev (n=300) | G3 V1-V4 | 0.470 | 0.467 | 0.0033 | 1 |
| dev (n=300) | G3 V1-V5 | 0.470 | 0.467 | 0.0033 | 1 |
| dev (n=300) | G3 V1-V5 + Phi-4 veto | 0.460 | 0.457 | 0.0033 | 1 |
| dev (n=300) | G2 V1-V5 + Phi-4 veto | 0.557 | 0.550 | 0.0067 | 2 |
| fresh (n=200) | wiki_plain | 0.640 | 0.555 | 0.0850 | 17 |
| fresh (n=200) | combo_plain | 0.905 | 0.840 | 0.0650 | 13 |
| fresh (n=200) | combo_cautious | 0.835 | 0.800 | 0.0350 | 7 |
| fresh (n=200) | MSany | 0.920 | 0.860 | 0.0600 | 12 |
| fresh (n=200) | G2 V1-V4 | 0.575 | 0.555 | 0.0200 | 4 |
| fresh (n=200) | G3 V1-V4 | 0.420 | 0.410 | 0.0100 | 2 |
| fresh (n=200) | G3 V1-V5 | 0.420 | 0.410 | 0.0100 | 2 |
| fresh (n=200) | G3 V1-V5 + Phi-4 veto | 0.415 | 0.405 | 0.0100 | 2 |
| fresh (n=200) | G2 V1-V5 + Phi-4 veto | 0.540 | 0.530 | 0.0100 | 2 |