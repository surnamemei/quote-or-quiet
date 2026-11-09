# Paper outline (v0.2, 2026-11-09)
Full text: paper/manuscript.md. Numbers trace to results/runs/s19/S19_RESULT.md, results/runs/s21/S21_RESULT.md,
docs/S22_DEV_FINDINGS.md, docs/L3_CERTIFICATES.md, results/runs/s22/mintaka_test_adj_result_strict.md.

North Star: a deductive span gate behind cross-source agreement and a veto gives a certified 1% silent-error bound on SimpleQA at 37%
coverage; elsewhere precision is limited by benchmark gold and ambiguity, and coverage by retrieval and source independence.

Claim architecture
1. L2 on sealed SimpleQA (FRESH-5): coverage 0.372, k = 4, upper 0.76%. Fully supported (pre-registered, one run).
2. Transfer misses the coverage floor: Mintaka 0.310 (k 28), PopQA 0.191 (k 17). Fully supported (pre-registered).
3. On Mintaka the frozen system's graded errors are mostly gold problems: strict blind adjudication removes 19 of 28; k_adj = 9, upper 0.92%.
   Supported, post hoc, LLM adjudicators validated by decoys (62/62, 61/63); sensitive to the rubric.
4. Raising coverage costs precision: pin + format gate add releases at 5.2% (Mintaka, adjudicated) and 6.3% (FRESH-5) error; FRESH-5 would
   fail L2 (14 vs <= 6). Supported, post hoc, design data.
5. At equal coverage the gate is no better than agreement on Mintaka and PopQA; FRESH-5 4 vs 9 (not significant). Post hoc.
6. Derivation certificates are sound and add about one correct release in 224 candidates. Negative result.
Boundaries: one reader family, one snapshot, English; PopQA errors read not adjudicated; FRESH-5 spent as design data.
Not in the paper: Goal B / Qualified state results (DEV only, L3 fork), S22 sealed Mintaka items (never run).
