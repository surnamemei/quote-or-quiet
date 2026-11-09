# S36 L1 with truth-relative errors

Decoys called wrong by both reviewers: 15/15 (VALID)

Primary (gold-wrong rows, both reviewers 'wrong'):
- system truth-relative errors k_sys = 3
- baseline expected truth-relative errors at exactly matched coverage E[k_base] = 8.04
- discordant: system-only 1.86, baseline-only 6.90
- share of random edge draws with k_sys > 0.5 k_base: 0.0192
- one-sided binomial on discordant errors (H0: P(system-only) >= 1/3): 2 of 9, p = 0.3772
- L1 verdict: NOT MET

Per set (gold-wrong rows): system errors / baseline errors (expected at matched coverage)

- fresh5: gold-wrong system 4 -> truth errors 0; baseline truth errors 4.61 (gold-relative at matched coverage 9.6)
- mintaka_test: gold-wrong system 28 -> truth errors 1; baseline truth errors 1.28 (gold-relative at matched coverage 25.9)
- popqa_test: gold-wrong system 17 -> truth errors 2; baseline truth errors 2.15 (gold-relative at matched coverage 17.9)

Gold-correct samples: system-only 0/30 wrong, baseline-only 0/30 wrong

Truth-relative errors (both reviewers):

- [popqa_test] who ['base', 'sys'] score 5 | Who is the author of Lear? | ans Edward Lear | gold ['Edward Bond']
- [mintaka_test] who ['base', 'sys'] score 5 | Number of movies in the Thor franchise? | ans 9 | gold ['3']
- [fresh5] who ['base'] score 5 | In which year did a mouse eradication program first commence on the volcanic island called Gough Island in the South Atlantic Ocean? | ans 2020 | gold ['2021']
- [fresh5] who ['base'] score 6 | By which year and month was WhatsApp downloaded by only a handful of Fishman's Russian-speaking friends? | ans 2009 | gold ['June 2009']
- [popqa_test] who ['base', 'sys'] score 5 | In what country is Fin? | ans Finland | gold ['Iran', 'Islamic Republic of Iran']
- [popqa_test] who ['base'] score 5 | Who was the screenwriter for Face? | ans Mike Werb and Michael Colleary | gold ['Tsai Ming-liang', 'Ming-liang Tsai']
- [fresh5] who ['base'] score 6 | What was the year and month when The Atlantic reported that the Centers for Disease Control and Prevention (CDC) were conflating the results of two different types of coronavirus tests that diagnose current coronavirus infections and measure whether someone has ever had the virus? | ans 2020 | gold ['May 2020']
- [fresh5] who ['base'] score 6 | What month, day, and year did the Durban-based shack-dwellers' movement Abahlali baseMjondolo take the KwaZulu-Natal government to court over their controversial Elimination and Prevention of Re-Emergence of Slums Act? | ans May 2009 | gold ['14 May 2009']
- [popqa_test] who ['base'] score 5 | In what country is Earl? | ans Earl is a British noble title, originating in England and used in the United Kingdom and Ireland. | gold ['United States of America', 'the United States of America']
- [fresh5] who ['base'] score 6 | What were the month, day, and year John Stanhope was raised to the peerage as Baron Stanhope of Harrington? | ans May 1605 | gold ['May 2, 1605']
- [fresh5] who ['base'] score 5 | How many siblings did Elizabeth Spencer, Baroness Hunsdon, have? | ans Five | gold ['6']
- [mintaka_test] who ['base'] score 6 | When did Pizarro reach the Inca territory? | ans Pizarro reached Inca territory by 1526. | gold ['1532']
- [fresh5] who ['base'] score 5 | In which meiosis phase do the meiotic spindle fibers at each pole of the cell attach to each other's sister chromatids? | ans Metaphase I | gold ['Metaphase II']
- [popqa_test] who ['base'] score 5 | Who was the composer of Land of Plenty? | ans Jocelyn Pook | gold ['Leonard Cohen', 'Leonard Norman Cohen']

Disagreements between reviewers:

- [mintaka_test] gold_correct_sample A correct for one reading B correct | Who was the first Catholic presidential candidate? | ans Al Smith
- [mintaka_test] gold_wrong A wrong B correct for one reading | When did Pizarro reach the Inca territory? | ans 1526
- [mintaka_test] gold_wrong A correct for one reading B correct | Who won the Grammy's Album of the Year in 2017? | ans Adele

## Reading (2026-11-09)
- Pre-set rule: the point condition holds (3 <= 0.5 x 8.04) and the randomisation test holds (p = 0.019), but the binomial test on discordant errors does not (2 of 9, p = 0.38). The rule needed all three: **L1 NOT MET.** With 9 discordant errors the binomial test has little power; the result is a 63% lower point estimate that is not statistically established.
- Where the difference comes from: on FRESH-5 the baseline's truth-relative errors are mostly incomplete answers (a year where the question asks for year and month, or month and year where it asks for a day: WhatsApp, The Atlantic, Abahlali, Stanhope) and plain wrong facts (meiosis phase, siblings, Gough Island). The system's type check (V3, question type MONTH_YEAR or DATE) refuses incomplete answers, which is a mechanism, not luck. On Mintaka and PopQA the two rules make nearly the same truth-relative errors (1 vs 1.3 and 2 vs 2.2), because there both rules release mostly the same answers.
- All three system errors are shared with the baseline (Lear, Thor, Fin), so the system adds no error of its own in this sample.
- Reviewer inconsistency: the same Pizarro fact was judged once as "wrong" by both (the baseline's sentence answer) and once as split (the system's "1526"), so it counts for the baseline only. Counting it for both would make k_sys = 4 (still <= 0.5 x 8.04 = 4.02 and the discordant test weaker).
- Gold-correct samples: 0 of 30 wrong for each rule; the gold misses no errors that matter here.

## Next confirmatory test (fixed now, before any S29 sealed result is seen)
The S29 sealed run gets the same S36 procedure as an independent test: all gold-wrong releases of the system and of the baseline at exactly matched coverage (same edge interpolation), 30 gold-correct samples per rule, 15 decoys, two blind reviewers. L1 on S29 holds if k_sys <= 0.5 E[k_base] and the one-sided binomial on discordant errors rejects at 5%. It is reported on its own, not pooled with S36 (pooling after seeing S36 would inflate the error rate of the test). The S29 pilot suggests the two rules are close on that set, so the expected outcome is NOT MET; this is written down so it cannot be adjusted later.
