# S19 design note (DRAFT, 2026-11-07 ~07:55; not frozen, nothing run on the untouched pool)

The last untouched pool is **1,526 original SimpleQA items** (stratum O, not in Verified; docs/FREEZE.md). This note decides
whether it is worth spending on a new sealed L2 test now, and what would have to change first. All numbers below come from
DEV + FRESH (design data) and the S18 sets (used since the verdict, so every S18 number for a new component is post hoc).

## What the overnight analyses found
Source tables: results/l3/checks2_eval.md, results/shared_eval/TWO_READER.md, results/l3/entail_check.md, results/l3/combo_eval.md.

| system (S18 sets, n = 2000; post hoc) | coverage | graded-wrong | SER |
|---|---|---|---|
| G3, gate V1-V4 (the frozen S18 system) | 38.2% | 20 | 1.00% |
| G3, gate V1-V5 draft (V2' whole numbers, V3' VERSION / year+month, V5 units) | 37.9% | 15 | 0.75% |
| G3, V1-V5 + Phi-4 cautious second-reader veto | **36.7%** | **9** | **0.45%** |
| G2, V1-V5 + span-entailment (Phi-4) + Phi-4 veto | 36.6% | 11 | 0.55% |
| G3, V1-V5 + entailment (both readers) + veto (everything stacked) | 30.3% (below the 35% floor) | 7 | 0.35% |

- The pre-registered span-entailment predictions **E1 and E2 both failed**: the check removes 15-19% of correct releases (limit 5%).
- On DEV + FRESH, the V1-V5 + veto system has 0 + 2 errors (0.4% over 500), consistent with S18's 0.45%.
- The errors that survive are of two kinds (provisional reading, not a gold audit):
  - **gold or strict-grading disputes**, 4 of the 9 (race time off by one second, death date off by two days, "shave his head" vs
    "cut his hair", a name without its last part): about **0.2% of all items, a floor that no reader or check can remove** under the
    gold-relative rule;
  - **shared-evidence misreadings** (A2 where every reader agrees, because the evidence states a nearby fact: an announcement date
    for "launch", employment years for "invented", a 2-2 score for "goals scored"): about 0.25%.

## Power on the untouched pool
L2 primary rule as in S18 (false-credit correction f_up = 0.0082, Clopper-Pearson 97.5% upper < 1%): at n = 1526 a pass needs
**at most 6 graded-wrong releases**.

| true rate | 0.20% | 0.25% | 0.30% | 0.35% | 0.40% | 0.45% | 0.50% | 0.60% |
|---|---|---|---|---|---|---|---|---|
| P(pass) | 0.96 | 0.91 | 0.82 | 0.71 | 0.59 | 0.47 | 0.36 | 0.19 |

The pool is all stratum O, where S18's rate was higher than average (all 20 errors were in O). For the best system above,
the S18 stratum-O rate is 9/1800 = 0.50%, and that figure is optimistic because the components were chosen on these errors.
With the Phi-4 AND Mistral veto it is 8/1800 = 0.44%. **Expected P(pass) is therefore about 0.3-0.45, before allowing for post-hoc optimism. Running S19 now would most likely burn the last sealed pool on a fail.**

## Recommendation: do not run S19 yet; first move one of three levers
1. **Gold adjudication (user decision, changes the measurement rule).** About half the remaining errors are gold disputes.
   Pre-register a blind adjudication: for every graded-wrong release, a person who does not see which system produced the answer
   checks the gold against the question and primary sources, using a written rubric (gold wrong / answer wrong / both acceptable).
   Errors judged "gold wrong" or "both acceptable" are excluded. This is one-directional, because only graded-wrong items are examined; hidden errors among
   graded-correct items stay covered by f_up. SimpleQA Verified itself was built this way. If it removes the floor, the true rate is about 0.25%
   and P(pass) is about 0.9. The cost is about 10-20 items for the user to adjudicate after the run.
2. **A stronger second reader of another family** (the veto is the largest single gain: Phi-4 14B halved the errors, Gemma 3 12B
   hardly helped). **Tried at 08:00 with Mistral Small 3.2 24B** (pre-registered M1-M3; results/shared_eval/MISTRAL_VETO.md):
   alone 11 errors (worse than Phi-4's 9); Phi-4 AND Mistral 8 errors (0.40%) at 36.2%, removing only 3.5% of correct releases.
   A bigger reader does not remove the shared misreadings, so this lever looks nearly used up. A reader that saw *different evidence*
   (for example the live page rather than the same passage) would be the next thing to try.
3. **Lower the coverage floor from 35% to 30%** (user decision). The fully stacked system reaches 0.35% at 30.3%; P(pass) is about 0.7
   at that rate, and higher with lever 1.

The L3 theorem itself is unchanged by all of this: every release is still a verbatim, typed, period-consistent span of a
hash-pinned page. The new components (veto, entailment) are learned, so they belong to the L2 (statistical) layer, not to L3.

## Decisions (2026-11-07 ~08:40; the user delegated the specifics: "You decide the specifics.")
1. **One joint sealed run on all 1,526 untouched items** (FRESH-5), shared with the Kimi session's tiered rule. Both systems are
   frozen in one pre-registration before anything runs; one generation pass serves both.
   - FRESH-5 sealed 08:42 by vkg/fresh5.py: original SimpleQA minus Verified minus FRESH-3/4 = 1,526 items, all stratum O,
     shuffled with Random(7000); SHA-256 d9eec22c1b906ae796dc0377be249229ffec4b64245d6fffaba523cb6396effc. Not inspected.
2. **Web evidence from DuckDuckGo, not Serper.** The Serper balance is 5 credits, and the user prefers not to top up. DuckDuckGo
   was the S14/S15 backend: keyless, held to one search per 10 s, contamination guard as before. Because the evidence changes,
   **both systems are re-measured on DEV + FRESH with DuckDuckGo evidence before freezing**: new 4B and Phi-4 answers, new judge
   labels. The Serper-based numbers above do not carry over automatically.
   - Prefetch (raw URLs and pages only, no model, no gold): results/runs/fresh5/prefetch_ddg.py, DEV and FRESH first, then FRESH-5.
     About 5.5 h of network time, no GPU.
3. **L2 system (primary):** L3 gate V1-V5 (V2'/V3'/V5 added to the frozen V1-V4) + all 3 sources agree (G3) + **Phi-4 cautious veto**.
   Phi-4 alone, not Phi-4 AND Mistral: the gain from Mistral was 9 → 8 on S18 (post hoc), and one veto model keeps the system small.
   The 4B and Phi-4 fit on one 32 GB card together. Coverage floor stays at 35%.
4. **L2 endpoint: adjudicated gold (primary), gold-relative (secondary, always reported next to it).**
   - Blind adjudication, fixed before the run: every graded-wrong release of the L2 system is mixed with twice as many decoys
     (graded-wrong answers of the baselines and graded-correct releases), shuffled, and shown without the system name. The
     user judges each against the question and primary sources with a written rubric: gold wrong / answer wrong / both
     acceptable / cannot tell. Only "gold wrong" and "both acceptable" remove an error. "Cannot tell" keeps it as an error.
   - Hidden errors among graded-correct releases stay covered by the grader's false-credit rate (f_up = 0.0082), as in S18.
   - Pass rule as S18: false-credit-corrected Clopper-Pearson 97.5% upper bound < 1% at n = 1526, i.e. at most 6 errors after adjudication.
5. **L1 (the Kimi session's tiered rule), co-primary:** tier 1 = the L2 system above; tier 2 = the 4B cautious and Phi-4 cautious
   combo answers agree; tier 3 = "I don't know". Tested as L1-A against wiki_plain with the S15 criteria (vkg/s17_eval.py).
   L1-B (combo_plain, MSany: equal budget) is reported and expected to fail on coverage and correctness.
6. **Error rate split:** two primary hypotheses (L2, L1-A), each at one-sided 2.5%.
7. **Order of work:** prefetch → DEV + FRESH re-measurement on DuckDuckGo evidence (needs a GPU for the 4B, Phi-4 and the judge,
   about 1 h on a 32 GB card) → final protocol with hashes → S19 run on FRESH-5 (about 2-3 h on a 32 GB card) → blind adjudication.
