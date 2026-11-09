# Conformal-style baseline (post hoc, design comparison)

calibration n = 2500, test (FRESH-5) n = 1526

| t | calib released | calib wrong | LTT p (H0: SER >= 1%) | test released (cov) | test wrong | test corrected upper |
|---|---|---|---|---|---|---|
| 6 | 880 | 7 | 0.0001 | 552 (0.362) | 9 | 1.20% |
| 5 | 1018 | 18 | 0.1323 | 631 (0.413) | 12 | 1.45% |
| 4 | 1410 | 35 | 0.9859 | 1064 (0.697) | 41 | 3.70% |
| 3 | 1852 | 72 | 1.0000 | 1178 (0.772) | 71 | 5.91% |
| 2 | 1955 | 100 | 1.0000 | 1242 (0.814) | 93 | 7.49% |
| 1 | 2083 | 160 | 1.0000 | 1296 (0.849) | 122 | 9.61% |
| 0 | 2175 | 229 | 1.0000 | 1335 (0.875) | 153 | 11.78% |

Selected t = 6: FRESH-5 released 552 (coverage 0.362), wrong 9, SER 0.59%, corrected upper 1.20%. Frozen system: coverage 0.372, 4 wrong, upper 0.76%.
