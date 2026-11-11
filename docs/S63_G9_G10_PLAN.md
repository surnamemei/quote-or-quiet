# S63: gates G9 and G10, second test: rule A3 on 200 new contested topics (plan, 2026-11-11, before any S63 run output)

Why. S62 (rule A2) failed G9: 25 of 300 kept statements misleading, 22 of them a view credited to a party the sentence does not name; G10 met its bound (3 of 300, upper 2.9%) but its decoys were 26 of 30. On the S62 data (now design data) an attribution question for the 27B kept 159 of the 300 reviewed statements with 0 misleading (upper 2.3%) and 0 other party or opposite, and dropped all 25 misleading ones.
Rule A3 (frozen now; results/runs/s63/s63_a3.py): A2 unchanged, plus YES required to: 'The statement says that a particular party holds a view. Does the sentence itself say that this same party holds, states or argues this view? Answer NO if the sentence states the view as a plain fact without saying who holds it, if it names a different person or body, or if it only covers part of the view.'
Topics: 200 new contested pages (same title filter; S56 and S62 topics excluded; seed 6301). Statements as before.
Review: as S62 (300 random kept statements or all if fewer; up to 100 best-overlap sentences where different; 30 decoys; two blind sentence-only reviewers; verdicts states / other party / opposite / not). Change to decoys: only on witness sentences that contain all content words of the original party (and none of the replacement's), so that the sentence visibly names the original party.
Predictions: A3 keeps 15 to 30% of statements; at least 250 kept; misleading for both at most 1.5% and other party or opposite at most 1% among reviewed kept (upper bounds at most 3%); decoys at least 27 of 30 for both measures.

Note (14:4x): the first run stopped after statement generation (1,576 statements, candidates built) because of a syntax error in the attribution prompt string of s63_a3.py (a line break where 
 was meant); the string was repaired with no change of wording and the run resumed from the parties step.
