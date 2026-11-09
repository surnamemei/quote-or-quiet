# Generality, step 1: decomposing silent error across benchmarks (2026-11-09; post hoc on unsealed sets, descriptive)

Data: frozen S19 system, per released answer. FRESH-5 (568 releases), Mintaka test (620), PopQA test (401). Error classes: Mintaka from
the strict blind adjudication (all 28 errors inside it); FRESH-5 and PopQA from the authors' reading against pinned pages (not blind).

| class (share of released answers) | FRESH-5 | Mintaka | PopQA | pooled (n = 1,589) | 95% CP interval |
|---|---|---|---|---|---|
| gold wrong, stale, or equally acceptable answer | 0.35% (2) | 3.06% (19) | 1.50% (6) | 1.70% (27) | 1.12 to 2.46 |
| ambiguous question or entity | 0 | 0.32% (2) | 2.24% (9) | 0.69% (11) | 0.35 to 1.24 |
| answer judged wrong | 0.35% (2) | 0.48% (3) | 0.50% (2) | **0.44% (7)** | 0.18 to 0.91 |
| adjudicators could not settle | 0 | 0.65% (4) | 0 | 0.25% (4) | 0.07 to 0.64 |
| all graded errors | 0.70% (4) | 4.52% (28) | 4.24% (17) | 2.77% (44) | |

## Reading
1. The part attributable to the system (answers judged wrong) is stable: 0.35%, 0.48%, 0.50% of released answers on three benchmarks that
   differ in wording, gold source and error mix; pooled 0.44% (0.18 to 0.91%). This is the closest thing to a transferable number we have.
   Caveat: classes on two of the three sets are unblinded readings.
2. Everything else is a property of the benchmark, and it differs by an order of magnitude: gold wrong or stale 0.35% to 3.06%,
   ambiguous 0 to 2.24%. Gold-relative SER therefore measures the benchmark about as much as the system.
3. Question-only features (results/runs/qfeatures.md, all questions of each set, no system output): the time-sensitivity rule flags 0.3%
   of FRESH-5, 9.0% of Mintaka and 0.1% of PopQA, which tracks the time mechanism of the gold class (Mintaka 3.06%) but not the PopQA
   gold class (multi-valued relations such as occupation: 1.50%). The share of questions whose first indexed mention has two or more
   Wikipedia senses is 62% to 76% on every set, so that feature as defined does not discriminate and cannot predict the ambiguity
   class (0 to 2.24%). A predictive rule for the benchmark-specific classes needs better features (relation multiplicity, namesake
   popularity at the released page), and three benchmarks are too few to fit one.

## Predictions fixed before the next sealed set is run
- P1. On a new sealed set with checked gold, answers judged wrong will make up at most 0.91% of released answers (upper end of the pooled
  interval above) at the frozen system's coverage (about 0.37 for SimpleQA-style questions).
- P2. The gold-wrong and ambiguous classes will be larger on a set with more time-sensitive or multi-valued questions; no number is
  predicted, the classes are reported separately.
- P3. A pilot of about 150 items per benchmark, adjudicated with the blind protocol, estimates the benchmark-specific classes well enough
  to predict gold-relative SER of the full set within a factor of two. This is the operational form of the certification protocol and is
  tested when the next sealed set arrives.
