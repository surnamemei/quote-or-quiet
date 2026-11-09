# S21 raw result (DEV dry run) (vkg/s21_eval.py score; alias-aware gold-relative, before adjudication)

## mintaka_dev (H1-M, primary)
n = 200; released 71 (coverage 0.355, floor 0.35); correct 69; graded-wrong k = 2; raw SER 0.0100; corrected upper (98.75% CP) 0.0479
Secondary endpoint (gold-relative): **FAIL**
Primary endpoint (adjudicated): pending the blind adjudication sheet.

| stratum | n | released | coverage | wrong | combo_plain answered | combo_plain wrong |
|---|---|---|---|---|---|---|
| mintaka_books | 28 | 16 | 0.571 | 1 | 27 | 5 |
| mintaka_geography | 15 | 8 | 0.533 | 0 | 13 | 0 |
| mintaka_history | 21 | 6 | 0.286 | 0 | 17 | 2 |
| mintaka_movies | 21 | 8 | 0.381 | 0 | 21 | 2 |
| mintaka_music | 29 | 8 | 0.276 | 0 | 27 | 7 |
| mintaka_politics | 20 | 0 | 0.000 | 0 | 18 | 4 |
| mintaka_sports | 37 | 10 | 0.270 | 0 | 35 | 7 |
| mintaka_videogames | 29 | 15 | 0.517 | 1 | 26 | 4 |
| ALL | 200 | 71 | 0.355 | 2 | 184 | 31 |

## popqa_dev (descriptive)
n = 300; released 59 (coverage 0.197, floor 0.35); correct 53; graded-wrong k = 6; raw SER 0.0200; corrected upper (98.75% CP) 0.0513

| stratum | n | released | coverage | wrong | combo_plain answered | combo_plain wrong |
|---|---|---|---|---|---|---|
| pop_high | 100 | 23 | 0.230 | 2 | 83 | 24 |
| pop_low | 100 | 21 | 0.210 | 2 | 76 | 33 |
| pop_mid | 100 | 15 | 0.150 | 2 | 81 | 39 |
| ALL | 300 | 59 | 0.197 | 6 | 240 | 96 |

Graded-wrong releases (popqa_dev):

- What is Rusty Willoughby's occupation? | gold songwriter / song writer | released Musician | page Rusty Willoughby
- In what country is Dobra River? | gold Romania / Roumania / Rumania / România | released Croatia | page Dobra (Kupa)
- Who was the producer of O Dragão da Maldade Contra o Santo Guerreiro? | gold Glauber Rocha / Glauber de Andrade Rocha | released Zelito Viana | page Antonio das Mortes
- What is Jordan the capital of? | gold Guimaras / Province of Guimaras | released Amman | page Index of Jordan-related articles
- What genre is Legion? | gold horror literature | released Superhero | page List of Legion of Super-Heroes publications
- What is Brussels Capital Region the capital of? | gold Burgundian Netherlands / Western European Union / European Economic Community / EEC | released Belgium | page List of ambassadors to Belgium

Adjudication sheet (mintaka only): 6 rows, results/runs/s21/S21_adjudication_sheet_dev.csv; key in S21_adjudication_key_dev.json (not shown to the adjudicator).