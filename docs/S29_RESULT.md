# S29 sealed run: result (written as each pre-registered step completes)

Pre-registration: docs/SEALED_SET_DESIGN.md (items 1-9 and the 2026-11-10 clarification). Frozen pipeline S19, free-search-mcp pool, 3,359 sealed questions (the "founded" relation dropped before the run).

## 1. Frozen system, gold-relative (s29_score.py, s29_final.py; fsm_test.md)
- Released 1,765 of 3,359: coverage 0.525. Prediction 0.40 to 0.65: **met**.
- Gold-relative wrong 54 (3.06% of releases). Prediction at most 1.5%: **failed**. Corrected upper bound over all questions before adjudication 2.13%.
- By relation (released / wrong): author 304/7, birth_place 423/22, death_year 184/1, office 9/1, director 349/13, birth_year 455/9, capital 41/1.
- Agreement-score baseline: t = 6 releases 1,633 with 51 wrong; t = 5 releases 1,856 with 60 wrong. At the system's coverage the two rules differ by about 3 gold-relative wrong (exact matched figure in the L1 analysis). Prediction "differ by fewer than 3": decided in the L1 analysis with edge interpolation.

## 2. Secondary test: two-source cell V2 (s29_v2.py, s29_v2_unblind.py; review/wd/V2_result.md)
- V2 (registered wording) adds 144 releases: coverage 0.525 to 0.568, +4.3 points. Prediction 2 to 6 points: **met**.
- Blind review (two reviewers per row, question and answer only, S38 rubric): decoys 15/15 caught by both (valid); 0/15 random frozen releases called wrong.
- Added releases wrong against the facts (both reviewers): V2 3/144 = 2.1%, one-sided 90% upper 4.6%: **pass** (rule: at least 40, at most 3%, upper at most 6%). V2b (secondary, broader cell) 4/156 = 2.6%, upper 5.1%: pass.
- The errors: a pope confused with a namesake (Paul II answered 2005, John Paul II's death year); a reign start year given as a birth year (Nur Devlet); two "head of government in year X" questions answered with a later officeholder (Nicaragua 2006, Kazakhstan 2020, the latter V2b only). Three further Tajikistan head-of-government answers (the president, not the prime minister) were called wrong by one reviewer and right for one reading by the other.
- Second half of the V2 pass rule: V2's truth-relative errors over all questions = 1 (frozen, from the L1 review below) + 3 (added) = 4 at coverage 0.568; corrected one-sided 97.5% upper bound 0.35%, below 1%: **pass**. V2 passes both parts of the secondary test.

## 3. L2 (primary endpoint; s29_l2.py; review/wd/L2_result.md)
- Two blind reviewers with gold shown, the earlier rubric, quote check on every removing verdict (results/runs/s22/quote_check.py: 66/72 and 59/73 quotes found, the rest reverted to "cannot tell"), removal only if both reviewers remove.
- Mechanical fix before the decision: the sheet's verdict and quote columns were named "verdict (gold wrong / ...)" and "verbatim_quote", while quote_check.py and s29_l2.py read "verdict" and "quote"; the first pass therefore saw every row as "cannot tell" (decoys 0/12, nothing removed). The columns were renamed in copies (L2_verdict_{A,B}_norm.csv), content unchanged, and both steps rerun.
- Decoys 12/12 called "answer wrong" by both (valid); gold-matching releases called wrong 0/24.
- k_adj = 18 of 54 gold-relative errors kept (36 removed). Corrected Clopper-Pearson one-sided 97.5% upper bound over 3,359 questions: **0.88%** at coverage 0.525. **L2 met on the sealed set.**
- Of the 18 kept, 1 was called "answer wrong" by both (Dominican Republic head of government 2011: Danilo Medina took office in 2012); the other 17 are kept because at least one reviewer could not tell or the quote failed, so k_adj is conservative.

## 4. L1 (s29_l1.py; review/wd/L1_result.md)
- Blind review with gold hidden (S36 rubric), 308 rows; decoys 15/15 caught by both.
- Truth-relative errors among the 1,765 frozen releases: **1**.
- L1-a (system SER lower than B0 raw closed book 76.9%, B1 closed book with abstention prompt 51.5%, B2 standard RAG 6.9%, B3 RAG with abstention prompt 5.4%; system 1.61%, gold-relative, McNemar one-sided, Holm): all four pass, p from 1e-32 down; robustness check with truth-relative rates passes for all four. **L1-a met.**
- L1-b (non-inferiority to the agreement-score ablation at exactly matched coverage, truth-relative, bootstrap 10,000): SER difference -0.005 points (upper +0.060, margin +0.25); yield difference +0.005 points (lower -0.655, margin -1). **L1-b met.** Revised L1 met.
- Original L1 (50% fewer errors than the ablation): k_sys 1 against an expected 1.18, NOT MET, as predicted (item 6). At this error level both rules are close to zero truth-relative errors and no test can separate them.
- Item 9 (L1 at V2's coverage; s29_v2l1.py, review/wd/V2_L1_result.md): the ablation at V2's coverage needs threshold 4, so the 24 gold-wrong ablation answers at score exactly 4 not judged before were reviewed with the same rubric (E4_sheet.csv; decoys 10/10 caught by both). V2 1,909 releases (coverage 0.568), ablation t = 4 with edge share 0.057; no gold-wrong answer of either rule left without a verdict. Truth-relative errors: V2 4, ablation 2.85 (expected). Original L1: NOT MET (prediction: not met). L1-b: SER difference +0.034 points (upper +0.149, margin +0.25), yield difference -0.034 (lower -0.982, margin -1): **met**, with the yield bound close to its margin.
