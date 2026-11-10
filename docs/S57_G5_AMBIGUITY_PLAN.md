# S57: gate G5, one answer per reading on new ambiguous names (plan, 2026-11-11, before any G5 run output)

Gate G5: false answer or misleading quote per reading; threshold 97.5% upper bound at most 3% for each; at least 250 readings with a witness; registered, unseen data, valid decoys.
Items: results/runs/s57/g5/e9_build.py, a copy of the S46 builder with seed 5703, 75 film names and 75 person names, the 120 E9 bases excluded: 150 names, 362 readings (built, CPU; no answers seen).
Pipeline unchanged from S46 part B (results/runs/s46/e9_run.py, copied with seed 5704): the 4B reader answers from each reading's page (plain and cautious prompts must agree), the answer is a typed verbatim span passing the gate, rule W1 chooses the witness. No change of any rule.
Review: every reading with a witness plus 30 decoys (another reading's answer; was 20 in S46), two blind reviewers; each row asks both whether the quote states the answer (states / incomplete / not) and whether the answer is true for that reading (look up allowed for the truth verdict), as in S46.
Predictions: witnesses for 80 to 95% of the readings (S46: 89.3%), so at least 290; false for both reviewers at most 1% and misleading for both at most 1% (upper bounds below 3%); decoys at least 27 of 30.
A failure is reported as failed; no rule changes on these data.
