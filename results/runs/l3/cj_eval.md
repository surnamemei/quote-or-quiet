# Conditional-truth judge on DEV (results/runs/l3/cj_eval.py)

| kind | label | SUPPORTED | NOT_SUPPORTED | UNCLEAR |
|---|---|---|---|---|
| system | true | 42 | 1 | 5 |
| system | false | 4 | 6 | 0 |
| system | unclear | 1 | 0 | 0 |
| neg_easy | false | 0 | 57 | 2 |
| neg_hard | true | 1 | 0 | 0 |
| neg_hard | false | 1 | 50 | 6 |

neg_easy: false credit 0/59 (95% upper 0.050)

neg_hard: false credit 1/57 (95% upper 0.081)

Disagreements:

- [system] What is Jordan the capital of? | E=Jordan | A=Amman | label false | judge SUPPORTED
- [system] Who was the screenwriter for Final Destination? | E=Final Destination (film) | A=Jeffrey Reddick | label true | judge NOT_SUPPORTED
- [system] Who wrote the Percy Jackson series? | E=Percy Jackson (film series) | A=Rick Riordan | label false | judge SUPPORTED
- [system] Who is Harry Potter's godfather? | E=Harry Potter | A=Sirius Black | label true | judge UNCLEAR
- [system] What author wrote The Scarlet Letter? | E=The Scarlet Letter (miniseries | A=Nathaniel Hawthorne | label false | judge SUPPORTED
- [system] Which one of Ron Howard's children has directed episodes of  | E=Ron Howard | A=Bryce Dallas Howard | label true | judge UNCLEAR
- [neg_hard] Who wrote the Pride and Prejudice? | E=Pride and Prejudice (musical) | A=Taylor | label false | judge SUPPORTED
- [system] What was the first novel James Bond appeared in? | E=James Bond | A=Casino Royale | label true | judge UNCLEAR
- [system] How many years was the attraction Horizons at EPCOT sponsore | E=Epcot | A=10 | label true | judge UNCLEAR
- [system] Where was the first "All-India Ijtema of Jamaat-e-Islami" he | E=Jamaat-e-Islami Kashmir | A=Pathankot | label false | judge SUPPORTED
- [system] How many Indigenous languages were designated in Togo in 197 | E=Togo | A=2 | label true | judge UNCLEAR