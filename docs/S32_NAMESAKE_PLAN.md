# S32: namesake detector and a "Qualified" answer (plan, 2026-11-09, before running)

Goal A allows three states: Verified, Qualified, Unresolved. S30 and S31 found that many remaining errors are questions whose subject names more than one thing (Heat 1995 vs 1986, Dude, Some Like It Hot). A Qualified answer states the reading: "For Heat (1995 film): Michael Mann." It is a true statement even when the benchmark meant the other film.

Detector (deterministic, no gold, no model call; pinned title index results/runs/l3/titles.db, 6.6 M titles):
1. Subject: the longest word n-gram of the question (1 to 8 words, not only stopwords) that equals a normalised title core in the index.
2. Pages of the subject: titles whose core equals the subject ("Heat", "Heat (1995 film)", "Heat (1986 film)") plus comma titles that start with it ("Marathon, Greece", "Marathon, Florida"), excluding "(disambiguation)" pages, keeping only pages of at least 3,000 characters.
3. Reading used: the page the answer was verified in, if it is one of the subject's pages; else the first retrieved Wikipedia title that is.
4. Variant A (any kind): the question is ambiguous if the subject has at least one other page besides the reading used, and the question does not contain the words of that page's qualifier.
   Variant B (same kind): as A, but the other page must share the last word of the qualifier with the reading used (film/film, song/song), or both be comma titles (places).
5. Output: if ambiguous and the reading is known, the answer is released as "For <reading title>: <answer>"; if ambiguous and the reading is unknown, it is not released.

Measured on the design sets (same 1,144 questions as S30/S31), on the frozen releases and on the S31 best cell of the two-source pool:
- cost: share of gold-correct releases that get a qualifier (the user's request is short answers; the target is at most 15%);
- benefit: how many gold-wrong releases get a qualifier whose stated reading makes the answer true (read by the author; listed);
- reading errors: qualified answers whose stated reading is not what the answer is about.
This is a design study; nothing is claimed as a test result. If a variant meets cost <= 15% and qualifies at least half of the namesake-type errors, it is frozen and tested on the S29 sealed outputs after the primary analysis there, as a secondary analysis.

## Design iterations and the frozen rule (added before the test run, 2026-11-09)
Three changes were made on the design sets, all visible in results/runs/s32/s32_namesake.py: (1) the subject is the core of an evidence title that the question names, with a fallback to the longest run of capitalised words that is a title core (the first version picked words such as "screenwriter" or "the capital"); (2) variant D was added: another page of the subject counts only if its text contains every content word of the question (5-letter stems, subject removed) and does not contain the answer; (3) a bug fix (the answer locator returns a generator, so the "does not contain the answer" test was always false until fixed).
Design result, frozen releases plus the S31 cell (472 rows, 454 gold-correct, 18 gold-wrong):
- variant A flags 25% of correct answers (fails the cost target); variant B flags almost nothing;
- variant D flags 17: 4 gold-wrong (Dobra River, Jordan as capital of Guimaras, Legion, Heat: all namesakes) and 13 gold-correct (2.9% of correct).
- the stated reading is unreliable: 9 of the 17 have no reading among the retrieved titles, and 3 of the correct ones would name a wrong reading (a given-name or surname page). So the Qualified output is not reliable from the title index alone; D is frozen as a withholding rule (flagged answers become Unresolved), not as a qualifier.
Frozen: s32_namesake.py, sha256 b01aaf61def31a1356a3efc3fe02f48832f30dc18d78303a96a887433ddd3f62, variant D used as "withhold if flagged".
Test (one run, secondary analysis): the frozen releases on FRESH-5, Mintaka test and PopQA test (already reported; never used in the S32 design). Pass rule: at least 5 releases flagged, at least 20% of the flagged releases gold-wrong, and at most 5% of the gold-correct releases flagged. The S29 sealed set cannot test this rule, because its subjects were chosen to have exactly one page in the title index.
Crash fix before the test result was seen (2026-11-09): the comma-title split failed on a title without a space after the comma (IndexError on FRESH-5); changed to split on ',' and strip. Design-set result rechecked and unchanged (17 flagged, 4 gold-wrong). New sha256 20e9df6b3f4fbad8dc497c74497c25a03ca16e03fea9545e34d0bee4d7a1a6b8.
