# Progress tracker (2026-11-11)

```
Overall [##################......................] 22/48 (46%)
```

Each gate has three standard criteria. T: the 97.5% one-sided Clopper-Pearson upper bound of the gate's error share is at or below the threshold. N: the evaluated sample has at least the minimum size. V: the test was registered with predictions before it ran, on data not used in the design, with decoy checks valid (at least 27 of 30 decoys caught). A criterion counts only when met in full. Progress = criteria met / all criteria. The bar is full at 48 of 48.


## Done or mostly done: [####################] 9/9 (100%)

| Gate | Area | T (threshold) | N (minimum sample) | T N V | Now | Evidence |
|---|---|---|---|---|---|---|
| G1 | Short facts, templated questions: released answer wrong | upper bound <1% at coverage >=35% | >=3000 sealed questions | YYY | S40: 10 adjudicated errors, upper bound 0.65% at 55.1% coverage; S29 0.88% at 52.5%; S19 0.76% at 37.2% | docs/S40_RESULT.md |
| G2 | Short facts, templated questions: shown quote does not state the answer | upper bound <=3% | >=250 reviewed releases | YYY | S40: W1 2 of 267 (0.7%, upper 2.7%); R27 0.7% | docs/S40_QUOTE_ANALYSIS_RESULT.md |
| G7 | Long-form biographies: kept claim false or quote not stating it | upper bound <=3% for both | >=300 reviewed claims | YYY | fresh 50 subjects: 1 of 400 false, 1 of 400 misleading (upper 1.4% each), decoys 30 of 30 | results/runs/s47/F5_result.md |

## Stage 1: close the measurement gaps (natural questions, ambiguity, chains): [###############.....] 9/12 (75%)

| Gate | Area | T (threshold) | N (minimum sample) | T N V | Now | Evidence |
|---|---|---|---|---|---|---|
| G3 | Natural questions: shown quote does not state the answer | upper bound <=3% | >=250 reviewed releases | YYY | S57: R27 on 705 unseen Mintaka releases: 2 of 367 witnesses misleading (0.5%, upper 2.0%), decoys 30 of 30; 52.1% of releases kept | docs/S57_G3_NATURAL_QUESTIONS_PLAN.md |
| G4 | Natural questions: released answer wrong at usable coverage | upper bound <1% at coverage >=35% | >=1000 sealed questions | --- | Mintaka and PopQA missed the 35% coverage floor (Section 5.9) | paper/manuscript.md 5.9 |
| G5 | Ambiguous names: false answer or misleading quote per reading | upper bound <=3% | >=250 readings | YYY | S57: 150 new ambiguous names, 315 readings with a witness: 0 misleading (upper 1.2%), 2 of 309 wrong by look-up (upper 2.3%), decoys 30 of 30 and 20 of 20 | docs/S57_G5_AMBIGUITY_PLAN.md |
| G6 | Two-hop questions: quote chain misleading or answer wrong | upper bound <=3% | >=150 reviewed chains | YYY | S57: C2' on 1,400 fresh persons: 0 of 209 accepted chains misleading or wrong (upper 1.7%), decoys 58 of 60; birth place to country only | docs/S57_G6_CHAINS_PLAN.md |

## Stage 2: new kinds of text and attribution: [###.................] 2/12 (17%)

| Gate | Area | T (threshold) | N (minimum sample) | T N V | Now | Evidence |
|---|---|---|---|---|---|---|
| G8 | Long-form, other kinds of text (organisations, events, science topics) | upper bound <=3% for both | >=300 reviewed claims | --- | not run |  |
| G9 | Contested topics: shown sentence does not report the view for the stated party | upper bound <=3% | >=250 reviewed kept statements | Y-- | 0 of 135 kept (upper 2.7%); decoys 16 of 30, invalid | results/runs/s56/E12_result.md |
| G10 | Contested topics: view moved to another party or reversed | upper bound <=3% by an independent check with valid decoys | >=250 checked statements | --- | judge accepts a moved party for 4.4% of usable cases (upper 9.4%); 81% of kept statements had no flip control before rule A2 | results/runs/s56/E12c_result.md |
| G11 | Pages that are not Wikipedia: shown quote does not state the answer | upper bound <=3% | >=250 reviewed releases | --Y | rule R: 8 of 213 (3.8%, upper 7.3%) | results/runs/s49/C_result.md |

## Stage 3: independent validity: [#######.............] 2/6 (33%)

| Gate | Area | T (threshold) | N (minimum sample) | T N V | Now | Evidence |
|---|---|---|---|---|---|---|
| G12 | Reviewers: people agree with the reviewers (the checks above are by language models) | kappa >=0.8 and >=90% of 'not' rows also 'not' by people | >=180 rows, 2 people | --- | open; a third language-model reviewer gave kappa 0.76 to 0.81 and 96.2% on 'not' rows, which does not count | results/runs/s54/Audit_external_result.md |
| G13 | Baselines: the quote rule beats the standard checkers on held-out rows | lower misleading share than every baseline at equal acceptance | >=900 held-out rows | YY- | better than MiniCheck-Flan-T5-Large; HHEM and AlignScore not run | results/runs/s54/MiniCheck_result.md |

## Stage 4: apply to existing models: [....................] 0/9 (0%)

| Gate | Area | T (threshold) | N (minimum sample) | T N V | Now | Evidence |
|---|---|---|---|---|---|---|
| G14 | Applied to other models: drafts of 3 or more different models | upper bound <=3% quote and <1% answer for each model | >=250 releases per model, sealed | --- | only Phi-4 and Qwen drafts tested | tool/README.md |
| G15 | Tool stress test | 0 releases without a machine-checked quote in the run | >=1000 mixed queries | --- | selftest only | tool/selftest.sh |
| G16 | Replication by someone else | headline numbers reproduced within the intervals | >=1 independent run of the release | --- | not done |  |
