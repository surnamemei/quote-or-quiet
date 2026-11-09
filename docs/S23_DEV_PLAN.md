# S23 (Phase 3: independent recovery) DEV plan, written before any generation (2026-11-09)

Question. Can the local-Wikipedia source find the right page without help from web results, so that "support 3" keeps its
independence while coverage rises? Diagnostic (results/runs/s23/indep_dev.md, indep_dev2 output): gold verbatim on retrieved pages
Mintaka DEV 0.58 -> 0.77, PopQA DEV 0.37 -> 0.71, SimpleQA DEV 0.58 -> 0.64 for the independent variant "T3"; web-pinning reference
0.87 / 0.62 / not measured. Ceiling only: it says nothing about releases or errors.

Variant "indep" (results/runs/s23/s23_run.py): wiki evidence = BM25 top-30 re-ranked by title-in-question (top 5) plus title-index
pages for the question's mentions (quoted strings, capitalised runs, boundary-clean n-grams; up to 3 senses of up to 2 mentions;
8 pages at most), contamination-checked. Web evidence and web generations are reused from S19; 4B readers (128 tokens, fence-tolerant
parse) and Phi-4 are regenerated; scoring with the S22 combination rule (S19 releases plus new releases that are not time-sensitive
and not subject-ambiguous, format-relaxed gate), alias-aware labels.

Decision rule (fixed now). Pool the three DEV sets (mintaka_dev, popqa_dev, dev). Let A = releases added by indep beyond the frozen S19
system, w = graded-wrong among them. Continue to the FRESH-5 design run only if A >= 40 and w / A <= 3%. For reference the web-pin
variant added releases at 5.2% (Mintaka, adjudicated) and 6.3% (FRESH-5, graded). If the rule fails, the independent-retrieval line
stops and the result (coverage gained, error rate of the added releases) is reported as such.

What this cannot show: FRESH-5 and the S21 sets are already unsealed, so any later run on them is design data; an L2 claim would need
new sealed questions. DEV samples are small (a few dozen added releases), so this run decides only whether to continue.

Note (2026-11-09, before the run): the first launch failed on a sqlite thread error; the title lookup now uses per-thread connections and also matches titles with a leading "The". The diagnostic numbers above were measured before that second change.
