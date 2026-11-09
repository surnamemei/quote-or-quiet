# Conditional-truth judge on DEV (results/runs/l3/cj_eval.py)

| kind | label | SUPPORTED | NOT_SUPPORTED | UNCLEAR |
|---|---|---|---|---|
| system | true | 59 | 1 | 4 |
| system | false | 3 | 1 | 5 |
| neg_easy | false | 0 | 50 | 10 |
| neg_hard | true | 0 | 1 | 0 |
| neg_hard | false | 1 | 49 | 9 |

neg_easy: false credit 0/60 (95% upper 0.049)

neg_hard: false credit 1/59 (95% upper 0.078)

Disagreements:

- [system] When did Isaac Newton publish his Comprehensive Theory of Gr | E=Isaac Newton | A=1687 | label true | judge UNCLEAR
- [system] Who played Mrs. Robinson in The Graduate? | E=The Graduate (novel) | A=Anne Bancroft | label false | judge SUPPORTED
- [system] Who was the only player to ever pinch hit for Ted Williams? | E=Ted Williams | A=Carroll Hardy | label true | judge UNCLEAR
- [system] How many NBA MVP Awards did Michael Jordan achieve? | E=Michael Jordan | A=5 | label true | judge UNCLEAR
- [neg_hard] What is Jean Gabriel Marie's occupation? | E=Jean Gabriel-Marie | A=French | label false | judge SUPPORTED
- [system] What is the name of the main character in The Scarlet Letter | E=Scarlet (color) | A=Hester Prynne | label false | judge SUPPORTED
- [system] Who was the first emperor of the Roman Empire? | E=Roman Empire | A=Augustus | label true | judge NOT_SUPPORTED
- [system] What was American author Mark Twain's real name? | E=Mark Twain (book) | A=Samuel Langhorne Clemens | label false | judge SUPPORTED
- [system] Which main character dies at the end of the movie the Avenge | E=Avengers: Endgame | A=Tony Stark | label true | judge UNCLEAR
- [neg_hard] What dynasty was Cleopatra apart of? | E=Cleopatra | A=Macedonian Greek | label true | judge NOT_SUPPORTED