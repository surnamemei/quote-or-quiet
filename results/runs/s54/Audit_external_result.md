# Audit sheet: external reviewer against the two language-model reviewers
Verdict counts: {'not': 83, 'incomplete': 57, 'states': 40}
reviewer 1: n=180, agreement 0.844, Cohen kappa 0.758
reviewer 2: n=180, agreement 0.878, Cohen kappa 0.810
Rows where the two LM reviewers agree: n=150, agreement 0.933, kappa 0.889

By key kind (rows; external verdicts states/incomplete/not):
- not: 40 rows; states 0, incomplete 3, not 37
- states: 40 rows; states 38, incomplete 2, not 0
- incomplete: 30 rows; states 1, incomplete 25, not 4
- split: 30 rows; states 1, incomplete 27, not 2
- decoy: 40 rows; states 0, incomplete 0, not 40

Rows where both LM reviewers said 'not' (incl. decoys): 80; external also 'not': 77 (96.2%).
Rows where both said 'states': 40; external 'states' 38, 'not' 0.
Decoys (answer of another row): 40; external 'not' 40.
Binary (not vs not-not) reviewer 1: agreement 0.944, kappa 0.888
Binary (not vs not-not) reviewer 2: agreement 0.939, kappa 0.877

Rows where the LMs agree and the external reviewer differs: 10
