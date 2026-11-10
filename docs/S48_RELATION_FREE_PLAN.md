# S48: removing the stated limits (plan, 2026-11-10 20:10, before any S48 output)

The user's objection: the results are limited (seven templated relations, one corpus, one sentence per witness, language-model reviewers, a
frozen August 2025 snapshot) and the novelty is modest. Related work (docs/S42_RELATED_WORK.md) already covers quote-backed answers, sufficiency
verifiers, round-trip and substitution checks. What can still be new has to come from taking away a limit and showing that the guarantee survives.
Four directions, in the order they will be tried:

A. **Relation-free witness rule.** W1 needs a hand-written frame check per relation. E11/W4 shows that a quote-only judge plus a swapped-value control
   works for open claims. Replace the seven frames by one rule for any (question, answer): the quote is a sentence; every number, year and ordinal
   of the question occurs in it; a quote-only 4B judge says YES to the answer and NO to a swapped answer of the same shape. Test on open questions
   (SimpleQA-style FRESH-5 releases of the frozen system), where no frame exists, against the frozen display (first accepted span).
B. **Quote chains.** A claim that needs two sentences (born in Lyon; Lyon is in France) is now Unresolved. A witness of two or three sentences, each
   checked, with a reader that must derive the answer from the set and fail when one sentence is removed (necessity test). Test on two-hop questions.
C. **Other corpora.** Wikipedia is a choice, not part of the method. Run the same rule on a corpus we did not build it for (the web pages the
   frozen system already fetches; later, private documents) and report the misleading rate there.
D. **Distilled judge and labels.** About 4,500 two-reviewer labels of 'does this quote state this answer' exist from S42 to S47. Release them as a
   dataset and train a small judge on them; report whether it matches the 4B prompt on held-out items at a fraction of the cost.

## A in detail (frozen now)

Input: the 601 releases of the frozen system on FRESH-5 (results/runs/s22/fresh5_releases.jsonl, source s19), question, answer, local Wikipedia titles.
Candidates: every span the gate accepts (same code as S42 E7), at most 30 per item; each with its sentence window (at most 300 characters).
Rule R (no relation frames, no training): the first candidate in page order such that (1) the quote is a sentence (not a table row, heading or list
line; at least 40 characters), (2) every number, year and ordinal word of the question occurs in the quote, (3) the 4B judge, shown only the page
title and the quote, answers YES to 'does this sentence state that the answer is the answer to this exact question', and (4) answers NO for the same
quote and question with the answer replaced by another release's answer of the same shape (four-digit year, other number, other phrase) that is not
in the quote. An item with no such candidate is Unresolved.
Review: a random 300 releases; for each, the frozen display quote (first accepted span) and, when it exists, the witness of rule R; presented as
separate rows in random order, plus 30 decoys (answer swapped with another release's); two blind reviewers, the quote verdict of E6 (states /
incomplete / not) and a truth verdict with a forced lookup, as in S47.
Predictions (written before any output): the frozen display is misleading (both reviewers 'not') in 8 to 20% of the 300; rule R keeps 65 to 90% of
the releases; among kept, misleading at most 2% and false at most 3%; the judge says YES to a swapped answer for at most 10% of candidates; the quote
verdict 'states' for both reviewers rises from the frozen display's rate to at least 90% for rule R.
If R keeps at least 65% with misleading at most 2%, the relation-free rule replaces W1 in the tool and the seven-relation limit is lifted for
single-sentence witnesses. FRESH-5 is design data (used in S22 to S25); a sealed set follows for the final claim (the Mintaka or S40 releases).

## Result A (run 20:08 to 20:11; results/runs/s48/A_result.md; design data)

601 releases of the frozen system on FRESH-5. Rule R kept a witness for 394 of 601 (65.6%); in the random 300 that were reviewed it kept 195 (65.0%).
The judge said YES to a swapped answer for 1 of 864 candidates (0.12%). Blind quote-only review of 360 rows (300 frozen display quotes, 30 witnesses
of rule R that differ from them, 30 decoys, two of which drew the same release as another decoy, so 28 distinct decoys, all 28 caught by both reviewers). The truth verdict planned for the review was not collected: the answers of FRESH-5 were audited against the facts in S22, and this test is about the quote:

| Quotes | n | misleading for both | 'states' for both |
|---|---|---|---|
| Frozen display (first accepted span), 300 releases | 300 | 60 (20.0%, 97.5% upper 25.0%) | 212 (70.7%) |
| Frozen display, the 195 releases that rule R keeps | 195 | 22 (11.3%, upper 16.6%) | 163 (83.6%) |
| Rule R witness, the same 195 releases | 195 | 2 (1.0%, upper 3.7%) | 185 (94.9%) |

Against the predictions: frozen display misleading in 8 to 20%: met at the edge (20.0%). Rule R keeps 65 to 90%: met at the lower edge (65.0%).
Misleading among kept at most 2%: met as a point estimate (1.0%; upper 3.7%). 'States' at least 90%: met (94.9%). Judge accepting a swapped
answer at most 10%: met (0.12%).
Cost, stated plainly: rule R withholds 35% of the releases (105 of 300). The frozen display of those withheld releases was misleading in 38 of 105
(36%), against 11% for the kept ones, so most of what is withheld is what a re-check would have caught; but the answers withheld are often right.
Applied to FRESH-5's 37.2% coverage, the relation-free requirement 'the quote states the answer' leaves about 24% coverage, below the 35% floor
that the earlier programme used for silent error. Both numbers are reported; they answer different questions (is the answer wrong; will a re-check
mislead).
Two quotes remain misleading under R (not examined further): one for the question about the Kashmiri word for a bridge, a sentence that mentions a bridge
name without defining the word, and one for the question about the district originally known as Panwangam.
Status: FRESH-5 was used in S22 to S25, so this is design data. The rule is frozen as written above (no change after seeing results). It is registered
for a sealed confirmation on the releases of S40 (docs/S40_PLAN.md, dated line 20:12).

