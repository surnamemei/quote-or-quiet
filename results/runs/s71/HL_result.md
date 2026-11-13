# S71: the project's reviewers and judge against human labels (VitaminC test, 600 rows, 200 per label)

| reviewer | n | agreement | kappa | false accepts (says it states the claim; humans: not supports) | false rejects |
|---|---|---|---|---|---|
| Claude reviewer A | 600 | 0.905 | 0.783 | 23 of 400 (5.8%; REFUTES 5, NEI 18) | 34 of 200 (17.0%) |
| Claude reviewer B | 600 | 0.912 | 0.799 | 23 of 400 (5.8%; REFUTES 7, NEI 16) | 30 of 200 (15.0%) |
| Claude pair, both 'states' | 600 | 0.908 | 0.790 | 21 of 400 (5.2%; REFUTES 5, NEI 16) | 34 of 200 (17.0%) |
| 27B judge (YES) | 600 | 0.822 | 0.552 | 12 of 400 (3.0%; REFUTES 4, NEI 8) | 95 of 200 (47.5%) |
