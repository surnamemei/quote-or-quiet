# Entity-slot checks on the S19 H1 system (exploratory, post hoc; results/runs/s21/ent_eval.py)

| set | n | system | released | coverage | wrong | correct |
|---|---|---|---|---|---|---|
| dev | 300 | H1 | 138 | 0.460 | 1 | 137 |
| dev | 300 | H1 + E-match | 88 | 0.293 | 0 | 88 |
| dev | 300 | H1 + E-unique | 129 | 0.430 | 1 | 128 |
| dev | 300 | H1 + E-match + E-unique | 80 | 0.267 | 0 | 80 |
| fresh | 200 | H1 | 83 | 0.415 | 2 | 81 |
| fresh | 200 | H1 + E-match | 59 | 0.295 | 0 | 59 |
| fresh | 200 | H1 + E-unique | 80 | 0.400 | 2 | 78 |
| fresh | 200 | H1 + E-match + E-unique | 56 | 0.280 | 0 | 56 |
| s18 | 2000 | H1 | 735 | 0.367 | 9 | 726 |
| s18 | 2000 | H1 + E-match | 492 | 0.246 | 5 | 487 |
| s18 | 2000 | H1 + E-unique | 684 | 0.342 | 9 | 675 |
| s18 | 2000 | H1 + E-match + E-unique | 451 | 0.226 | 5 | 446 |
| fresh5 | 1526 | H1 | 568 | 0.372 | 4 | 564 |
| fresh5 | 1526 | H1 + E-match | 388 | 0.254 | 3 | 385 |
| fresh5 | 1526 | H1 + E-unique | 522 | 0.342 | 4 | 518 |
| fresh5 | 1526 | H1 + E-match + E-unique | 357 | 0.234 | 3 | 354 |
| popqa_dev | 300 | H1 | 59 | 0.197 | 7 | 52 |
| popqa_dev | 300 | H1 + E-match | 31 | 0.103 | 2 | 29 |
| popqa_dev | 300 | H1 + E-unique | 50 | 0.167 | 5 | 45 |
| popqa_dev | 300 | H1 + E-match + E-unique | 25 | 0.083 | 1 | 24 |
| mintaka_dev | 200 | H1 | 71 | 0.355 | 2 | 69 |
| mintaka_dev | 200 | H1 + E-match | 19 | 0.095 | 1 | 18 |
| mintaka_dev | 200 | H1 + E-unique | 54 | 0.270 | 2 | 52 |
| mintaka_dev | 200 | H1 + E-match + E-unique | 10 | 0.050 | 1 | 9 |