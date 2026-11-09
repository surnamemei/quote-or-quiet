# S23 DEV scoring (design data)

| set | variant | n | released (cov) | wrong | added vs frozen S19 | wrong among added | added from variant |
|---|---|---|---|---|---|---|---|
| mintaka_dev | indep | 200 | 96 (0.480) | 4 | 25 | 2 | 16 |
| mintaka_dev | pin | 200 | 108 (0.540) | 6 | 37 | 4 | 28 |
| popqa_dev | indep | 300 | 79 (0.263) | 8 | 20 | 1 | 15 |
| popqa_dev | pin | 300 | 89 (0.297) | 16 | 30 | 9 | 25 |
| dev | indep | 300 | 165 (0.550) | 3 | 27 | 2 | 17 |

Pooled over the three DEV sets (added beyond the frozen S19 system):
- indep: A = 72, w = 5, w / A = 0.069
- pin: A = 67, w = 13, w / A = 0.194
Decision rule (A >= 40 and w / A <= 3%) for indep: STOP the independent-retrieval line

Wrong among added releases:
- mintaka_dev indep: What year did the first Mario game come out? | gold ['1983'] | answer 1981 | from var
- mintaka_dev indep: When did Ark: Survival Evolved first come out? | gold ['2017-08-27', '27-Aug-17'] | answer June 2, 2015 | from var
- mintaka_dev pin: Who won the Super Bowl MVP in 2007? | gold ['Peyton Manning'] | answer Eli Manning | from var
- mintaka_dev pin: Who is the youngest quarterback to ever win the Super Bowl? | gold ['Patrick Mahomes'] | answer Ben Roethlisberger | from var
- mintaka_dev pin: What is the armed conflict within a nation called? | gold ['civil war'] | answer Non-international armed conflict | from var
- mintaka_dev pin: What album won Album of the Year in 2014? | gold ['Morning Phase'] | answer Random Access Memories | from var
- popqa_dev indep: Who was the screenwriter for Face? | gold ['Ronan Bennett'] | answer Michael Colleary | from s19
- popqa_dev pin: Who was the screenwriter for Face? | gold ['Ronan Bennett'] | answer Michael Colleary | from s19
- popqa_dev pin: In what country is Lim? | gold ['Montenegro', 'me'] | answer Peru | from var
- popqa_dev pin: What genre is Egg? | gold ['progressive rock', 'prog-rock'] | answer Egg punk | from var
- popqa_dev pin: Who was the composer of Grandpa? | gold ["Jamie O'Hara"] | answer Howard Blake | from var
- popqa_dev pin: Who was the director of The Blues? | gold ['Martin Scorsese', 'Martin Skorseze'] | answer John Landis | from var
- popqa_dev pin: Who was the screenwriter for Baby? | gold ['Daniel Mulloy'] | answer Sai Rajesh Neelam | from var
- popqa_dev pin: Who was the director of My Wife? | gold ['Tinto Brass', 'Mauro Bolognini'] | answer Fatin Abdel Wahab | from var
- popqa_dev pin: Who was the producer of Police Squad!? | gold ['Jim Abrahams', 'James S. Abrahams'] | answer Robert K. Weiss | from var
- popqa_dev pin: Who was the screenwriter for The Kid? | gold ['Charlie Chaplin', 'Charles Spencer Chaplin'] | answer Audrey Wells | from var
- dev indep: What is the area between the River Indus and the River Jhelum called? | gold ['Sindh Sagar Doab'] | answer Doab | from s19
- dev indep: What day, month, and year did Carrie Underwood reveal the track listing for her album "Storyteller"? | gold ['September 10, 2015'] | answer September 9, 2015 | from var
