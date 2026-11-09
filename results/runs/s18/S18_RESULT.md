# S18 result: sealed L2 test of the L3-gated system (FRESH-3 + FRESH-4, n = 2000)

Run 2026-11-06 21:30 – 2026-11-07 04:10 on a dedicated RunPod RTX 5090, exactly as frozen in docs/S18_PROTOCOL.md.
After the run, all 25 frozen files and both test-set hashes re-verified unchanged (results/runs/s18/hashes_freeze.txt).
Raw output: results/runs/s18/S18_raw_fresh3_fresh4.md (vkg/s18_eval.py). Post-verdict analyses: results/runs/s18/post_analysis.py.

## Verdict
**L2 NOT MET.** G3 (L3 gate + all three sources agree) released 38.2% of questions (floor 35%: pass) with **20 graded-wrong
releases** in 2000 (raw SER 1.00%). With the false-credit correction, true errors ≤ 21, and the 97.5% upper bound is **1.60%**
(the threshold is 1%; ≤ 10 graded-wrong was needed). The secondary G2 is further away (68 wrong, upper 4.35%).

| system | coverage | correct | SER (raw) | SER 95% upper (CP) |
|---|---|---|---|---|
| G3: L3 gate, all 3 agree | 0.382 | 0.371 | 0.0100 | 0.0145 |
| G2: L3 gate, ≥ 2 agree | 0.550 | 0.516 | 0.0340 | 0.0414 |
| wiki_plain | 0.615 | 0.493 | 0.1220 | 0.1347 |
| combo_plain | 0.859 | 0.758 | 0.1005 | 0.1122 |
| MSany | 0.898 | 0.771 | 0.1270 | 0.1399 |

What the gate does achieve: it cuts SER **tenfold** against the best plain baseline (1.0% vs 10.1%) while still answering
37% of all questions correctly, and **all 20 errors are in stratum O** (original SimpleQA gold): stratum V (Verified gold),
n = 200, has 0 errors at 38.5% coverage.

## Predictions (priors fixed before the run)
| | prediction | prior | outcome |
|---|---|---|---|
| R1 | L2 met for G3 | ~35% | **fail** (20 > 10) |
| R2 | G3 coverage ≥ 35% | ~85% | **pass** (38.2%) |
| R3 | G3 raw SER on O > on V | ~70% | **pass** (1.11% vs 0.00%) |
| R4 | most released-but-wrong answers are A2 | ~75% | **pass** (15 of 20, provisional classification, see below) |
| R5 | gold audit finds ≥ 1 gold error | ~70% | pending (needs the user's audit) |
| R6 | L1-A (G2 vs wiki_plain) met | ~30% | **fail**: SER (a) pass, correct (b) pass, coverage (c) fail (−6.5 pts vs the −3 pt limit) |
| R7 | contaminated pages ≤ 5% | ~95% | **pass** (36 of 12,729 = 0.28%) |

The power estimate was optimistic: I expected about 8 errors (DEV + FRESH rate 0.4%); the sealed rate is 1.0%, 2.5 times higher.
That gap is the design-on-DEV optimism the protocol named as risk (a).

Other L1 rows (secondary, all NOT MET, coverage being the binding criterion every time): G2 vs combo_plain, G2 vs MSany,
G3 vs wiki_plain. The gate trades coverage for safety; the S15 L1 criteria do not allow a coverage drop over 3 points.

## L3 assumption audit of the 20 released-but-wrong G3 answers (provisional: my reading of the source context, not a gold audit)
The theorem held for every release (each is a verbatim, typed, period-consistent span of a hash-pinned page). Failures come from
the assumptions outside it. Classified after reading 150 characters around each released span:

| class | n | cases (released vs gold; where the span came from) |
|---|---|---|
| A2: the span answers something else | 15 | "90 seconds" for *how many rounds*; "700" inside "5,700 ha" for *how many centuries*; "Dota 2" ×2 for *which game version*; announcement date for *launch*; "1923 to 1929" (employment) for *Hellschreiber invented*; "turning to mathematics" for *entered to study* (physics); "Philip of Austria" for *betrothed in* (page: Low Countries); an organisation for *exhibition*; a religion list on *Singaporeans in the UK*; 1853 (relocation) for *founded* (page: 1761); 1847 (made a municipality) for *founded* (gold 1840); "based in Amsterdam" for *where Rest Energy was performed*; 20 Aug 1942 (another appointment) for *Minister of Justice*; "2" from a "2–2 home draw" for *EFL Cup goals* |
| A1: the page differs from gold | 2 | race time 03:02:25 vs 3:02:24; death date 17 vs 19 June 2019 |
| A3: type misparse | 1 | "year and month" parsed as YEAR, so "2018" for "November 2018" |
| near-correct, graded strictly | 2 | "asked to shave his head" vs "cut his hair"; "Ghulam Nabi Wani" vs "Ghulam Nabi Wani Sogami" |

End-to-end, P(wrong | released) = 20/763 = 2.6%. A2 is the dominant term of the union bound (ε_A2 ≈ 15/763 ≈ 2.0% of releases);
most A2 cases are spans from a sentence that has nothing to do with the question, on the right page.

## What this means for L2 (analysis after unsealing; FRESH-3 and FRESH-4 are now used)
- At the observed 1.0% rate no sample size can pass; the true rate has to be about 0.5% or lower, and then n ≈ 2000 is enough.
- **Draft gate checks, measured after unsealing** (vkg/l3_checks2.py; results/l3/checks2_eval.md, checks3_eval.md). These were designed on
  these 20 errors, so the S18 numbers are optimistic; DEV and FRESH were unchanged by them (0 blocked) except V6.
  | gate | G3 released | G3 wrong (SER) |
  |---|---|---|
  | V1-V4 (frozen) | 763 (38.2%) | 20 (1.00%) |
  | + V2' whole numbers ("700" inside "5,700"), V3' VERSION type and "year and month", V5 unit = counted noun | 758 (37.9%) | 15 (0.75%), 0 correct blocked |
  | + V6 sentence support, ≥ 1 question word in the span's sentence | 727 (36.3%) | 13 (0.65%) |
  | + V6 with ≥ 2 words | 599 (29.9%, below the floor) | 9 (0.45%) |
  V2', V3' and V5 are clean wins (5 errors, no correct answer lost). V6 is a blunt instrument: errors among what it removes run only about
  2× the base rate, so lexical overlap does not separate A2 well. None of these reaches the needed ~0.3% at ≥ 35% coverage.
- **Second reader and entailment check, measured after unsealing** (results/shared_eval/TWO_READER.md, results/l3/entail_check.md,
  results/l3/combo_eval.md; all post hoc on these sets):
  | system | G3 released | G3 wrong (SER) |
  |---|---|---|
  | V1-V4 + Phi-4 cautious veto (release only if Phi-4's own combo answer agrees) | 736 (36.8%) | 10 (0.50%) |
  | V1-V5 draft + Phi-4 cautious veto | 735 (36.7%) | **9 (0.45%)** |
  | V1-V5 + span-entailment (Phi-4 and Gemma) + veto | 606 (30.3%, below the floor) | 7 (0.35%) |
  Gemma 3 12B as the veto reader is much weaker (20 → 16). The pre-registered entailment predictions E1 and E2 **failed**:
  the check removes 15-19% of correct releases. Of the 9 errors left, 4 are gold or strict-grading disputes (a floor of about
  0.2%) and 5 are misreadings of a nearby fact that every reader shares. Design consequences: docs/S19_DESIGN.md.
- A new sealed test is still possible: 1,526 original SimpleQA items are untouched. Stratum-O gold noise remains a structural
  headwind: 6 of 20 errors here are gold disputes or strict grading. Those count against the system under the gold-relative rule.

## Costs
Wall time 6.7 h (estimate was 1.5–2 h). Per set: evidence about 60–78 min, generation about 20 min, judge about 95 min
(2,373 and 2,419 new labels), all on one 32 GB card. Serper: 994 credits used; 6 FRESH-4 items had no web search (budget rule), as planned.
