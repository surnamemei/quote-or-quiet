# S73: rule Q3, phrase extraction for free-phrase answers (design, 2026-11-13)

Why. G4 failed twice. On NQ-open (S68) rule Q2 kept its errors low (5 of 1,500 after adjudication) but answered 17.1%: of 1,166 questions without a witness, 715 had a candidate supported by two readers but no gate-accepted typed span, because NQ readers often answer with a sentence ('The donkey talks in the Bible in Numbers 22:28-30.') and the typed checks were built for short Wikidata answers.

Rule Q3 (results/runs/s73/g4c_design.py). Same readers and pages as Q2. The typed-span step is replaced by phrase extraction: sub-phrases of the reader answers (1 to 8 tokens, trimmed of stop words, with a content token not in the question), supported by at least two readers, found verbatim in a sentence window of a retrieved page; only maximal phrases; at most 4 per question. Witness: the 27B says YES for the phrase and NO for a swapped phrase (R27). Release when the witnessed phrases occur together in one reader answer and the question is not time-sensitive.

Design data only: the 1,500 NQ-open questions of S68, whose sealed test is spent. No sealed item was used.

Result (G4C_d68_result.md).
- Released 377 of 1,500: coverage 25.1% (Q2 17.1%). 208 questions were released by both rules; Q2 released 48 that Q3 did not.
- Gold-wrong 80 (5.33% of questions, 21.2% of releases; Q2 30, 11.7%). Not adjudicated.
- Withheld: no witness 1,090, conflict 14, time-sensitive 19.
- Funnel: a phrase was found verbatim on a retrieved page for 1,045 questions; the 27B said YES on 461 of 5,312 sentence checks, and 454 passed the swap test.

Reading.
- Coverage. Even if every gold-wrong release were cleared, 25.1% is far below the 35% floor. The binding step is now the 27B judge, not the span step: it accepts few sentences for free phrases, consistent with its 47.5% false-reject rate against human labels (S71).
- Errors. The gold-wrong releases are a mix. Some are answers NQ's gold does not list but which are defensible (Atlantic Ocean for Uruguay, acetate ion, Theophilus for Acts, Radcliffe Line). Some are truncations, where the most supported phrase is shorter than the answer ('2017' for 'May 19, 2017'). Some are plain errors (Eleanor Roosevelt for who changed the role of the first lady; Brothers Grimm for the original Little Red Riding Hood). S68's adjudication cleared five sixths of Q2's gold-wrong releases. At that rate, Q3's 80 would leave about 13 errors, above the 7 that the bound allows on 1,500 questions.

Decision. No third sealed test of G4 with Q3: it would fail on coverage and probably on errors. G4 on natural questions needs either readers that give short answers (so that the typed checks apply) or a judge that accepts more true sentences without accepting decoys. Both are new designs. G4 stays at failed; the tracker is unchanged (41 of 48).

## Ceiling and a looser judge prompt (2026-11-13, design data only)
Ceiling (results/runs/s73/ceiling.py): a gold answer occurs verbatim on the local five pages for 797 of 1,500 questions (53.1%), and on those pages plus the Wikipedia pages named in the web results for 1,256 (83.7%). The evidence is there; the losses are in the release steps.
Judge on Q3 candidates (prompt as in rule R27): for candidates that match the gold it said YES on 302 of 1,801 sentence checks (16.8%); on swapped answers 7 of 461 (1.5%). Some NO verdicts are right (fragments such as 'June' or 'directly'); many are literal readings of loosely worded questions ('when was the show made' against 'aired from March 18, 2005').
Variant v2 (G4C_JUDGE=v2: the question read as a person most likely meant it; swap test unchanged): gold-matching candidates YES 488 of 1,608 (30.3%), but swapped answers YES 106 of 798 (13.3%). Coverage 33.4%, gold-wrong 125 (25.0% of releases).
Reading: loosening the judge buys coverage only by accepting swapped answers nine times as often, which is the failure the swap test exists to catch. Neither prompt gives both 35% coverage and a decoy-safe judge on NQ-open. G4 is not pursued further with the current reader and judge; a third sealed test is not registered. What would change it: a judge that is both lenient on paraphrase and strict on swaps (for example the 27B fine-tuned on reviewed rows, as the 4B judge of S52 was), or readers that answer with a page span directly.
