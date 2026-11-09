# S21 raw result (vkg/s21_eval.py score; alias-aware gold-relative, before adjudication)

## mintaka_test (H1-M, primary)
n = 2000; released 620 (coverage 0.310, floor 0.35); correct 592; graded-wrong k = 28; raw SER 0.0140; corrected upper (97.50% CP) 0.0208
Secondary endpoint (gold-relative): **FAIL**
Primary endpoint (adjudicated): pending the blind adjudication sheet.

| stratum | n | released | coverage | wrong | combo_plain answered | combo_plain wrong |
|---|---|---|---|---|---|---|
| mintaka_books | 252 | 101 | 0.401 | 1 | 226 | 21 |
| mintaka_geography | 269 | 84 | 0.312 | 0 | 238 | 37 |
| mintaka_history | 241 | 59 | 0.245 | 5 | 196 | 13 |
| mintaka_movies | 226 | 60 | 0.265 | 2 | 210 | 46 |
| mintaka_music | 262 | 83 | 0.317 | 5 | 241 | 35 |
| mintaka_politics | 244 | 60 | 0.246 | 5 | 216 | 38 |
| mintaka_sports | 243 | 65 | 0.267 | 8 | 218 | 43 |
| mintaka_videogames | 263 | 108 | 0.411 | 2 | 231 | 24 |
| ALL | 2000 | 620 | 0.310 | 28 | 1776 | 257 |

## popqa_test (descriptive)
n = 2100; released 401 (coverage 0.191, floor 0.35); correct 384; graded-wrong k = 17; raw SER 0.0081; corrected upper (97.50% CP) 0.0135

| stratum | n | released | coverage | wrong | combo_plain answered | combo_plain wrong |
|---|---|---|---|---|---|---|
| pop_high | 700 | 119 | 0.170 | 3 | 548 | 132 |
| pop_low | 700 | 177 | 0.253 | 10 | 524 | 170 |
| pop_mid | 700 | 105 | 0.150 | 4 | 489 | 203 |
| ALL | 2100 | 401 | 0.191 | 17 | 1561 | 505 |

Graded-wrong releases (popqa_test):

- In what country is Turin? | gold United States of America / the United States of America / America / U.S.A. | released Italy | page Outline of Turin
- What is Gordie Gosse's occupation? | gold politician / political leader / political figure / polit. | released Youth worker | page Gordie Gosse
- Who is the author of Lear? | gold Edward Bond | released Edward Lear | page Foss (cat)
- What genre is Brain Slaves? | gold neo-psychedelia | released garage rock | page Brain Slaves
- What is Alex Krieps's occupation? | gold politician / political leader / political figure / polit. | released General practitioner | page Alex Krieps
- What genre is William Keepers Maxwell, Jr.? | gold short story / tale / pripovijetka | released Domestic realism | page William Keepers Maxwell Jr.
- In what country is Fin? | gold Iran / Islamic Republic of Iran / Persia / ir | released Finland | page Finnish Correspondence Chess Federation
- Who was the director of Shaft? | gold John Singleton / John Daniel Singleton | released Gordon Parks | page Shaft (franchise)
- Who was the director of Barabbas? | gold Roger Young | released Richard Fleischer | page Barabbas (novel)
- Who was the screenwriter for Exposed? | gold James Toback / James Lee Toback | released Gee Malik Linton | page Gee Malik Linton
- Who is the author of Science-Fantasy Quintette? | gold Ed Earl Repp / Bradnor Buckner / Edward Earl Repp | released L. Ron Hubbard and Ed Earl Repp | page Science-Fantasy Quintette
- Who was the producer of Unprecedented: The 2000 Presidential Election? | gold Robert Greenwald | released Richard Ray Pérez and Joan Sekler | page Unprecedented: The 2000 Presidential Election
- Who is the father of Dick Grayson? | gold Batman / Matches Malone / Sir Hemingford Grey / Mordecai Wayne | released John Grayson | page Dick Grayson
- Who was the screenwriter for Hook? | gold Malia Scotch Marmo / Nick Castle / Nicholas Charles Castle, Jr. / Nicholas Charles Castle Jr. | released James V. Hart | page James V. Hart
- In what city was Gilbert Bodart born? | gold Seraing | released Ougrée | page Gilbert Bodart
- In what country is Lima? | gold United States of America / the United States of America / America / U.S.A. | released Peru | page The Church of Jesus Christ of Latter-day Saints in Peru
- What is Javier Alva Orlandini's occupation? | gold politician / political leader / political figure / polit. | released lawyer | page Javier Alva Orlandini

Adjudication sheet (mintaka only): 84 rows, results/runs/s21/S21_adjudication_sheet.csv; key in S21_adjudication_key.json (not shown to the adjudicator).