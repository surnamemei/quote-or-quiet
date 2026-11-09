# S38: re-evaluate the rejected coverage variants against the facts (plan, 2026-11-09, before any review)

Why: S22, S23, S30 and S31 rejected ways of raising coverage because the added releases were 5-9% wrong against the gold. S35 then showed that the frozen system's own releases are about 4-5% wrong against the gold on Mintaka and PopQA and 0 of 180 wrong against the facts. The 3% bar was applied to a measure that is mostly benchmark noise on these sets, so the rejections may have been wrong.
Variants (design data only, cached outputs; the same releases that were scored before):
- indep: S23 independent title-index retrieval + format gate + time and subject rules (72 added on Mintaka DEV, PopQA DEV, SimpleQA DEV);
- pin: S22 web-pinned Wikipedia pages + format gate + the same rules (67 added);
- webgate: S30 W(2), spans from two web domains (24 added);
- cell: S31 best two-source cell, explore and held-out halves (about 55 added).
Review: every added release of every variant (shared answers once), question and answer only, two blind model reviewers (S35 rubric: correct / correct for one reading / wrong / cannot tell), 20 injected-false decoys (valid if at least 18 are called wrong by both). A truth-relative error needs both reviewers to say wrong.
Pass rule per variant, fixed now: at least 40 added releases and a truth-relative error rate among them of at most 3% (point estimate), and the one-sided 90% upper bound at most 6%. A passing variant becomes a candidate for version 2, to be frozen and tested on a new sealed set (with the L1 comparison at the higher coverage). FRESH-5 numbers from S22 (8 real errors in 126 pinned releases) are kept in mind: they are test data and are not re-used.
