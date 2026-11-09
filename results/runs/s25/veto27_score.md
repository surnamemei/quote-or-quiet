# S25 stronger veto (design data)

| policy | variant | A (added vs frozen S19) | wrong among added | correct among added |
|---|---|---|---|---|
| 27b | indep | 79 | 5 | 74 |
| 27b | pin | 72 | 13 | 59 |
| both | indep | 72 | 5 | 67 |
| both | pin | 65 | 11 | 54 |
| phi4 | indep | 73 | 5 | 68 |
| phi4 | pin | 67 | 13 | 54 |

Decision rule (docs/S25_PLAN.md): wrong added releases fall by at least half and at least 75% of the correct added survive, pooled over pin and indep, relative to policy phi4:
- 27b: wrong 18 (phi4 18), correct 133 (phi4 122) -> not an improvement
- both: wrong 16 (phi4 18), correct 121 (phi4 122) -> not an improvement
