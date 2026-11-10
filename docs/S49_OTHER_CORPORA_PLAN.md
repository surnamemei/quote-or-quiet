# S49: another corpus (plan, 2026-11-10 20:17, before any S49 judge output)

Limit to remove: the corpus is Wikipedia. The method does not use anything specific to it: a stored page, a sentence of that page, a quote-only reader. Test:
the same frozen rule R (docs/S48_RELATION_FREE_PLAN.md, unchanged) on web pages that are not Wikipedia, which are messier (navigation text, lists, comments,
repeated names).
Data: the 601 FRESH-5 releases of the frozen system. For each, the pages the system fetched (cached text, pinned by its sha-256 here), excluding Wikipedia
and its mirrors (domains containing 'wiki', explained.today, alchetron, grokipedia, dbpedia, kiddle, britannica), that contain the released answer as a whole
word (up to 10 occurrences per page, 20 per release). 475 releases have at least one such page (1,184 pages). No gate, no typing: any occurrence is a candidate.
The page 'title' shown to the judge and the reviewers is the domain name (cached text has no title).
Naive display: the first occurrence on the first such page. Rule R: the first candidate that is a sentence, holds the question's numbers, is accepted by the 4B
quote-only judge for the answer and rejected for a swapped answer of the same shape (at most six candidates tried).
Review: a random 300 of the 475 releases; naive display and, where different, the R witness; 30 decoys; two blind reviewers, quote only, no web.
Predictions (before any output): naive display misleading in 25 to 50% of the 300; rule R keeps 30 to 60% of the releases; misleading among kept at most 3%
(upper bound reported); 'states' for both reviewers at least 88%; the judge accepts a swapped answer for at most 10% of candidates.
What it would show: the quote requirement is corpus-independent. What it would not: that the page says something true (web pages are not curated); the
guarantee remains 'the quoted page says this', and a wrong page makes a wrong answer with a correct quote. Truth is not reviewed here.

## Result (20:22; results/runs/s49/C_result.md; design data)

475 releases had a non-Wikipedia page holding the answer; rule R kept 345 of 475 (72.6%); the judge accepted a swapped answer for 0 of 1,118 candidates. Quote-only
blind review of 378 rows (a random 300 releases, 30 R witnesses that differ from the naive quote, 30 decoys; decoys 30 of 30):

| Quotes | n | misleading for both | 'states' for both |
|---|---|---|---|
| Naive display (first occurrence on the first page) | 300 | 59 (19.7%, 97.5% upper 24.6%) | 150 (50.0%) |
| Naive display, the 213 releases rule R keeps | 213 | 24 (11.3%, upper 16.3%) | 131 (61.5%) |
| Rule R witness, the same 213 releases | 213 | 8 (3.8%, upper 7.3%) | 157 (73.7%) |

Against the predictions: naive misleading 25 to 50%: not met (19.7%, lower than predicted). Rule R keeps 30 to 60%: exceeded (71.0% of the sample). Misleading
among kept at most 3%: FAILED (3.8%, upper 7.3%). 'States' for both at least 88%: FAILED (73.7%). Judge accepting a swapped answer at most 10%: met (0%).
Reading: the requirement transfers only partly. Rule R cuts the misleading share from 11.3% to 3.8% on the same releases (a reduction of two thirds), but on messy
web text the remaining rate is about three times that on Wikipedia (1.0%), and 'states' for both is 74%, with many quotes rated 'incomplete' (a sentence that
holds the answer but not the whole question). The eight misleading R quotes are of web kinds: a page title or heading that passes the sentence test (a BBC
page title, a Northwestern page title, a phys.org headline), a date that belongs to another event of the same sentence (a project that began in October 2013 with a
test in January 2014), and a book-listing line. These are failure modes that a stricter sentence test (no title-case headings, no 'Title - Site' lines) and a
check that the answer is not inside a title would address; that is a new rule and needs its own fresh test. Not reviewed: whether the page is true.

