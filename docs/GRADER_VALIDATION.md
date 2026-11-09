# Validation of the repaired open-world grader (`grade_v3`)

Date: 2026-11-05. Author: an LLM (Claude) reading the rows; no human labeller, no web lookup, no model call, no GPU. Scripts and raw artefacts: `results/audit/validation/` (`v1_draw.py`, `v2_compare.py`, `v3_extra.py`, `v4_report.py`, `sample_blind.jsonl`, `my_labels.txt`, `sample_key_HIDDEN.json`, `metrics.json`, `disagreements.json`, `extra.json`). Nothing under `vkg/` or any existing file was edited.

## 1. Result in one paragraph
On 240 hand-labelled answered rows (120 that `grade_v3` calls correct, 120 that it calls wrong) the grader has **0 false positives among 120 grader-correct rows (0.0%, 95% Clopper-Pearson [0.0%, 3.0%])** and **47 false negatives among 120 grader-wrong rows (39.2%, [30.4%, 48.5%])**. Precision of the "correct" label is therefore high in this sample, but the "wrong" label is unreliable for the grounded systems (RAG and oracle files): in those two files 47 of 80 sampled grader-wrong rows are correct answers. The false negatives are concentrated in 12 distinct questions that recur across systems, so the row-level rate overstates what a question-level rate would be (section 4). The cause of nearly all false negatives is that `repaired` demands every gold token in the answer, which fails on omitted middle names, shorter official names, alias parentheticals and gold-data artefacts. This is the limitation the `repaired` docstring already lists as known.

## 2. Procedure and sample

* Seed: `random.Random(20261105)` (`v1_draw.py`). Pool: rows with `status == "answer"` and a non-empty answer in the three files (closed-book n500, RAG n300, oracle n251). Grader label from `vkg.grade_open.grade_v3(row)`, called as a black box; its code was not read until all 240 labels were written to `my_labels.txt`.
* Rows were written to `sample_blind.jsonl` (question, gold, answer, system, file; no grader label) in shuffled order; the grader labels went to a separate key file that I did not open until the labels were saved.
* Quota: 120 grader-correct and 120 grader-wrong. Within each file x stratum the draw is a round-robin over the systems present (B0_raw, B1_abstain, B2_strict, VKG_v2), at most 8 B0_raw rows per file x stratum, so B0_raw is 24/120 = 20.0% of each stratum (cap not exceeded).
* The closed-book file has only 44 grader-correct answered rows (29 B0_raw, 11 B1_abstain, 4 VKG_v2), so with the B0_raw cap it yields 23. The shortfall of 17 was moved to the RAG file (48) and the oracle file (49), taken from non-B0 systems first by the round-robin. Grader-wrong: 40 per file.
* Labelling rule: standard SimpleQA. Correct = answer contains the gold fact and does not contradict it; harmless extra detail allowed; a hedge ("more than 137") instead of a value is incorrect; less specific than gold (year only for a full date, "uncle" for "maternal uncle") is incorrect; "acceptable range" in the gold is honoured; abstentions are incorrect.

Sample composition (rows):

| file | grader-correct | grader-wrong | B0_raw | B1_abstain | B2_strict | VKG_v2 |
|---|---|---|---|---|---|---|
| closed | 23 | 40 | 16 | 35 | 0 | 12 |
| rag | 48 | 40 | 16 | 25 | 24 | 23 |
| oracle | 49 | 40 | 16 | 25 | 25 | 23 |

## 3. Error rates

Rates are over rows (each row counts once; the same question appears under several systems, see section 4). Intervals are exact Clopper-Pearson 95%.

| file | grader-correct n | false positives | FP rate | 95% CI | grader-wrong n | false negatives | FN rate | 95% CI | overall agreement |
|---|---|---|---|---|---|---|---|---|---|
| closed | 23 | 0 | 0.0% | [0.0%, 14.8%] | 40 | 0 | 0.0% | [0.0%, 8.8%] | 100.0% |
| rag | 48 | 0 | 0.0% | [0.0%, 7.4%] | 40 | 19 | 47.5% | [31.5%, 63.9%] | 78.4% |
| oracle | 49 | 0 | 0.0% | [0.0%, 7.3%] | 40 | 28 | 70.0% | [53.5%, 83.4%] | 68.5% |
| all three | 120 | 0 | 0.0% | [0.0%, 3.0%] | 120 | 47 | 39.2% | [30.4%, 48.5%] | 80.4% |

False negatives by file and system (grader-wrong rows that I label correct / sampled grader-wrong rows):

| file | B0_raw | B1_abstain | B2_strict | VKG_v2 |
|---|---|---|---|---|
| closed | 0/8 | 0/24 | - | 0/8 |
| rag | 0/8 | 6/11 | 6/11 | 7/10 |
| oracle | 2/8 | 9/11 | 8/11 | 9/10 |

Reading: false negatives are essentially absent for B0_raw and for the closed-book file, and common for the three grounded systems in the RAG and oracle files. A grader that under-credits some systems and not others biases between-system comparisons of "wrong" counts and precision, not only absolute levels.

## 4. How far the row-level numbers can be trusted

* **Repeated questions.** The 120 grader-wrong rows contain only 70 distinct question ids, and the 47 false negatives only 12 distinct questions. The same RAG/oracle questions are answered by up to four systems, and the small grader-wrong pools in those files were drawn almost exhaustively. Counted by distinct question, the false-negative rate is 12/70 = 17.1% (CI [9.2%, 28.0%]). The 120 grader-correct rows contain 91 distinct ids; 0/91 gives a 95% upper bound of about 4.0% for the false-positive rate by question.
* **Sample is not the population.** The draw equalises systems, so it over-weights small cells (for instance 8 of the 8 closed-book VKG_v2 wrong rows, but 8 of 471 closed-book B0_raw wrong rows). Re-weighting the per-cell false-negative rates by the cell sizes of the full grader-wrong pool (838 rows) gives about 67 false-negative rows, or 8.0% of all grader-wrong rows. Applying the rule proposals in section 6 to the full pool independently flips 72 of 838 rows (8.6%), which agrees. Treat 8-9% as the pool-level estimate and the 39.2% in section 3 as a statement about the stratified sample.
* **Borderline labels.** 18 of the 47 false negatives are borderline (spelling variant of the gold name, nickname, title without author prefix, romanised song title, rounded number inside the accepted range). Counting all of them as wrong gives 29/120 = 24.2% (CI [16.8%, 32.8%]) as a lower reading.

## 5. Disagreements grouped by cause

All 47 disagreements are false negatives (I say correct, grader says wrong). There are no false positives.

| cause | rows | distinct questions | files | borderline? |
|---|---|---|---|---|
| A omitted middle name/initial | 10 | 2 | oracle 4, rag 6 | no |
| B1 shorter official name (dropped "The Republic of") | 4 | 1 | oracle 2, rag 2 | no |
| B2 secondary component of comma-gold omitted (county) | 6 | 1 | oracle 4, rag 2 | no |
| B3 title given without author prefix | 5 | 1 | oracle 3, rag 2 | yes (subjective) |
| C alias in gold parenthetical (consumption) | 5 | 1 | oracle 3, rag 2 | no |
| D spelling variant / nickname | 9 | 2 | oracle 6, rag 3 | yes (subjective) |
| E gold-data artifact (stray URL / footnote marker) | 4 | 2 | oracle 4 | no |
| F mixed-script gold, romanised answer | 2 | 1 | oracle 2 | yes (subjective) |
| G rounded number with scale word (2.1 million) inside range | 2 | 1 | rag 2 | yes (subjective) |

Notes on the causes: (A) gold "Katharine B. Blodgett" answered "Katharine Blodgett"; "Zofia Emilia Kielan-Jaworowska" answered without "Emilia". (B1) "The Republic of Colombia" answered "Colombia". (B2) "Randolph, Orange County" answered "Randolph" (the question asks for the town). (B3) gold "Zanele Muholi: African Women Photographers #1" answered without the author prefix. (C) gold "Tuberculosis (then know as "Consumption")": `repaired` deletes the parenthetical and then requires "tuberculosis", but the question asks for the name used at the time, which is the quoted alias. (D) "Niloufar Bayan" (the gold looks like a typo of Bayani) vs "Bayani"; "Kathy" vs "Kathryn" Kusner. (E) two gold strings carry scraping artefacts: "White" + a glued URL, and a dissertation title ending in the footnote marker "[1]"; the answers are exact. (F) gold "ド・キ・ド・キ☆モーニング[ Doki Doki☆Morning ] by BABYMETAL" answered "Doki Doki Morning". (G) gold range 2,006,000 to 2,217,157, answer "2.1 million".

### Full disagreement list

`k` is the row index in `sample_blind.jsonl`. "Mine" is my label, "grader" is `grade_v3`. Gold and answer are truncated to 70 and 80 characters.

| k | file | system | id | gold | answer | mine | grader | reason |
|---|---|---|---|---|---|---|---|---|
| 148 | rag | B2_strict | sqa-1157 | 2,111,578 (acceptable range: anything between 2,006,000 and 2,217,157) | 2.1 million | C | wrong | borderline: 2.1 million is a rounded value inside the accepted range |
| 163 | rag | VKG_v2 | sqa-1157 | 2,111,578 (acceptable range: anything between 2,006,000 and 2,217,157) | 2.1 million | C | wrong | borderline: 2.1 million is a rounded value inside the accepted range |
| 14 | rag | VKG_v2 | sqa-2966 | Katharine B. Blodgett | Katharine Blodgett | C | wrong | omits middle initial 'B.' |
| 28 | oracle | B1_abstain | sqa-2966 | Katharine B. Blodgett | Katharine Blodgett | C | wrong | omits middle initial 'B.' |
| 58 | rag | B2_strict | sqa-2966 | Katharine B. Blodgett | Katharine Blodgett | C | wrong | omits middle initial 'B.' |
| 78 | rag | B1_abstain | sqa-2966 | Katharine B. Blodgett | Katharine Blodgett | C | wrong | omits middle initial 'B.' |
| 149 | oracle | B2_strict | sqa-2966 | Katharine B. Blodgett | Katharine Blodgett | C | wrong | omits middle initial 'B.' |
| 26 | oracle | B1_abstain | sqa-1400 | Kathy Kusner | Kathryn Kusner | C | wrong | borderline: Kathryn vs nickname Kathy, same person |
| 45 | oracle | VKG_v2 | sqa-1400 | Kathy Kusner | Kathryn Kusner | C | wrong | borderline nickname, as 26 |
| 197 | oracle | B2_strict | sqa-1400 | Kathy Kusner | Kathryn Kusner | C | wrong | borderline nickname |
| 9 | rag | B1_abstain | sqa-2099 | Niloufar Bayan | Niloufar Bayani | C | wrong | borderline: gold 'Bayan' looks like a typo; answer 'Bayani' is the same person (spelling v |
| 37 | rag | VKG_v2 | sqa-2099 | Niloufar Bayan | Niloufar Bayani | C | wrong | borderline spelling variant, as 9 |
| 173 | rag | B2_strict | sqa-2099 | Niloufar Bayan | Niloufar Bayani | C | wrong | borderline spelling variant |
| 195 | oracle | VKG_v2 | sqa-2099 | Niloufar Bayan | Niloufar Bayani | C | wrong | borderline spelling variant |
| 196 | oracle | B1_abstain | sqa-2099 | Niloufar Bayan | Niloufar Bayani | C | wrong | borderline spelling variant |
| 227 | oracle | B2_strict | sqa-2099 | Niloufar Bayan | Niloufar Bayani | C | wrong | borderline spelling variant |
| 35 | oracle | B2_strict | sqa-3768 | Randolph, Orange County | Randolph | C | wrong | omits county |
| 107 | rag | B2_strict | sqa-3768 | Randolph, Orange County | Randolph | C | wrong | omits county |
| 139 | oracle | B0_raw | sqa-3768 | Randolph, Orange County | Randolph | C | wrong | omits county |
| 170 | rag | B1_abstain | sqa-3768 | Randolph, Orange County | Randolph | C | wrong | omits county |
| 201 | oracle | B1_abstain | sqa-3768 | Randolph, Orange County | Randolph | C | wrong | omits county |
| 226 | oracle | VKG_v2 | sqa-3768 | Randolph, Orange County | Randolph | C | wrong | omits county |
| 110 | oracle | B1_abstain | sqa-947 | Solution of the Two-dimensional Mixed-mixed Boundary Value Problem of  | Solution of the Two-dimensional Mixed-mixed Boundary Value Problem of Elasticity | C | wrong | gold ends with footnote marker [1]; answer is the exact title |
| 169 | oracle | VKG_v2 | sqa-947 | Solution of the Two-dimensional Mixed-mixed Boundary Value Problem of  | Solution of the Two-dimensional Mixed-mixed Boundary Value Problem of Elasticity | C | wrong | gold ends with footnote marker [1]; answer is the exact title |
| 36 | rag | B2_strict | sqa-3241 | The Republic of Colombia | Colombia | C | wrong | omits 'The Republic of' |
| 54 | oracle | B1_abstain | sqa-3241 | The Republic of Colombia | Colombia | C | wrong | omits 'The Republic of' |
| 147 | rag | VKG_v2 | sqa-3241 | The Republic of Colombia | Colombia | C | wrong | omits 'The Republic of' |
| 233 | oracle | VKG_v2 | sqa-3241 | The Republic of Colombia | Colombia | C | wrong | omits 'The Republic of' |
| 42 | oracle | B2_strict | sqa-2546 | Tuberculosis (then know as "Consumption") | consumption | C | wrong | 'consumption' is the then-name asked for |
| 50 | rag | B1_abstain | sqa-2546 | Tuberculosis (then know as "Consumption") | consumption | C | wrong | 'consumption' is the then-name asked for |
| 89 | rag | VKG_v2 | sqa-2546 | Tuberculosis (then know as "Consumption") | consumption | C | wrong | 'consumption' is the then-name asked for |
| 106 | oracle | B1_abstain | sqa-2546 | Tuberculosis (then know as "Consumption") | consumption | C | wrong | 'consumption' is the then-name asked for |
| 111 | oracle | VKG_v2 | sqa-2546 | Tuberculosis (then know as "Consumption") | consumption | C | wrong | 'consumption' is the then-name asked for |
| 90 | oracle | B2_strict | sqa-972 | Whitehttps://www.sfgmc.org/blog/pride-flags#block-yui_3_17_2_1_1683145 | white | C | wrong | gold has a stray URL appended; colour is white |
| 204 | oracle | VKG_v2 | sqa-972 | Whitehttps://www.sfgmc.org/blog/pride-flags#block-yui_3_17_2_1_1683145 | white | C | wrong | gold has a stray URL appended; colour is white |
| 56 | oracle | B1_abstain | sqa-2210 | Zanele Muholi: African Women Photographers #1 | African Women Photographers #1 | C | wrong | borderline: title without 'Zanele Muholi:' author prefix |
| 63 | oracle | VKG_v2 | sqa-2210 | Zanele Muholi: African Women Photographers #1 | African Women Photographers #1 | C | wrong | borderline: title without 'Zanele Muholi:' author prefix |
| 109 | rag | B1_abstain | sqa-2210 | Zanele Muholi: African Women Photographers #1 | African Women Photographers #1 | C | wrong | borderline: title without 'Zanele Muholi:' author prefix |
| 117 | rag | VKG_v2 | sqa-2210 | Zanele Muholi: African Women Photographers #1 | African Women Photographers #1 | C | wrong | borderline: title without 'Zanele Muholi:' author prefix |
| 136 | oracle | B0_raw | sqa-2210 | Zanele Muholi: African Women Photographers #1 | African Women Photographers #1 | C | wrong | borderline: title without 'Zanele Muholi:' author prefix |
| 88 | rag | B1_abstain | sqa-3583 | Zofia Emilia Kielan-Jaworowska | Zofia Kielan-Jaworowska | C | wrong | omits middle name Emilia |
| 159 | oracle | B2_strict | sqa-3583 | Zofia Emilia Kielan-Jaworowska | Zofia Kielan-Jaworowska | C | wrong | omits middle name Emilia |
| 199 | rag | B2_strict | sqa-3583 | Zofia Emilia Kielan-Jaworowska | Zofia Kielan-Jaworowska | C | wrong | omits middle name Emilia |
| 203 | rag | VKG_v2 | sqa-3583 | Zofia Emilia Kielan-Jaworowska | Zofia Kielan-Jaworowska | C | wrong | omits middle name Emilia |
| 208 | oracle | VKG_v2 | sqa-3583 | Zofia Emilia Kielan-Jaworowska | Zofia Kielan-Jaworowska | C | wrong | omits middle name Emilia |
| 33 | oracle | B1_abstain | sqa-3021 | ド・キ・ド・キ☆モーニング[ Doki Doki☆Morning ] by BABYMETAL | Doki Doki Morning | C | wrong | borderline: song identified, omits '☆' and 'by BABYMETAL' |
| 100 | oracle | B2_strict | sqa-3021 | ド・キ・ド・キ☆モーニング[ Doki Doki☆Morning ] by BABYMETAL | Doki Doki Morning | C | wrong | borderline: song identified, omits symbol and 'by BABYMETAL' |

## 6. Proposed rule changes (not applied)

These were prototyped as separate functions in `v3_extra.py` (function `proposed`), never in `vkg/`. Each proposal adds *alternative gold strings* that are then passed through the existing `repaired`, so every existing safeguard (hedge words, number-range handling, month check) still applies. Prototype result on the 240 labelled rows: rules 1-2 plus the scale-word step of rule 3 fix 36 of the 47 false negatives (11 remain); adding the fuzzy name token of rule 3 fixes 42 (5 remain: Kathy/Kathryn Kusner and the romanised song title). Zero of the 73 grader-wrong rows that I labelled wrong become correct. The rules were designed after seeing these rows, so the in-sample fix counts are optimistic. As an out-of-sample check on false positives I ran the prototype over all 838 grader-wrong answered rows in the three files: it flips 72 rows (11 distinct gold/answer pairs); I read all 11 pairs and judge all of them correct answers (three are borderline: the Muholi title, Bayani, 2.1 million). That check is limited to rows `grade_v3` already calls wrong, and it says nothing about new rules interacting with future model outputs.

**Rule 1: name-core alternatives (causes A, B1, B2; 20 of 47 rows).** Accept the answer if `repaired` passes for any of: (a) for a person-valued question (question contains who/whom or a role noun such as scientist, player, coach) and a gold with no digits and at least three tokens, the first and last gold token only; (b) the gold with official-name affixes removed (republic, kingdom, commonwealth, federation, state, democratic, islamic, "the", "of"); (c) for a gold of the form "X, <county|parish|province|state|district|region|oblast|prefecture>", the part X, unless the question names both parts ("city and country"). Guards: the (a) rule still requires both surname and forename, so "John Smith" does not match "John Brown"; the (c) restriction to a trailing administrative word is what keeps "1 year, 161 days" and "subjective, psychological, ..." from matching on their first comma segment (an earlier, looser version did flip those two, which is why the container word is required).

**Rule 2: gold clean-up and alias (causes C, E, B3; 14 of 47 rows).** Before tokenising the gold: delete `https?://\S*` and `[n]` footnote markers; treat a quoted string inside a gold parenthetical ("Consumption") as an alternative gold; for a question about a title, publication, book or album, treat the part after the first colon as an alternative gold when it has at least three tokens. This also removes two data defects from the benchmark side, which is independent of the answerer.

**Rule 3: numbers with scale words, and an optional fuzzy name token (causes G, D; 2 + 6 rows).** (a) For a gold with an "acceptable range", expand "N million/thousand/billion" in the answer to a plain number before the range test (credits "2.1 million" in 2,006,000-2,217,157; "more than 137" is still rejected by the hedge check). (b) Optional and riskier: a gold token of at least five letters may be matched by an answer token that equals it plus at most one extra character (Bayan/Bayani). It cannot see Kathy/Kathryn or romanisation, and it can in principle equate real distinct names (Jonas/Jonah are not covered by the prefix form, but Alex/Alexa would be if the length limit were lowered), so I would use it to route rows to manual review rather than to credit them automatically.

Whichever rules are adopted, the between-system conclusions should be re-derived with the revised grader, because the present false negatives sit almost entirely in B1/B2/VKG rows of the RAG and oracle files (section 3).

## 7. Limitations

* The labeller is an LLM, not a human; no second labeller, so there is no inter-rater agreement figure. No web or model lookup was used, so factual calls rely on the gold string and on my own knowledge (for example that the gold "Niloufar Bayan" is a misspelling and that Randolph is the answer to the town question).
* Borderline labels are subjective (18 rows; section 4). A strict human could label spelling variants, nicknames, title prefixes and the romanised song title as wrong, which moves the false-negative count from 47 to 29.
* Rows are not independent: the same question is answered by several systems. Row-level confidence intervals are therefore too narrow; the question-level figures in section 4 are more honest.
* The sample is stratified by grader label, file and system, with a B0_raw cap. It estimates error rates inside those strata, not a population rate. The population-level estimate in section 4 is a post-stratification on cell sizes and is itself approximate.
* The closed-book file supplied only 23 of the 120 grader-correct rows; its false-positive interval is wide (0 to 14.8%).
* The false-positive finding (0/120) covers the answer types that occur in this data (names, years, numbers, dates, short phrases). Containment of all gold tokens is safe against wrong entities in this sample, but a longer multi-sentence answer that happens to mention the gold tokens was not present and is untested.
* I knew the stratum sizes (120/120) and, from the draw script, the per-cell counts before labelling, but never the label of an individual row. The grader code was read only after the labels were saved. Labels were written in four batches of 60 before any comparison.
* The strict grader (`vkg.tasks.matches`) was not evaluated separately here; only `grade_v3` (strict OR repaired) was.
