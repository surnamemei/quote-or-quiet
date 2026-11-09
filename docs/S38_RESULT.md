# S38: rejected coverage variants judged against the facts

Decoys called wrong by both: 20/20 (VALID)

| variant | added | gold-wrong | truth-wrong (both) | rate | one-sided 90% upper | wrong by either | right for one reading | pass (>= 40, <= 3%, upper <= 6%) |
|---|---|---|---|---|---|---|---|---|
| indep | 72 | 5 | 2 | 2.8% | 7.2% | 2 | 1 | fail |
| pin | 67 | 13 | 5 | 7.5% | 13.4% | 5 | 7 | fail |
| webgate | 24 | 2 | 0 | 0.0% | 9.1% | 0 | 1 | fail |
| cell | 55 | 4 | 0 | 0.0% | 4.1% | 0 | 4 | PASS |

Truth-relative errors (both reviewers):

- [pin/popqa_dev] In what country is Lim? | ans Peru | gold ['Montenegro', 'me']
- [pin/popqa_dev] Who was the director of My Wife? | ans Fatin Abdel Wahab | gold ['Tinto Brass', 'Mauro Bolognini']
- [indep/dev] What is the area between the River Indus and the River Jhelum called? | ans Doab | gold ['Sindh Sagar Doab']
- [pin/popqa_dev] What genre is Egg? | ans Egg punk | gold ['progressive rock', 'prog-rock']
- [pin/popqa_dev] Who was the director of The Blues? | ans John Landis | gold ['Martin Scorsese', 'Martin Skorseze']
- [indep,pin/popqa_dev] Who was the screenwriter for Face? | ans Michael Colleary | gold ['Ronan Bennett']

Gold-wrong but judged correct by both:

- [webgate] Who was the composer of Dude? | ans Sai Abhyankkar | gold ['Galt MacDermot', 'Arthur Terence Galt MacDermot'] | ['correct for one reading', 'correct for one reading']
- [pin] Who was the screenwriter for Baby? | ans Sai Rajesh Neelam | gold ['Daniel Mulloy'] | ['correct for one reading', 'correct for one reading']
- [pin] What album won Album of the Year in 2014? | ans Random Access Memories | gold ['Morning Phase'] | ['correct for one reading', 'correct']
- [indep] What year did the first Mario game come out? | ans 1981 | gold ['1983'] | ['correct for one reading', 'correct for one reading']
- [cell] Who was the screenwriter for Heat? | ans Michael Mann | gold ['William Goldman', 'S. Morgenstern'] | ['correct for one reading', 'correct for one reading']
- [pin] Who won the Super Bowl MVP in 2007? | ans Eli Manning | gold ['Peyton Manning'] | ['correct for one reading', 'correct for one reading']
- [cell] How many livres did artist Jean-Antoine Watteau sell his painting "Camp-fire" first to Sirois for? | ans 200 | gold ['60 livres (acceptable range: anything between 58 and 62 livres)'] | ['correct', 'correct']
- [cell] How many albums has Bush released? | ans 10 | gold ['8'] | ['correct for one reading', 'correct for one reading']
- [pin] What is the armed conflict within a nation called? | ans non-international armed conflict | gold ['civil war'] | ['correct', 'correct']
- [webgate] Who was the director of Some Like It Hot? | ans Billy Wilder | gold ['George Archainbaud'] | ['correct', 'correct']
- [pin] Who was the producer of Police Squad!? | ans Robert K. Weiss | gold ['Jim Abrahams', 'James S. Abrahams'] | ['correct', 'correct']
- [indep] When did Ark: Survival Evolved first come out? | ans June 2, 2015 | gold ['2017-08-27', '27-Aug-17'] | ['correct', 'correct']
- [indep] What day, month, and year did Carrie Underwood reveal the track listing for her album "Storyteller"? | ans September 9, 2015 | gold ['September 10, 2015'] | ['correct', 'correct']
- [pin] Who is the youngest quarterback to ever win the Super Bowl? | ans Ben Roethlisberger | gold ['Patrick Mahomes'] | ['correct', 'correct']
- [pin] Who was the composer of Grandpa? | ans Howard Blake | gold ["Jamie O'Hara"] | ['correct for one reading', 'correct for one reading']
- [cell] What is the religion of Francis? | ans Christian | gold ['Catholic Church', 'Roman Catholic Church'] | ['correct for one reading', 'correct for one reading']
- [pin] Who was the screenwriter for The Kid? | ans Audrey Wells | gold ['Charlie Chaplin', 'Charles Spencer Chaplin'] | ['correct for one reading', 'correct for one reading']

## Reading (2026-11-09)
- The S31 two-source cell (support 2 of 3, Phi-4 agrees, gate passes, the Wikipedia reader abstained) passes: 55 added releases, 0 wrong against the facts (one-sided 90% upper bound 4.1%), 4 right for one reading. It was rejected in S31 for 8.7% gold-relative errors; against the facts those were reading mismatches. The earlier rejection came from the measure, not the method.
- Independent title retrieval has 2 real errors in 72 (2.8%), below 3% as a point estimate, but the upper bound (7.2%) is above 6% at this sample size: not passed, not ruled out.
- Pinned pages have real errors (5 of 67, all PopQA namesakes: Lim, My Wife, Egg, The Blues, Face): rejected, as before.
- Every truth-relative error in the table is a same-name subject in PopQA or a generic term for a specific name (Doab).
- Next: the cell rule is computable from the S29 sealed outputs without any new generation; it is registered as a secondary confirmatory test there before any S29 result is seen (SEALED_SET_DESIGN.md).
