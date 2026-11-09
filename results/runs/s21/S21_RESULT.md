# S21 result: transfer test of the frozen S19 H1 system (2026-11-08)

Protocol: docs/S21_PROTOCOL.md (frozen 07:08). One run, test files never opened by this session. Raw: S21_raw.md; final: S21_final.md.

## Run
- run_test.sh failed on the first attempt (CUDA OOM on one 201,455-character mintaka_test web passage at VKG_MEM_FRAC 0.65);
  resumed with run_test_resume.sh at 0.88, the only change (deviation D1, DEVIATIONS.md). Generation, judge, Phi-4 and 2,948
  alias labels completed at 14:15. Frozen hashes re-checked after the run: 98/98 OK (hashes_check_after.txt).

## H1-M (single primary, mintaka_test, n = 2000): **FAIL**
- Released 620, **coverage 0.310 < 0.35 floor**; correct 592; graded-wrong k = 28; raw SER 1.40%; corrected 97.5% CP upper 2.08%.
- Fails on both conditions. The coverage failure alone decides it, so no adjudication outcome can change the verdict: even with all
  28 errors removed the coverage floor is missed. Primary = secondary = FAIL. The blind sheet (84 rows,
  S21_adjudication_sheet.csv; key kept apart) was offered for the descriptive error classes (P5) only and the user declined;
  S21_final.md is therefore final with the sheet blank (all "cannot tell"), as the protocol prescribes.
- By stratum: coverage 0.25 (history, politics) to 0.41 (books, video games); errors concentrated in sports (8), history, music,
  politics (5 each).

## Predictions (stated before unsealing)
| | prediction | prior | outcome |
|---|---|---|---|
| P1 | H1-M met | 12% | **not met** (as predicted) |
| P2 | coverage ≥ 35% | 50% | **not met** (0.310; DEV 0.355 was optimistic by 4.5 points, about 1.3 DEV sampling SD) |
| P3 | gold-relative SER ≤ 1.5% (k ≤ 30) | 75% | **met** (k = 28) |
| P4 | system SER ≤ half of combo_plain's | 90% | **met** (1.40% vs 12.85%; combo_plain answered 1776, wrong 257) |
| P5 | ≥ 1/3 of adjudicated errors ambiguous / both acceptable | 60% | **not assessed** (user declined adjudication on 2026-11-08; sheet left blank, all rows "cannot tell") |

## PopQA (descriptive, popqa_test, n = 2100)
- Released 401, coverage 0.191; wrong 17; raw SER 0.81% (upper 1.35%). combo_plain: answered 1561, wrong 505 (24.0%).
- Predictions: coverage < 0.35 **met**; low-popularity tercile coverage below high **not met** (low 0.253, mid 0.150, high 0.170);
  ambiguous subjects the largest error class **met** (post hoc classes by this session, below).
- Error classes (17, read after unsealing, post hoc):
  - ambiguous subject (8): Turin, Lima (gold: US towns), Fin, Lear, Shaft, Barabbas, Exposed, Hook;
  - gold incomplete / both acceptable (6): Gordie Gosse, Alex Krieps, Javier Alva Orlandini (occupations), Dick Grayson (biological
    father John Grayson), Gilbert Bodart (Ougrée is part of Seraing), Science-Fantasy Quintette (co-author);
  - ill-posed (1): genre of a person (William Keepers Maxwell Jr.);
  - plausible real errors (2): Brain Slaves genre, Unprecedented producer.
- A_S check (string match of any gold alias in the release page): correct releases 371/384 (Mintaka 559/592); wrong releases 11/17
  (Mintaka 14/28). Many "wrong" releases come from pages that also name the gold, consistent with entity / reading-choice errors
  rather than unsupported claims.

## Tiered answering (Kimi, descriptive; E:\Models\halluc_runs\TIERED_S21_TEST.md, frozen scripts, hashes unchanged)
| set | tiered cov / correct / SER | tier 1 alone | wiki_plain | combo_plain | tiers 1 / 2 / abstain |
|---|---|---|---|---|---|
| mintaka_test | 0.758 / 0.673 / 8.50% | 0.310 / 0.296 / 1.40% | 0.657 / 0.494 / 16.30% | 0.888 / 0.759 / 12.85% | 620 / 896 / 484 |
| popqa_test | 0.567 / 0.424 / 14.29% | 0.191 / 0.183 / 0.81% | 0.460 / 0.299 / 16.19% | 0.743 / 0.503 / 24.05% | 401 / 790 / 909 |
L1-A (descriptive) NOT MET on both sets, criterion (a) failing (Mintaka +0.0035, upper +0.0185; PopQA +0.0619), as the prereg
predicted. Tier 2 (reader agreement) carries almost all errors (Mintaka 142 of 170); tier 1 matches H1-M raw exactly.
(The frozen script's header still says "PRIMARY L1-A"; PREREG_S21_TIERED.md, withdrawn before the freeze, governs.)

## Mintaka errors read after unsealing (post hoc, by the system's author, NOT blind; decides nothing)
The user declined blind adjudication, so the primary endpoint stays gold-relative. For interpretation only, all 28 were read:
| class | n | items |
|---|---|---|
| gold out of date; released answer is current in the Aug 2025 snapshot | 14 | presidents of Kenya (2 items), Philippines, Lebanon; governor of Arkansas; Brewers manager; NFL career passing yards; career triple-doubles; Taylor Swift's Grammys; LeBron James's championships; Rams' Super Bowls; NBA franchises without a Finals appearance; longest Super Bowl field goal; latest Resident Evil title |
| gold wrong regardless of date | 3 | 1988 NBA first pick (Danny Manning; gold names the 1998 pick); Black Eyed Peas 2005 Grammy ("Let's Get It Started"); start year of Operation Desert Storm (1991) |
| both acceptable / ambiguous question | 9 | Cleopatra's dynasty (2 items: Ptolemaic vs Macedonian); first pharaoh (Narmer vs Menes); "Grammy Album of the Year in 2017" (ceremony vs award year); Rocky III opponent; Minecraft release (2009 public vs 2011 full); first Patternist book (publication vs internal order); Pizarro's arrival; Lee Morgan's style |
| plausible real errors | 2 | "another name for Harp" (blues harp vs harmonica); number of Thor films |
Mintaka (built 2021-22) asks many time-dependent questions ("current president"); the system reads a 2025 snapshot. Gold-relative
selective risk is 28/620 = 4.5% (FRESH-5: 4/568 = 0.7%), so per released answer the measured precision is about 6x worse than on
FRESH-5; this unblinded reading suggests most of that gap is benchmark time-stamping and gold noise rather than system error. Only a
blind adjudication could make that a result. Neither reading changes H1-M, which fails on coverage.

## Reading
1. The S19 L2 PASS does not transfer to Mintaka or PopQA at the 35% coverage floor. Per item, SER is 1.4% and 0.8%, about 9x and
   30x lower than combo_plain; per released answer (selective risk) it is 4.5% and 4.2% gold-relative, against 0.7% on FRESH-5 and
   14.5% / 32.4% for combo_plain. On Mintaka most of the gap is stale or wrong gold (post hoc, above).
2. The dominant residual error on templated questions is the entity slot (ambiguous subject), as DEV indicated; the scope of the
   S19 claim is SimpleQA-style, unambiguously worded questions.
3. Next (DEV only): a Qualified output state that names the assumed entity, and coverage work on comparative / count questions.
