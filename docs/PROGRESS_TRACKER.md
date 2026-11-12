# Progress tracker (2026-11-11)

```
Overall [#################################.......] 40/48 (83%)
```

Each gate has three standard criteria. T: the 97.5% one-sided Clopper-Pearson upper bound of the gate's error share is at or below the threshold. N: the evaluated sample has at least the minimum size. V: the test was registered with predictions before it ran, on data not used in the design, with decoy checks valid (at least 27 of 30 decoys caught). A criterion counts only when met in full. Progress = criteria met / all criteria. The bar is full at 48 of 48.


## Done or mostly done: [####################] 9/9 (100%)

| Gate | Area | T (threshold) | N (minimum sample) | T N V | Now | Evidence |
|---|---|---|---|---|---|---|
| G1 | Short facts, templated questions: released answer wrong | upper bound <1% at coverage >=35% | >=3000 sealed questions | YYY | S40: 10 adjudicated errors, upper bound 0.65% at 55.1% coverage; S29 0.88% at 52.5%; S19 0.76% at 37.2% | docs/S40_RESULT.md |
| G2 | Short facts, templated questions: shown quote does not state the answer | upper bound <=3% | >=250 reviewed releases | YYY | S40: W1 2 of 267 (0.7%, upper 2.7%); R27 0.7% | docs/S40_QUOTE_ANALYSIS_RESULT.md |
| G7 | Long-form biographies: kept claim false or quote not stating it | upper bound <=3% for both | >=300 reviewed claims | YYY | fresh 50 subjects: 1 of 400 false, 1 of 400 misleading (upper 1.4% each), decoys 30 of 30 | results/runs/s47/F5_result.md |

## Stage 1: close the measurement gaps (natural questions, ambiguity, chains): [##################..] 11/12 (92%)

| Gate | Area | T (threshold) | N (minimum sample) | T N V | Now | Evidence |
|---|---|---|---|---|---|---|
| G3 | Natural questions: shown quote does not state the answer | upper bound <=3% | >=250 reviewed releases | YYY | S57: R27 on 705 unseen Mintaka releases: 2 of 367 witnesses misleading (0.5%, upper 2.0%), decoys 30 of 30; 52.1% of releases kept | docs/S57_G3_NATURAL_QUESTIONS_PLAN.md |
| G4 | Natural questions: released answer wrong at usable coverage | upper bound <1% at coverage >=35% | >=1000 sealed questions | -YY | S68 (second test, rule Q2, 1,500 sealed NQ-open questions): 5 adjudicated errors (0.33%, upper 0.78%, below 1%) but coverage 17.1%, below 35%, so T fails. S58 (first test, Mintaka): coverage 35.2% but 7 errors (upper 1.20%). The loss on NQ-open is the typed-span step (free-phrase answers) | docs/S68_G4B_PLAN.md |
| G5 | Ambiguous names: false answer or misleading quote per reading | upper bound <=3% | >=250 readings | YYY | S57: 150 new ambiguous names, 315 readings with a witness: 0 misleading (upper 1.2%), 2 of 309 wrong by look-up (upper 2.3%), decoys 30 of 30 and 20 of 20 | docs/S57_G5_AMBIGUITY_PLAN.md |
| G6 | Two-hop questions: quote chain misleading or answer wrong | upper bound <=3% | >=150 reviewed chains | YYY | S57: C2' on 1,400 fresh persons: 0 of 209 accepted chains misleading or wrong (upper 1.7%), decoys 58 of 60; birth place to country only | docs/S57_G6_CHAINS_PLAN.md |

## Stage 2: new kinds of text and attribution: [####################] 12/12 (100%)

| Gate | Area | T (threshold) | N (minimum sample) | T N V | Now | Evidence |
|---|---|---|---|---|---|---|
| G8 | Long-form, other kinds of text (organisations, events, science topics) | upper bound <=3% for both | >=300 reviewed claims | YYY | S60 (second test, W4 with the 27B judge, 50 fresh topic pages): 5 of 400 kept claims false (upper 2.9%), 0 misleading (upper 0.9%), decoys 30 of 30; the first test with the 4B judge (S59) failed on truth | docs/S60_G8B_PLAN.md |
| G9 | Contested topics: shown sentence does not report the view for the stated party | upper bound <=3% | >=250 reviewed kept statements | YYY | S63 (rule A3, 200 new topics): 2 of 300 kept statements misleading (upper 2.4%); A2 had failed on S62 (8.3%) with views credited to parties the sentence does not name | docs/S63_G9_G10_PLAN.md |
| G10 | Contested topics: view moved to another party or reversed | upper bound <=3% by an independent check with valid decoys | >=250 checked statements | YYY | S63: 2 of 300 credited to another party or reversed (upper 2.4%); decoys with specific named parties 30 of 30 (a first decoy set with generic parties was invalid) | docs/S63_G9_G10_PLAN.md |
| G11 | Pages that are not Wikipedia: shown quote does not state the answer | upper bound <=3% | >=250 reviewed releases | YYY | S61: R27 on non-Wikipedia pages of 705 Mintaka releases: 1 of 523 witnesses misleading (upper 1.1%), decoys 30 of 30; rule R with the 4B judge had 3.8% (S49) | docs/S61_G11_WEB_PLAN.md |

## Stage 3: independent validity: [##########..........] 3/6 (50%)

| Gate | Area | T (threshold) | N (minimum sample) | T N V | Now | Evidence |
|---|---|---|---|---|---|---|
| G12 | Reviewers: people agree with the reviewers (the checks above are by language models) | kappa >=0.8 and >=90% of 'not' rows also 'not' by people | >=180 rows, 2 people | --- | open; a third language-model reviewer gave kappa 0.76 to 0.81 and 96.2% on 'not' rows, which does not count | results/runs/s54/Audit_external_result.md |
| G13 | Baselines: the quote rule beats the standard checkers on held-out rows | lower misleading share than every baseline at equal acceptance | >=900 held-out rows | YYY | S64: at equal acceptance the 27B judge lets through fewer not-stating quotes than MiniCheck and HHEM (held-out 1.1% vs 3.1%/4.3%; Mintaka 1.9% vs 7.4%/9.9%; registered confirmatory set 0.4% vs 3.0%/2.1%); AlignScore not run (pickle) | docs/S64_G13_BASELINES_PLAN.md |

## Stage 4: apply to existing models: [###########.........] 5/9 (56%)

| Gate | Area | T (threshold) | N (minimum sample) | T N V | Now | Evidence |
|---|---|---|---|---|---|---|
| G14 | Applied to other models: drafts of 3 or more different models | upper bound <=3% quote and <1% answer for each model | >=250 releases per model, sealed | YYY | S65: the quote check after Llama 3.1 8B, Gemma 3 12B, Mistral Nemo 12B on 2,001 sealed PopQA questions: drafts 52 to 68% wrong; released 305 to 330 answers each with 0 errors after a look-up truth check (bound 0.18%) and 0.3 to 1.0% misleading quotes (upper bounds 1.8 to 2.9%) | docs/S65_G14_OTHER_MODELS_PLAN.md |
| G15 | Tool stress test | 0 releases without a machine-checked quote in the run | >=1000 mixed queries | -YY | S66: 1,000 requests, every quote verbatim in a hash-matched page (1,513 statements), but 208 /bio claims show a value not verbatim in their quote (draft wording vs page wording), so the registered check fails; fix in tool v2, then a second test | docs/S66_G15_STRESS_PLAN.md |
| G16 | Replication by someone else | headline numbers reproduced within the intervals | >=1 independent run of the release | --- | not done |  |
