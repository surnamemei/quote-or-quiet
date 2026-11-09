# D3 v2 (blind LLM parsers, phi4) on used sets (exploratory; DEV is design data)

| set | system | released | coverage | wrong | correct | wrong blocked | correct blocked |
|---|---|---|---|---|---|---|---|
| dev (n=300) | G3 V1-V5 | 141 | 0.470 | 1 | 140 |  |  |
| dev (n=300) | G3 V1-V5 + v2-soft | 69 | 0.230 | 0 | 69 | 1 | 71 |
| dev (n=300) | G3 V1-V5 + v2-soft + v1-qual | 67 | 0.223 | 0 | 67 | 1 | 73 |
| dev (n=300) | G3 V1-V5 + v2-strict | 63 | 0.210 | 0 | 63 | 1 | 77 |
| dev (n=300) | G3 V1-V5 + v2-strict + v1-qual | 62 | 0.207 | 0 | 62 | 1 | 78 |
| dev (n=300) | G3 V1-V5 + veto | 138 | 0.460 | 1 | 137 |  |  |
| dev (n=300) | G3 V1-V5 + veto + v2-soft | 67 | 0.223 | 0 | 67 | 1 | 70 |
| dev (n=300) | G3 V1-V5 + veto + v2-soft + v1-qual | 65 | 0.217 | 0 | 65 | 1 | 72 |
| dev (n=300) | G3 V1-V5 + veto + v2-strict | 61 | 0.203 | 0 | 61 | 1 | 76 |
| dev (n=300) | G3 V1-V5 + veto + v2-strict + v1-qual | 60 | 0.200 | 0 | 60 | 1 | 77 |
| dev | correct releases: no q-frame 11, no s-frame 8, mismatch 43, role not whole 36 (of 140) | | | | | | |
| fresh (n=200) | G3 V1-V5 | 84 | 0.420 | 2 | 82 |  |  |
| fresh (n=200) | G3 V1-V5 + v2-soft | 51 | 0.255 | 1 | 50 | 1 | 32 |
| fresh (n=200) | G3 V1-V5 + v2-soft + v1-qual | 47 | 0.235 | 0 | 47 | 2 | 35 |
| fresh (n=200) | G3 V1-V5 + v2-strict | 43 | 0.215 | 1 | 42 | 1 | 40 |
| fresh (n=200) | G3 V1-V5 + v2-strict + v1-qual | 41 | 0.205 | 0 | 41 | 2 | 41 |
| fresh (n=200) | G3 V1-V5 + veto | 83 | 0.415 | 2 | 81 |  |  |
| fresh (n=200) | G3 V1-V5 + veto + v2-soft | 50 | 0.250 | 1 | 49 | 1 | 32 |
| fresh (n=200) | G3 V1-V5 + veto + v2-soft + v1-qual | 46 | 0.230 | 0 | 46 | 2 | 35 |
| fresh (n=200) | G3 V1-V5 + veto + v2-strict | 42 | 0.210 | 1 | 41 | 1 | 40 |
| fresh (n=200) | G3 V1-V5 + veto + v2-strict + v1-qual | 40 | 0.200 | 0 | 40 | 2 | 41 |
| fresh | correct releases: no q-frame 9, no s-frame 3, mismatch 25, role not whole 10 (of 82) | | | | | | |
| s18 (n=2000) | G3 V1-V5 | 758 | 0.379 | 15 | 743 |  |  |
| s18 (n=2000) | G3 V1-V5 + v2-soft | 414 | 0.207 | 6 | 408 | 9 | 335 |
| s18 (n=2000) | G3 V1-V5 + v2-soft + v1-qual | 382 | 0.191 | 4 | 378 | 11 | 365 |
| s18 (n=2000) | G3 V1-V5 + v2-strict | 353 | 0.176 | 6 | 347 | 9 | 396 |
| s18 (n=2000) | G3 V1-V5 + v2-strict + v1-qual | 329 | 0.165 | 4 | 325 | 11 | 418 |
| s18 (n=2000) | G3 V1-V5 + veto | 735 | 0.367 | 9 | 726 |  |  |
| s18 (n=2000) | G3 V1-V5 + veto + v2-soft | 403 | 0.202 | 3 | 400 | 6 | 326 |
| s18 (n=2000) | G3 V1-V5 + veto + v2-soft + v1-qual | 375 | 0.188 | 3 | 372 | 6 | 354 |
| s18 (n=2000) | G3 V1-V5 + veto + v2-strict | 345 | 0.172 | 3 | 342 | 6 | 384 |
| s18 (n=2000) | G3 V1-V5 + veto + v2-strict + v1-qual | 324 | 0.162 | 3 | 321 | 6 | 405 |
| s18 | correct releases: no q-frame 84, no s-frame 27, mismatch 256, role not whole 118 (of 743) | | | | | | |
| fresh5 (n=1526) | G3 V1-V5 | 589 | 0.386 | 7 | 582 |  |  |
| fresh5 (n=1526) | G3 V1-V5 + v2-soft | 329 | 0.216 | 3 | 326 | 4 | 256 |
| fresh5 (n=1526) | G3 V1-V5 + v2-soft + v1-qual | 312 | 0.204 | 3 | 309 | 4 | 273 |
| fresh5 (n=1526) | G3 V1-V5 + v2-strict | 280 | 0.183 | 2 | 278 | 5 | 304 |
| fresh5 (n=1526) | G3 V1-V5 + v2-strict + v1-qual | 270 | 0.177 | 2 | 268 | 5 | 314 |
| fresh5 (n=1526) | G3 V1-V5 + veto | 568 | 0.372 | 4 | 564 |  |  |
| fresh5 (n=1526) | G3 V1-V5 + veto + v2-soft | 318 | 0.208 | 2 | 316 | 2 | 248 |
| fresh5 (n=1526) | G3 V1-V5 + veto + v2-soft + v1-qual | 302 | 0.198 | 2 | 300 | 2 | 264 |
| fresh5 (n=1526) | G3 V1-V5 + veto + v2-strict | 274 | 0.180 | 1 | 273 | 3 | 291 |
| fresh5 (n=1526) | G3 V1-V5 + veto + v2-strict + v1-qual | 264 | 0.173 | 1 | 263 | 3 | 301 |
| fresh5 | correct releases: no q-frame 60, no s-frame 28, mismatch 195, role not whole 88 (of 582) | | | | | | |