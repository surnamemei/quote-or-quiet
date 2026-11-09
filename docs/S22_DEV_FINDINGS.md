# S22 DEV: where the frozen S19 system loses coverage (2026-11-08, design data only)

Scripts: results/runs/s22/abstain_dev.py (abstain_dev.md), cf_dev.py (counterfactual rules). Cached labels only; DEV sets
mintaka_dev (200) and popqa_dev (300). S21 test sets are not used for design.

## Abstention breakdown (frozen S19 H1 system)
| reason | Mintaka n (candidate correct / wrong) | PopQA n (correct / wrong) |
|---|---|---|
| released | 71 (69 / 2) | 59 (53 / 6) |
| support 2 | **85 (58 / 27)** | **156 (79 / 77)** |
| support 1 | 11 (4 / 7) | 29 (6 / 23) |
| no candidate | 8 | 41 |
| gate: no span in pinned documents | 18 (18 / 0) | 10 (7 / 3) |
| gate: V checks | 6 (6 / 0) | 1 (0 / 1) |
| Phi-4 veto | 1 | 4 |

## Findings
1. **Answer-format losses at the gate are small.** Full-sentence reader answers and date formats block about 12% of Mintaka DEV
   (all candidates correct). Extracting the longest gate-accepted n-gram recovers 5 (coverage 0.355 -> 0.380, +1 error: the
   extractor picked the verb "cast"). On PopQA it adds 2 releases, both wrong (ambiguous titles). A clean fix is a short-answer
   prompt, not n-gram heuristics. Not enough on its own to clear the 0.35 floor on test (0.310 + about 2.5 points).
2. **Support 2 cannot be admitted with the existing filters.** Admitting support-2 candidates through the same gate and veto
   adds 19-20 releases on Mintaka with 8-9 wrong (about 45%), on PopQA 28 with 10-15 wrong. Gate and Phi-4 do not separate
   right from wrong here: support carries the precision.
3. **Support 2 is in practice one source.** 51 + 19 of the 85 Mintaka support-2 items are web_plain + web_cautious + combo agreeing
   with both wiki readers disagreeing; the combo passage contains the web pages, so the agreement is not independent.
4. **The local wiki retrieval misses the right page.** In 69 of 85 Mintaka support-2 items (133 of 156 PopQA) the kept web results
   name an en.wikipedia.org article that exists in the local FineWiki snapshot but is not among the localwiki.search top-5 titles
   (example: "What year did the second Punic War begin?" -> top-5 "Punic people", "Victoria (mythology)", ...; no "Second Punic War").
   Coverage is limited by retrieval for the wiki source, not by the readers.

## Experiment launched: wiki-pin (results/runs/s22/s22_run.py, run_pin.sh)
Wiki evidence pins the web-named Wikipedia articles first (kept URLs only, local snapshot, contamination check), then fills to 5
with the original search. Web evidence and web generations reused from S19. Phi-4 and alias labels recomputed. Expected: more
support-3 items and gate passes on Mintaka; risk: PopQA ambiguous titles pinned to the wrong namesake (e.g. "Aida" -> the opera).
Pins on DEV: Mintaka 178/200 items get at least one pinned page, PopQA 281/300.
Independence caveat: a pinned page is often the same article the web reader saw live; the L3 gate still verifies the span against
the pinned local document, but "support 3" then means less source diversity than in S19. To be reported with any result.

## Time-sensitivity rule (results/runs/s22/temporal.py)
Motivation (disclosed): reading the S21 Mintaka TEST errors after unsealing showed 14 of 28 graded errors on time-dependent
questions whose gold predates the 2025 snapshot. Rule, question text only: flag questions about incumbents, "current / latest",
present-tense counts ("how many ... has / have won"), and all-time records, unless the question carries an explicit year; quoted
titles are ignored. Flagged questions get no Verified answer (Qualified "as of the snapshot" or Unresolved).
- Flag rates: SimpleQA DEV 3/300, FRESH 0/200, FRESH-5 5/1526, Mintaka DEV 20/200, PopQA DEV 0/300.
- DEV releases removed: Mintaka 3 of 71 (all correct), PopQA 0. DEV shows the cost (about 1.5 points of Mintaka coverage), not the benefit.
- On the S21 Mintaka test outputs (biased check, rule written after reading those errors, not tuned on them): an earlier, looser
  version flagged 47 of 620 releases, 13 of them graded wrong. The rule cannot reach L2 alone; it lowers coverage. It only helps
  together with a coverage gain.

## CPU proxy for wiki-pin, and the gold ceiling on Mintaka
Gate + Phi-4 on the pinned pages for support-2 candidates (no regeneration; an upper-bound proxy): Mintaka DEV 45 would pass,
34 correct / 11 graded wrong; PopQA DEV 66, 38 / 28. Of the 11 Mintaka "wrong" ones, read on DEV: stale gold (Celtics titles,
Bush albums, McGwire's age), wrong gold (youngest Super Bowl-winning QB is Roethlisberger, not Mahomes; 2014 Album of the Year
ceremony), ambiguous (2007 vs XLII MVP, "most Oscars", first Mario game, Beatles formation year, "civil war"), and about 1-2 real
errors (Australian House of Representatives, 150).
**Consequence.** Gold-relative L2 on Mintaka is out of reach for any system that reads a 2025 source: on S21 test about 26 of 620
releases (4.2%) are stale, wrong or ambiguous gold by an unblinded reading; at 35% coverage that alone is about 29 graded errors
in 2000, against an allowance of 10. Either the primary endpoint is blind adjudication (as the protocols allow, but never done so
far), or the test distribution must have gold that is as current as the source and checked (error rate well below 1%).

## Gate rejections, read one by one (Mintaka DEV, 24 items, all candidates correct)
- 17 "no span found": the local top-5 titles are off-topic ("Taj Mahal" -> albums by the musician Taj Mahal; "Battle of
  Hastings" -> "1869 Hastings by-election"; "Germany's largest city" -> lists of places in Arizona). Retrieval again; pinning
  addresses these too. Full-sentence answers are a minority (5).
- 3 V3 type: "218 BC" rejected as YEAR; full dates ("November 15, 2001") rejected where the question was typed YEAR.
- 4 V4: pages like "1979 in baseball" carry a year not in the question; the check works as intended.

## Reader outputs lost to truncation (pipeline defect present since S17)
The 4B often answers the plain prompt in a ```json fence with a long sentence; at the 40-token limit the JSON is cut before the
answer closes and parse() keeps only "```json" (raw outputs are not saved). Share of lost outputs, plain prompts:
Mintaka test web/wiki/combo 9 / 13 / 10%, PopQA test 12 / 22 / 20%, FRESH-5 6 / 13 / 7%, Mintaka DEV 10 / 10 / 8%.
Every lost output can cost a support vote. Fix in S22 variants: limit 128 tokens, fence-tolerant parse, a JSON cut before the
answer closes counts as no answer (results/runs/s22/s22_run.py parse2).

## Variants queued (results/runs/s22/run_s22dev.sh, starts when the GPU lock frees)
- tok: token/parse fix only, S19 evidence; pin: token/parse fix + wiki pinning. All six 4B outputs and Phi-4 regenerated (128
  tokens), alias labels added. Scorer: results/runs/s22/score_variants.py (variants_dev.md). S19 baseline on DEV: Mintaka 71
  released / 2 wrong (0.355), PopQA 59 / 6 (0.197); with the time rule Mintaka 68 / 2 (0.340).

## L1 at matched coverage (post hoc, descriptive; existing outputs, no new runs)
Strong equal-budget baseline: combo_plain answers ranked by how many of the other readers agree with them (6 4B outputs + Phi-4,
0-7), cut at the system's exact coverage. Gold-relative errors at the same coverage:
| set | coverage | system k | agreement-ranked combo_plain k | ratio |
|---|---|---|---|---|
| FRESH-5 | 0.372 | 4 | 9 | 0.44 |
| Mintaka test | 0.310 | 28 | 26 | 1.08 |
| PopQA test | 0.191 | 17 | 19 | 0.89 |
| Mintaka DEV | 0.355 | 2 | 2 | 1.00 |
| PopQA DEV | 0.197 | 6 | 7 | 0.86 |
At equal coverage the gate + veto does about as well as "all readers agree" on Mintaka and PopQA; only FRESH-5 shows a halving
(point estimate, 4 vs 9, not significant). The gate's contribution is the certificate (verbatim span on a pinned page, L3),
not fewer errors at equal coverage. L1 against this baseline is unlikely in S22 unless a component removes errors on which all
readers agree (stale gold, wrong entity) — the time rule and a Qualified state target exactly those. Plan: add L1 to the S22
protocol as a pre-registered secondary on the same single run (no extra GPU), with an honest prior; the adjudication sheet must
then include the baseline's errors at matched coverage too, so both sides are adjudicated alike.

## DEV variants measured (2026-11-08 19:40; results/runs/s22/variants_dev.md, entity_dev.md, pin_errors_dev.json)
- tok (128 tokens, fence-tolerant parse): lost outputs 61 -> 0 (Mintaka DEV), 175 -> 0 (PopQA DEV), but coverage unchanged on
  Mintaka (71 / 2 wrong) and +3 on PopQA. Necessary hygiene, not a coverage lever.
- pin: Mintaka DEV 118 released (0.590), 11 graded wrong; PopQA DEV 126 (0.420), 36 wrong. Mintaka errors are mostly gold issues
  (stale, wrong, two readings) plus ~3 real (Australian House of Representatives; "The Stealth" -> the film; "Salaryman" ->
  Salary Man Kintaro). PopQA errors are almost all namesakes: pinning picks the famous work (After Hours, The Fog, Some Like It
  Hot), PopQA asks about an obscure one.
- Subject-ambiguity rule (entity_dev.py; longest title core found in the question has more than one page and the release
  page's qualifier is not named): removes 26 of 36 PopQA pin errors at half the coverage; on Mintaka it mostly removes correct
  releases (famous works have namesakes).
- Best Mintaka DEV combination: **S19 releases ∪ (pin releases that are neither time-sensitive nor subject-ambiguous)**:
  94 released (0.470), 6 graded wrong, of which about 5 look like gold issues on reading. Further tuning on 200 items would overfit.
- Rough S22 pass probability on 1800 new Mintaka items: coverage ~0.42 expected (P(≥0.35) high); adjudicated errors 6-10
  expected against k ≤ 8: about 50%. Next: use the closed S21 Mintaka test (2000 items, now design data for S22) for a much
  tighter estimate: pin variant + blind adjudication pilot. PopQA stays descriptive.

## Certifiable ceiling and the format relaxation (2026-11-08 21:00; ceiling_dev.py, gate_fmt.py, fmt_dev.py)
- Gold verbatim (any alias, date variants) on the pinned pages: Mintaka DEV 87% with pin titles (58% with S19 titles), PopQA DEV
  62% (37%), SimpleQA DEV 58% (S19 titles). Count/compute questions are about 11% of Mintaka generic and mostly verbatim too, so
  the verbatim condition is not the binding constraint on Mintaka; selection is.
- Of the Mintaka DEV pin items with gold on the page but not released, the largest group failed the gate only on the surface
  form: the max-support candidate is the first reader's full sentence ("The Green Bay Packers won the first Super Bowl.") while the
  other readers give the short form; and "when" questions with full-date answers fail the YEAR grammar.
- Format relaxation (user-approved): try every agreeing surface form longest first plus date variants; YEAR accepts era years
  ("218 BC") and, for "when" questions, full dates. Claims stay verbatim and typed.
  | set | frozen gate | format-relaxed |
  |---|---|---|
  | SimpleQA DEV (S19) | 138 / 1 wrong | 148 / 2 wrong ("Doab" vs "Sindh Sagar Doab") |
  | Mintaka DEV (S19) | 71 / 2 | 80 / 2 |
  | Mintaka DEV (pin) | 118 / 11 | 135 / 11 |
  | PopQA DEV (pin) | 126 / 36 | 141 / 39 (namesakes) |
- Combination rule (S19 ∪ pin-not-time-not-ambiguous) with the format gate, Mintaka DEV: **108 released (0.540), 6 graded wrong**
  (same 6 as before; about 5 gold issues on reading). Frozen gate: 94 (0.470), 6.

## Closed S21 Mintaka test (2000) as design data: combination rule + blind web adjudication (2026-11-08 22:40)
Scripts: results/runs/s22/combo_s21test.py (combo_mintaka_test.md, mintaka_test_releases.jsonl), adj_unblind.py
(mintaka_test_adj_result.md), quote_check.py. Pin variant regenerated on all 2000 items (run_s22_s21test.sh).
- Combination rule (S19 ∪ pin-not-time-not-ambiguous, format gate): **1005 released (coverage 0.502)**, 697 from S19 + 308 from
  pin; **63 graded wrong** (35 S19 part, 28 pin part). Pin alone: 1280 (0.640), 97-98 wrong.
- Blind sheet 251 rows (63 system errors, 63 baseline-wrong, 63 system-correct, 62 injected-false), split into 4 consecutive
  parts for 4 fresh general-purpose agents (sheet + rubric only; WebSearch/WebFetch; verbatim quotes required).
- Quote-check bug found and fixed: HTML tag boundaries produced "plath ." vs quote "plath." so correct quotes failed (first pass
  found 65 of 141). Comparison now on letters/digits only, in order (word order still exact): 119 of 141 found, 22 reverted.
| kind | n | gold wrong | answer wrong | both acceptable | ambiguous | cannot tell | removed |
|---|---|---|---|---|---|---|---|
| system | 63 | 35 | 7 | 19 | 2 | 0 | 54 |
| baseline-wrong | 63 | 17 | 31 | 6 | 4 | 5 | 23 (0.37) |
| system-correct | 63 | 0 | 0 | 42 | 0 | 21 | - |
| injected-false | 62 | 0 | 62 | 0 | 0 | 0 | 0 |
- **Validity 62/62 (VALID). Adjudicated k = 9 of 1005** -> corrected E = 10, CP 97.5% upper 0.92% at n = 2000: would pass L2
  at coverage 0.502 (design data, not a test).
- Unblinded reading by this session (not blind, the builder): most removals are clear stale gold (Kenya/Philippines/Lebanon
  presidents, Arkansas governor, Brady records, LeBron titles, Rams Super Bowls, Swift Grammys) or plain gold errors (Streep 1939,
  1988 draft pick, Desert Storm 1990, Rocky III opponent, Gore popular vote). About 4 look lenient: copper vs brown (Statue of
  Liberty), 42 vs 35 (youngest president), "14th century" vs 1368, Tennis for Two vs Pong. Strict count k ~ 13 (upper 1.17%: fail).
- Remaining real errors: Japan's "Senate", Franco-Dutch war "1678", Pizarro 1526, "a running bounce", Streep for "his
  performances", Thor 9 films, plus Resident Evil Requiem, which is wrong only against the August 2025 reference date (the web
  evidence is live). For S22 the reference date should be the run date.
- Short-answer rewrite (short_dev.md): with the format gate, +1 release on Mintaka DEV, +1 wrong on SimpleQA DEV, PopQA mixed.
  **Dropped from S22.**
- **S22 pass estimate (1800 new Mintaka items, k ≤ 8):** expected adjudicated k ≈ 9 × 0.9 ≈ 8 (Poisson P(k ≤ 8) ≈ 0.55), coverage
  ~0.50 (safely above 0.35). With adjudicator leniency uncertainty (±4), about 45-55%. Levers that do not touch precision tuning:
  reference date = run date; a second independent blind adjudicator, with an error removed only if both agree (more robust, but
  fewer removals). Neither moves the odds much; the run is a coin flip on k.

## Strict re-adjudication of the same 251-row sheet (2026-11-08 23:30; mintaka_test_adj_result_strict.md)
Rubric v2 (scratchpad rubric2.txt): added "matches gold"; "both acceptable" only for same-thing-different-name or two defensible
readings each sourced; vaguer/coarser answers are "answer wrong"; reference date = today (2026-11-08). Two independent blind
adjudicators (8 fresh agents); a removal needs BOTH to remove it, with quotes found by the script (adj_combine.py).
- Validity: injected-false 62/62 caught by both. System-correct decoys 61/63 "matches gold" (2 called answer wrong).
- **System errors kept: k_adj = 29 of 63** (lenient single-adjudicator run: 9). Composition of the 29, my reading: about 9 real
  wrong answers (Japan "Senate", Franco-Dutch "1678", Pizarro 1526, "a running bounce", Game Boy "designer", Thor 9 films, Parma
  population, 14th century, Greek Dark Ages), about 9 genuinely ambiguous questions (all-time scorer without a sport, who led
  Germany after Hitler, Baftas start, BCS 2008, NC 2016, first Patternist book, youngest president, first video game, Grammy
  2017), about 6 where one adjudicator verified the answer but the other could not quote it (Streep 1949, Swift 14 Grammys,
  Lee Morgan hard bop, Menes/Narmer, Super Bowl host, Cleopatra) and about 5 splits between the adjudicators.
- Consequence: floor with only real errors plus ambiguous questions is about 18 of 1005 (1.8%); the L2 allowance is 10 of 2000.
  Mintaka cannot be passed as a plain-answer L2 benchmark under this rubric. The ambiguous-question errors are exactly what a
  Qualified output should absorb (the L3 fork's layer); the real-wrong ones are about 0.9%.

## New pipeline on FRESH-5 (SimpleQA, closed after S19; design data only; 2026-11-09 02:00; combo_fresh5.md)
Pin variant regenerated on all 1526 items (S19 web evidence reused), combination rule with the format gate:
- Released 727 (coverage **0.476** vs 0.372 for the frozen S19 system); graded wrong **14** vs 4 (frozen). S19 part (601 releases): 6 wrong
  (the format gate adds 2 date/name variants: "Gerald Andan" for "Gerad Yakubu Andan", "1 May 2023" for "April 30, 2023");
  pin part (126 added releases): **8 wrong, 6.3%**. Pin alone: 738 released, 13 wrong.
- The 8 pin errors are real wrong answers (Callisto for Jupiter's third-largest moon, Raymond Fuoss, Jean-Pierre Demailly, Emily, 5
  siblings, 1886 for 1868, a wrong commissioning date, a wrong high school), not gold issues. On Mintaka the pin errors hid among
  gold issues; on clean SimpleQA the precision of the pinned-page releases is poor. A pinned page is the page the web reader
  already saw, so "support 3" carries less independent evidence than in S19.
- k = 14 against k ≤ 6 allowed at n = 1526: the new pipeline would fail L2 on FRESH-5 even if adjudication removed a few errors.
- Decision (rule set in advance): no S22 run. The frozen S19 system stays the system of record; its L2 pass on SimpleQA stands.
  Pin and the format gate are reported as coverage-raising and precision-lowering. The sealed 1800 Mintaka items stay sealed.

## Frozen S19 system's 28 Mintaka test errors under the strict blind adjudication (2026-11-09; post hoc, no new run)
All 28 frozen-system errors (S21 adjudication key, kind "system") are among the 63 system rows of the strict sheet. Strict verdicts
(adj2_comb.csv): gold wrong 16, both acceptable 3 (removed 19); answer wrong 3, ambiguous 2, cannot tell 4 (kept 9).
k_adj = 9 of 620 releases at n = 2000: E = 10, CP 97.5% upper 0.92% (< 1%), coverage 0.310 < 0.35 -> coverage, not precision, is the
binding constraint for the frozen system on Mintaka. Added releases of the combination rule: 385, of which 20 strict-adjudicated
errors survive (5.2%); on FRESH-5 159 added releases, 10 errors (6.3%). Used in paper/manuscript.md v0.2 (Tables 2 and 3).

## S23 (2026-11-09): independent retrieval on DEV, and a Learn-then-Test baseline
- Independent retrieval (title-index mention matching + title-re-ranked BM25, no web-named pages): docs/S23_DEV_RESULT.md. Pooled added releases
  73 with 5 wrong (6.8%), rule (<= 3%) not met, line stopped. Variant-only additions: 2 of 31 (6.5%) vs pin 11 of 53 (21%) on the two sets both ran.
- Conformal-style baseline (results/runs/s23/conformal_base.md): LTT on the agreement score (0..6), calibration 2,500 SimpleQA design items,
  selected the strictest threshold (all six other readers agree): FRESH-5 coverage 0.362, 9 wrong, corrected upper 1.20% (fails the L2 rule);
  the frozen system has 0.372, 4 wrong, 0.76%. Calibration predicted 0.28% SER (7/2500), observed 0.59% (9/1526).
