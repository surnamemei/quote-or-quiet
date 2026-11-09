# S21 DEV feasibility (frozen S19 H1 system; design data)

## popqa_dev (n=300)
released 59 (coverage 0.197, floor 0.35); wrong k=7 (alias string-match among wrong: 0); upper at this n 0.0519

| stratum | n | released | coverage | wrong | combo_plain answered | combo_plain correct | combo_plain wrong |
|---|---|---|---|---|---|---|---|
| pop_high | 100 | 23 | 0.230 | 3 | 83 | 56 | 27 |
| pop_low | 100 | 21 | 0.210 | 2 | 76 | 42 | 34 |
| pop_mid | 100 | 15 | 0.150 | 2 | 81 | 42 | 39 |
| ALL | 300 | 59 | 0.197 | 7 | 240 | 140 | 100 |

Abstention reasons: support<3 (2) 156, released 59, support<3 (0) 41, support<3 (1) 29, gate 11, vetoed 4

## mintaka_dev (n=200)
released 71 (coverage 0.355, floor 0.35); wrong k=2 (alias string-match among wrong: 0); upper at this n 0.0432

| stratum | n | released | coverage | wrong | combo_plain answered | combo_plain correct | combo_plain wrong |
|---|---|---|---|---|---|---|---|
| mintaka_books | 28 | 16 | 0.571 | 1 | 27 | 21 | 6 |
| mintaka_geography | 15 | 8 | 0.533 | 0 | 13 | 13 | 0 |
| mintaka_history | 21 | 6 | 0.286 | 0 | 17 | 15 | 2 |
| mintaka_movies | 21 | 8 | 0.381 | 0 | 21 | 19 | 2 |
| mintaka_music | 29 | 8 | 0.276 | 0 | 27 | 20 | 7 |
| mintaka_politics | 20 | 0 | 0.000 | 0 | 18 | 14 | 4 |
| mintaka_sports | 37 | 10 | 0.270 | 0 | 35 | 28 | 7 |
| mintaka_videogames | 29 | 15 | 0.517 | 1 | 26 | 22 | 4 |
| ALL | 200 | 71 | 0.355 | 2 | 184 | 152 | 32 |

Abstention reasons: support<3 (2) 85, released 71, gate 24, support<3 (1) 11, support<3 (0) 8, vetoed 1
