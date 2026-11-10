# S43: long-form claims and ambiguous questions (plan, 2026-11-10 14:37, before any reader output; the candidate list s43_cands.jsonl, CPU only, was built at 14:37 right after this file)

Why: the programme's product is only useful if it (a) works on more than seven templated short-fact relations and (b) handles
questions that name several things. S41 showed that the short-form machinery keeps 9.9% of the slots of a 4B-written biography,
and rule Q does not carry over (47.5% wrong). A reviewer will ask for both. Related work (docs/S42_RELATED_WORK.md) says what is
not new: quote-backed claims, sufficiency verifiers, round-trip and substitution checks. What S43 tests is whether the E7 witness
idea (choose the quote, withhold when none is sufficient) carries over to claims written by a model.

## Part A. Anchored witnesses for long-form claims (E8)

Diagnosis from existing data (results/runs/s43/feasibility.py, CPU, no models): the 50 design biographies have 1,492 slots
(subject, question, value, type). All 50 subjects have their own page in the local Wikipedia; the value occurs verbatim in
that page for 517 slots (34.7%) and passes the deductive gate (release2 with the subject page as the only title) for 519
(34.8%). S41 asked the 4B reader to answer the slot question from the top five retrieved pages and kept 147 (9.9%). Most of
the loss in S41 is therefore retrieval and agreement, not the gate. Dates (3 of 62 pass) and lists (occupation 40 of 185)
lose most to string format.

Design (rule W2, written now):
1. Evidence: the subject's own page only (title equal to the draft's subject), pinned by hash. No other page, no web search.
2. Candidates: every accepted span of the slot value in page order (at most six), found with the same locate/verify/extra code
   as E7. For DATE slots the value is also tried in the other day-month order (June 26, 1993 and 26 June 1993). List values
   (comma or 'and') are tried whole only.
3. A candidate is the witness if the 4B reader, shown only the page title and the quote, returns the value for the slot question
   (G), and returns the swapped value when the span is replaced by another slot's value of the same type (W).
4. The slot is kept if a witness exists; the output for the slot is the quote and its page title. Otherwise the slot is dropped.
   No new text is written: the long-form output is the list of kept quotes.
5. Not in the rule: Phi-4, the frame check (it is written for seven relations), sources other than the subject page.

Review: every kept slot, a random 40 of the dropped slots, 30 decoys (value swapped with another slot's of the same type, or
question swapped with another subject's). Two blind reviewers with web search; they see the question, the value, the page title
and the quote. They give (a) the quote verdict states / incomplete / not as in E6, and (b) whether the claim is true: right /
wrong / unsure, using web search. Misleading = both say 'not' for (a); false = both say 'wrong' for (b).

Predictions (written before any run):
- Retention (kept / 1,492) between 15% and 30%; the S41 value was 9.9%.
- Kept slots that are false for both reviewers: at most 3%; misleading quotes among kept: at most 2%. Decoys: at least 27 of 30.
- Slots dropped in the random sample that are false for both: at least 20% (the rule drops the false claims first).
- Retention by type: highest for year, person, nationality (over 40%); near zero for OTHER, NUMBER.
These are design-set numbers (the 50 biographies were used in S37 and S41). If the false share among kept is at most 3% and
retention is above 15%, the rule is frozen and a sealed test follows on 50 new subjects drafted by the same model. If it fails,
the failure modes are described and the rule revised on this design set, once.

## Part B. Ambiguous questions (E9; design only now)

Question: when a question can be read as several things (the title 'Heat' is a film, a song, a physical quantity), can the system
release one answer per reading, each with its own witness, instead of guessing or staying silent? Planned test: take the
namesake questions of the second sealed set that the gold audit marked as ambiguous (docs/S42 and Section 5.8 of the paper),
retrieve the candidate pages whose title equals the subject up to a bracketed qualifier, apply W1 to each reading, and release
the list of (reading, answer, quote). Measures: share of questions whose intended reading is in the list, share of listed
readings whose quote states its answer (blind review as in E7), and the size of the list. Predictions and the exact set are
fixed in a dated amendment before it is run. Not started.

## Order
A first (GPU is free until the S40 prefetch ends, about six hours from 14:35). Then B. The S40 chain takes the GPU lock when
the prefetch is done; S43 steps use the same check-after-write lock and idle priority and do not delay it.

## Results, part A (E8; run 2026-11-10 14:38 to 14:44; results/runs/s43/S43_result.md; design data)

Rule W2 kept 181 of 1,492 slots (12.1%; 41 of 50 biographies keep at least one). 526 slots had a candidate span, 181 passed the two
reader checks. Blind review of 251 rows (181 kept, 40 random dropped, 30 decoys; decoys 30 of 30 caught; reviewers agreed on the quote
verdict in 202 of 211 rows and on the truth verdict in 242 of 251):

| Rows | n | claim false for both reviewers | quote misleading for both | quote 'states' for both |
|---|---|---|---|---|
| Kept | 181 | 8 (4.4%, 97.5% upper 8.5%) | 6 (3.3%, upper 7.1%) | 141 (77.9%) |
| Random dropped | 40 | 15 (37.5%) | | |

Against the predictions: retention 15 to 30%: FAILED (12.1%). Kept false at most 3%: FAILED (4.4%; cluster bootstrap upper 8.9%).
Kept quote misleading at most 2%: FAILED (3.3%). Decoys at least 27 of 30: met. Dropped false at least 20%: met (37.5%). Retention by
type: year 37%, nationality 45%, person 24%; near zero for OTHER and NUMBER: partly met.
Failure modes of the 8 false and 6 misleading kept slots (listing in S43_verdict_listing.md, not for release): four are table rows
(a season line or a filmography row: the quote holds the number but not the claim); four put a constraint of the question that the quote
does not hold (the fifth album, the first major success, a named series, a start of career); one is a question that is itself
malformed. S42's 'sentence' flag (the quote is a sentence, not a table row or heading) was computed but not part of W1 or W2.
Post hoc check on the same 181 (results/runs/s43/s43_refine.py; once, as the plan allows): requiring a sentence quote and requiring every
number, year and ordinal word of the question to occur in the quote keeps 151 slots (10.1%) with 3 false (2.0%, upper 5.7%) and 1
misleading (0.7%). That is the retention of S41 (9.9%, false 1.4%) with the quote also checked, not a step towards use.
Reading: anchoring on the subject's page raises the ceiling (34.8% of slots have a gate-passing span) but a value-string witness
cannot reach most claims of a 4B biography, because they are paraphrases, lists or qualitative statements (the dropped sample is 37.5%
false and 62.5% not false). A sealed test of W2 or its revision would repeat S41's low retention. Next: part C below.

## Part C. Sentence-level witnesses for claims (E11; written 2026-11-10 14:45, before any run)

Change: the witness is chosen by what a sentence says, not by whether the value string occurs. For each slot the candidates are the
three sentences of the subject's page with the highest content-word overlap with the draft sentence the slot came from (sentences
only: not table rows, headings or list lines; at least 40 characters). A candidate is the witness if (J) the 4B judge, shown only the
page title and the sentence, answers YES to 'does this sentence state that V is the answer to Q?' and NO for the same sentence with V
replaced by another slot's value of the same type (control), and (N) every number, year and ordinal word of the question occurs in the
sentence. First candidate in rank order that passes. The slot is kept with the sentence as its quote. Values are not required to occur
in the page as a string, so paraphrases and lists can pass; the deductive gate (typed verbatim span) is therefore not part of this rule,
and a kept slot carries the guarantee R1 only for the quote (the sentence exists on the page), not for the value string.
Predictions: retention 20 to 40%; false for both reviewers among kept at most 3%; misleading quote at most 2%; control YES rate (the
judge accepting a swapped value) at most 10% on the candidates it is applied to. Review as in part A on a fresh sheet.

## Results, part C (E11; run 14:45 to 14:52, review to 14:56; results/runs/s43/E11_result.md; design data)

Rule E11 kept 478 of 1,492 slots (32.0%; 44 of 50 biographies). The judge said YES to a swapped value for 4 of 2,473 candidates
(0.16%; prediction at most 10%: met). A random 300 of the 478 kept slots, 40 dropped slots and 30 decoys were reviewed blind
(decoys 30 of 30; the reviewers agreed on the quote verdict in 315 of 330 rows and on the truth verdict in 361 of 370).

| Rows | n | claim false for both | quote misleading for both | quote 'states' for both |
|---|---|---|---|---|
| Kept (sample of 300 of 478) | 300 | 5 (1.7%, 97.5% upper 3.8%; cluster bootstrap upper 3.2%) | 17 (5.7%, upper 8.9%) | 189 (63.0%) |
| Random dropped | 40 | 24 (60.0%) | | |

Against the predictions: retention 20 to 40%: met (32.0%). Kept false at most 3%: met as a point estimate (1.7%), upper bound 3.8%.
Kept quote misleading at most 2%: FAILED (5.7%). Control at most 10%: met.
Of the 17 misleading quotes, 12 are claims that are true: a vague slot ('what has his leadership been marked by') whose answer is a
generic phrase that no sentence states, or a sentence about the same person that does not hold the value (the Gallipoli sentence for
'whose power did Demosthenes oppose'). The dropped sample is 60% false, so the rule does remove false claims first.
Post hoc check on the same reviewed sample (results/runs/s43/e11_refine.py; this is the one revision the plan allows): requiring
that at least 75% of the content words of the value occur in the quote keeps 198 of the 300 (66%), with 2 false (1.0%, upper 3.6%)
and 3 misleading (1.5%, upper 4.4%), quote 'states' for both in 82%. Vagueness by slot type alone does not help (12 misleading remain).

Frozen rule W4 = E11 plus value coverage of at least 0.75, written 2026-11-10 14:57, before any new subject is drafted:
- Candidates, judge, control and the number check as in part C; the value must also have at least 75% of its content words in the quote.
- Predicted on 50 new subjects: kept slots 15 to 25% of all slots; false for both reviewers among kept at most 3%; misleading quote
  at most 3%; control YES at most 10%; decoys at least 27 of 30.
- The 50 subjects are drawn from English Wikipedia people not among the 50 design subjects, by the same procedure as the design set
  (S37), drafted closed-book by the same model with the same prompt, split into slots by the same code. All kept slots (at most 400)
  are reviewed blind with 40 dropped and 30 decoys. Drafts and slots are written to results/runs/s44 before the rule is applied.

## Result, sealed test of rule W4 (S44; 15:26; results/runs/s44/W4_result.md)

50 new subjects (none among the 50 design subjects), drafted by the same model with the same prompt and split by the same code
into 1,547 slots, before the rule was applied. W4 kept 317 slots (20.5%; 41 of 50 subjects). The judge said YES to a swapped
value for 12 of 2,971 candidates (0.4%). Blind review: 317 kept, 40 dropped, 30 decoys (decoys 30 of 30; the reviewers agreed on the
quote verdict in 334 of 347 rows and on the truth verdict in 377 of 387).

| Rows | n | claim false for both | quote misleading for both | quote 'states' for both |
|---|---|---|---|---|
| Kept | 317 | 15 (4.7%, 97.5% upper 7.7%; cluster bootstrap upper 7.7%) | 15 (4.7%, upper 7.7%) | 235 (74.1%) |
| Random dropped | 40 | 18 (45.0%) | | |

Against the predictions: retention 15 to 25%: met (20.5%). Control at most 10%: met. Decoys at least 27 of 30: met. Kept false at most
3%: FAILED (4.7%). Kept quote misleading at most 3%: FAILED (4.7%). Rule W4 fails its sealed test and is not adopted.
Post hoc breakdown (the set is now design data, nothing below is a test): witnesses that are the first candidate in page order with
the value verbatim in the quote are 198 slots (12.8% of all) with 5 false (2.5%, upper 5.8%) and 3 misleading (1.5%, upper 4.4%); the
value-verbatim witnesses overall are 251 with 11 false (4.4%); later-candidate witnesses carry most of the risk, as in E7. By type,
nationality (31 slots) and date (19) had no failure; organisation had 5 false in 39 (12.8%) and person 3 misleading in 16.
Failure modes of the 15 false kept slots (read from the listing, not counted by category): claims that are outdated (a player's current team after a trade), claims where the sentence holds a related fact and the question asks for another (retiring from international, not professional, football; serving in the Navy Reserve against being offered a place in it), and questions whose answer is the role or the subject itself.
Reading. In long-form drafts the failure is no longer the quote alone: the claim itself is often false or outdated, and the questions
produced by the decomposition are looser than the templated relations of E7. The sentence-level witness reaches 20% retention at
4.7% false and 4.7% misleading, against 0.20% misleading for templated short-form questions. With the rules tried so far long-form
output cannot be offered as 'every claim re-checks'; it can be offered with a stated residual of about 5% among kept claims and a
retention of 13 to 20%. A further rule (first candidate only, verbatim value, restricted types) is a hypothesis for a new fresh set of
subjects, not a result.

