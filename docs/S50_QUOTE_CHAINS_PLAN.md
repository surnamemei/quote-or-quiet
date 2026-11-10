# S50: quote chains for two-hop questions (plan, 2026-11-10 21:22, before any S50 output)

Limit to remove: a witness is one sentence. A question whose answer needs two sentences (X was born in Ghent; Ghent is a city in Belgium) is Unresolved today.
Pilot: the templated birth-place releases of the S42 test items that have a W1 witness (results/runs/s42/e7_test_witness.json, 221 items); items whose answer is a
single place name with its own page (no comma) are the hop-1 set (71 items). Question: 'In which country was X born?'. Hop 1 is the W1 witness quote (X was born in
the place). Hop 2 is a sentence of the page of the place that states its country.

Chain rule C2 (written now):
1. Hop 2: the 4B reader (plain and cautious) answers 'In which country is PLACE?' from the first 1,500 characters of the page of the place and the two answers agree;
   the country is located in a sentence of that page (a sentence of at least 40 characters, not a table row or heading); a quote-only judge accepts it for the
   sub-question and rejects a swapped country.
2. Bridge: the page title is exactly the place string of the hop-1 quote, and no other page of the title index shares that name as a place (a qualifier with
   city, town, village, municipality, commune or similar), and the page is not a disambiguation page; otherwise Unresolved, because the hop-1 quote does not say
   which place of that name is meant.
3. Chain: a quote-only reader shown both sentences answers the two-hop question with the country, and follows a swapped country in sentence 2.
The necessity of each sentence is reported: whether sentence 1 alone already yields the country.

Review: every accepted chain, every chain rejected only for the bridge rule, and decoys (country swapped); two blind reviewers, two tasks: (a) do the two sentences
together state the answer, for the same place in both (states / incomplete / not); (b) is the country correct for this person (forced lookup).

Predictions: accepted chains 40 to 80% of the 71 items; bridge rejections 10 to 35%; among accepted chains misleading (both 'not') at most 5% and false at most 5%;
'states' for both at least 90%; among the chains rejected only for the bridge at least one wrong country (the rule is needed). Small n: the upper bounds will be wide.

## Machine result and a change of rule (21:52; results/runs/s50/b_out_run1.json, b_out.json)

71 items. The country was found on the page of the place for 69, a sentence 2 existed for 69, the hop-2 judge accepted 68 (it rejected the swapped country), the bridge rule
passed 56 (13 places share their name with another place). Chain reader, first run: it returned the country for 68 of 69, but followed the swapped sentence 2 for 0;
with sentence 1 alone it returned the country for 65 of 69. Accepted by the rule C2 as written: 0 of 71 (prediction 40 to 80%: FAILED).
Cause: the 4B reader knows which country a city is in and prefers it to a sentence that says otherwise, so a counterfactual substitution test at the chain level cannot
show that sentence 2 is what the answer rests on. A second run with the instruction to follow the sentences even if they contradict what the reader knows (a change of
the prompt after seeing the first run; both runs are kept) returned the country for 66, followed the swap for 2, and accepted 2 of 71. The test is therefore not
usable with this reader for common-knowledge hops; it would need a place the reader does not know.
Revised rule C2' (written after seeing these counts, so the review below is its first test): accepted = the hop-2 judge accepts sentence 2 for the sub-question (swapped
country rejected) and the bridge rule passes. Logic: sentence 1 states the place, sentence 2 states that place's country, the bridge rule makes them the same place;
no chain-level reader is used. C2' accepts 55 of 71 (77.5%); 13 are rejected only by the bridge rule (12 of them the chain reader would have accepted).
Review: 78 rows (55 accepted, 13 bridge-rejected, 10 decoys), two blind reviewers, (a) do the two quotes together state the answer for one place, (b) is the country
correct by lookup. Predictions for C2' (misleading at most 5%, false at most 5%, 'states' at least 90%, at least one wrong country among the bridge-rejected) stand as written.

## Result of the review (21:54; design data, pilot of 71 items)

Blind review of 78 rows by two reviewers (10 decoys, all caught):

| Rows | n | two quotes together misleading (both) | answer false (both) | together 'states' (both) |
|---|---|---|---|---|
| Accepted by C2' | 55 | 1 (1.8%, 97.5% upper 9.7%) | 0 (0.0%, upper 6.5%) | 50 (90.9%) |
| Rejected only by the bridge rule | 13 | 0 (upper 24.7%) | 0 (upper 24.7%) | 13 (100%) |

Against the predictions: misleading at most 5%: met as a point estimate (1.8%), upper bound wide (9.7%); false at most 5%: met (0 of 55, upper 6.5%); 'states' at least 90%: met
(90.9%); at least one wrong country among the bridge-rejected: NOT met (0 of 13), so this pilot does not show that the bridge rule is needed: it withheld 13 correct chains
(19% of the 69 with a sentence 2). The rule is justified by the hazard (a hop-1 quote naming a place that shares its name with another place) and not by an observed error; in 71 items
no such error occurred. The chain-level reader test of rule C2 as first written could not be satisfied (0 of 71) because the 4B reader knows which country a city lies in.
The one misleading accepted chain was not examined further. Limits: one relation pair (birth place, country), 71 items, places with their own page, wide bounds.
What the pilot supports: a two-sentence witness, each sentence checked on its own against its sub-question with the swap control, and an entity-bridge check, answers a two-hop
question that the one-sentence rule leaves Unresolved, with no wrong answer in 55 chains and one doubtful pair of quotes.

