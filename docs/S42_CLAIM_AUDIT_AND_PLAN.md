# S42: does the evidence prove "hallucination is eliminated or transformed"? Audit, revised argument, plan

Date: 2026-11-10. Written before any S42 experiment except E1 (a count over existing outputs, marked as such below).
Request: take "AI hallucination is completely eliminated or transformed" as the target conclusion, check whether the current
arguments prove it, and if not, restate the argument, plan the missing tests and run them on small models.

## 1. Verdict on the conclusion as worded

Not proved, and in one part not provable.

- "Completely eliminated", read as "no released statement is ever false", cannot be proved for an open-world system:
  a released answer can be false because the source is false (S) or because a true source was read for the wrong
  question (R). THEORY T4 already says this. The sealed tests give a bound (0.76% and 0.88%), not zero, and one released
  answer of 1,765 was wrong.
- What can be proved by construction is narrower: no released statement lacks a verbatim, machine-checked quote in a
  hash-pinned page. This holds for any generator, and it is the only part of "completely" that the design can deliver.
- "Transformed" was never measured directly. The paper compares error rates of whole systems; it does not follow the
  raw model's own wrong answers and say what became of each one. The Qualified state exists on synthetic sets only.

## 2. The argument, premise by premise

| # | Premise needed for the conclusion | Status on 2026-11-10 | Evidence | Gap |
|---|---|---|---|---|
| P1 | Every output unit is in exactly one of Verified / Qualified / Unresolved; nothing is emitted outside them | Holds by construction for short answers. Long-form: designed, not measured | release rule; S37 slots | S41 (running) |
| P2 | A Verified statement always carries a quote that passes the mechanical check, whatever model proposed it | Holds by construction; never attacked with a hostile generator | quote_check on all releases | E2 |
| P3 | The raw model's own wrong answers are each turned into a verified right answer, a qualified statement or Unresolved | Not measured before today | none | E1 (done), E2 |
| P4 | What is still released and wrong is rare and bounded | Shown on two sealed sets: upper bounds 0.76% (n=1,526) and 0.88% (n=3,359); 1 of 1,765 wrong against the facts | paper 5.1, 5.8 | natural questions only; never tested on questions built to mislead the reader (E4) |
| P5 | The residual is converted too (a doubtful reading is shown as Qualified, not asserted) | Not implemented on real data | entity lists on synthetic sets only | E3 |
| P6 | The conversion is not trivial (it keeps the model's right answers) | Not measured before today | none | E1 (done): 42% of right answers are lost; E3 tries to recover them |
| P7 | The guarantee does not depend on which model generates the claims | Argued, not tested | T4 | E2 |
| P8 | The bound does not depend on which small models play reader and second reader | One assignment only (Qwen3-4B reads, Phi-4 checks) | S19, S29 | E5 |
| P9 | Scope: other task forms, languages, sources | Short factoid questions, English, one Wikipedia snapshot plus web | paper limits | S41 for long-form; the rest stays a stated limit |

## 3. Restated conclusion (what the completed argument would support)

For any generator, the system's output has three properties:

1. Elimination, exact: no statement is released without a machine-checked verbatim quote from a pinned page (P1, P2).
   This is a property of the release function, tested by attack (E2), not a rate.
2. Transformation, measured: each wrong answer of the raw model becomes a verified right answer, a quoted attribution
   or Unresolved, except a residual with a stated upper bound (P3, P4, P5).
3. Cost, measured: the share of the model's right answers that survive as Verified or Qualified (P6).

"No released statement is ever false" is not claimed. The residual is supported-but-wrong: a real quote that answers a
different question, or a wrong source.

## 4. Experiments

Data rules: S29 is a sealed set that has been opened and reviewed, so anything designed on it is post hoc and is
labelled so. Prospective tests use data not yet seen: S40 (sealed, chain not started), S41 (blind review pending) and
new sets built for E4. Only local models (Qwen3-4B, Phi-4, Qwen3.8-27B, embedding model). One heavy job at a time.

### E1. Paired outcome matrix (done before this file; descriptive, no prediction)

results/runs/s42/matrix.py, S29 sealed set, n = 3,359, gold-relative with the S29 adjudication.

| Baseline answer | n | Verified, matches gold | Verified, mismatch cleared by review | Verified, not cleared | Verified, wrong | Unresolved |
|---|---|---|---|---|---|---|
| Raw model wrong | 2,582 | 1,295 (50.2%) | 34 | 16 | 1 | 1,236 (47.9%) |
| Raw model right | 680 | 393 (57.8%) | 2 | 0 | 0 | 285 (41.9%) |
| Raw model no answer | 97 | 23 | 0 | 1 | 0 | 73 |
| Standard RAG wrong | 232 | 1 | 32 | 13 | 1 | 185 (79.7%) |
| Standard RAG right | 2,939 | 1,710 (58.2%) | 4 | 4 | 0 | 1,221 (41.5%) |

Reading: of the raw model's 2,582 wrong answers, 17 (upper bound 1.05%) are still released without being cleared, one
of them wrong for both reviewers; half are replaced by a verified right answer and half become Unresolved. The cost is
large: 42% of the answers the raw model or RAG had right are withheld. The release decision is almost independent of
whether the raw model knew the answer (58% against 52%).

### E2. Any generator: claims from hostile generators through the verifier (CPU, existing reader outputs)

Claim verification as in S41: the value is the only candidate; kept if at least 3 of 3 sources hold an answer that
agrees with it, the gate finds it as a typed verbatim span, and Phi-4 agrees. Reader outputs do not depend on the claim.
Generators: (a) the raw model's short closed-book answers (4 words or fewer); (b) decoys: the reference answer of another
question of the same relation (wrong unless by coincidence); (c) for released questions, any reader answer that
disagrees with the released one.
Predictions (fixed now): (b) kept at most 3 of 3,359; (a) gold-wrong claims kept and not cleared at most 1%;
(c) kept at most 2%. Every kept claim re-passes the quote check (0 exceptions).
If (b) or (c) fails: the agreement function leaks; report the leaks and fix the matcher in a new, dated rule.

### E3. Qualified state on real data (design on S29, prospective on S40 and S41)

Rule Q, fixed here before looking at any S29 cell: a question the frozen rule does not release becomes Qualified if the
max-support candidate passes the deductive gate (typed verbatim span in a pinned page), whatever the support count and
whatever Phi-4 says. Output form: "According to <page>: '<sentence>'" plus which cross-check failed. The system asserts
the quote, not the answer, so the statement is true whenever the quote check passes. Everything else stays Unresolved.
Predictions on S29 (post hoc set, cells not yet looked at): Qualified adds at least 10 points of coverage; the answer
inside the quote matches gold in 85 to 95% of Qualified items; raw-right answers lost to Unresolved fall from 42% to
at most 30%. Prospective: the same rule, unchanged, as a secondary analysis on S40 and on the S41 slots.
Stop rule: if gold match in Qualified is below 80% on S29, Qualified is not added to S40.

### E4. Questions built to mislead the reader (GPU, small models, new data, blind review)

P4 was shown on natural questions, where the retrieved page usually answers the question asked. The one known real
error is a question whose qualifier the page does not match. Build sibling questions from S29 releases by changing
the relation while keeping the subject (birth place to death place, birth year to death year, director to producer and
to composer, author to translator and to publisher, capital to largest city), so that the page holds a typed span that
answers the old question. Run the frozen rule with local-Wikipedia evidence; two blind reviewers with web search judge
every release (gold hidden, decoys mixed in).
Predictions: coverage falls well below the natural 52%; among releases the wrong rate is above 1% (expected 3 to 10%),
and most wrong releases repeat the original relation's answer. If the wrong rate is at most 1%, P4 extends to this
attack. If above, test one fix only, fixed before unblinding the second half: a frame check that the quoted sentence
holds the question's relation word or a listed synonym; failures go to Qualified. Related work to cite, not redo:
SQuAD 2.0 unanswerable questions, contrast sets.

### E5. Role swap (GPU, small models)

Phi-4 as reader (plain and cautious), Qwen3-4B as second reader, same gate, local-Wikipedia evidence, on the S29
questions (opened set: post hoc, gold-relative with the existing adjudication). Compared with the unswapped
Wikipedia-only pipeline on the same passages. Prediction: coverage changes by more than 5 points in either direction;
gold-wrong releases not cleared stay at or below 1.5% of releases for both assignments.

E4 details, fixed 2026-11-10 10:13 before any E4 output (code: results/runs/s42/e4_build.py, e4_run.py):
- 741 sibling questions and the 741 original questions of the same subjects as a control arm (seed 4242). Types: death place 120,
  death year 120, producer 100, composer 100, publisher 80, translator 80, largest city 41 (all from S29 releases), and 100 questions
  with a year, shifted back by 9 years (sampled from all S29 questions with a year).
- Pipeline: the Wikipedia-only one used for S41, as question answering. Verified = both Qwen3-4B readers answer and agree, the gate
  finds the answer as a typed verbatim span, Phi-4 agrees on the same passage. Qualified (rule Q) = not Verified, and the first
  answering reader's answer passes the gate. This is not the frozen three-source rule (no web search here), so the control arm
  measures the same pipeline on natural questions.
- The frame check is fixed now instead of after half the review: a Verified item moves to Qualified unless its quoted sentence
  holds a word of the question's relation (list in e4_run.py), or, for questions with a year, that year or a range covering it.
  Both systems (without and with the frame check) are reported on both arms.
- Review: every Verified sibling item, 60 random Verified control items and 20 decoys, mixed, two blind reviewers, gold hidden.
- Prior work: RefusalBench (arXiv 2510.10390) builds unanswerable variants by 176 perturbations and finds refusal accuracy below
  50% for frontier models on multi-document tasks. E4 is not a new benchmark; it is one attack aimed at this gate.

## 5. Order

E1 done. E2 and E3 (CPU) now. S41 review when its run ends. E4, then E5, on the GPU one at a time after the S41
reader step. S40 unchanged, with rule Q added as a secondary analysis before its chain starts.

## 6. Results

Predictions are quoted from section 4. A prediction that did not hold is marked FAILED and is not reworded.

### E2 (run 2026-11-10; results/runs/s42/E2_claims.md)

| Generator | Claims | Kept by the verifier | Prediction | Outcome |
|---|---|---|---|---|
| (b) decoys: another question's reference answer | 3,359 | 0 (upper bound 0.11%) | at most 3 | met |
| (a) raw model, gold-wrong short answers | 954 | 13 (1.36%); 12 not cleared by the S29 review (1.26%, upper bound 2.19%) | at most 1% not cleared | FAILED |
| (a) raw model, gold-right short answers | 495 | 332 (67.1%) | none | |
| (c) reader answers that disagree with the release | 21 | 1 (4.76%) | at most 2% | FAILED on n = 21 |

Every kept claim re-passed the quote check (0 exceptions), so property 1 of section 3 held under all three generators.

What the 13 kept gold-wrong claims are: one is the known wrong release (Danilo Medina for the Dominican Republic in
2011). Seven are a true but coarser place than the reference ("Mexico", "France", "Ohio", "Italy", "Portugal",
"Germany", "Nigeria"): the agreement function is token containment, so a country agrees with "city, country". Five are
another reading or a stale reference (Mbabane, Bujumbura, Bertolt Brecht, Yash Chopra, Aśvaghoṣa). Nine of the 13 were
never reviewed, because the system released a different value or nothing for those questions; they go to two blind
reviewers with the E4 sheet. The one kept claim in (c) matches the reference answer.

Two consequences. First, with claim verification the generator chooses the granularity: a model that says only the
country gets a Verified country. That is a true statement and a less useful one, and the paper's bound, which is about
the system's own candidate, does not cover it. Second, the 1% prediction failed against the reference answers; whether
it fails against the facts is decided by the blind review, not here.

### E3 (run 2026-11-10; results/runs/s42/E3_qualified.md)

S29, n = 3,359: Verified 1,765 (52.5%), Qualified 384 (11.4%), Unresolved 1,210 (36.0%).

| Prediction | Result | Outcome |
|---|---|---|
| Qualified adds at least 10 points | 11.4 | met |
| quoted answer matches gold in 85 to 95% of Qualified items | 311 of 384 = 81.0% | FAILED (above the 80% stop line, so rule Q goes to S40 as planned) |
| raw-right answers lost to Unresolved fall from 42% to at most 30% | 30.6% | FAILED, narrowly |

The shortfall is one relation. Office questions with a year: 43 of 91 match (47.3%). All other relations: 268 of 293
(91.5%). By cell: support 2 with Phi-4 agreeing 258 items at 90.7%; support 3 with Phi-4 differing 43 at 79.1%;
support 2 with Phi-4 differing 50 at 56.0%; support 1, 33 items at about 45%.

The transformation table that section 1 said was missing (raw model, gold-relative):

| Raw model answer | n | Verified | Qualified, quote holds gold answer | Qualified, quote holds another answer | Unresolved |
|---|---|---|---|---|---|
| wrong | 2,582 | 1,346 (52.1%) | 240 (9.3%) | 59 (2.3%) | 937 (36.3%) |
| right | 680 | 395 (58.1%) | 65 (9.6%) | 12 (1.8%) | 208 (30.6%) |
| none | 97 | 24 | 6 | 2 | 65 |

A Qualified statement asserts the quote, which is true whenever the quote check passes. The 59 + 12 + 2 items whose
quote holds another answer are true attributions that answer the question badly; a reader who takes the quote as the
answer is misled in 19% of Qualified items. This is the measured size of the residual that rule Q moves from "silent"
to "shown with a warning", and it is reported as a cost of the state, not hidden in it.

Against standard RAG: of its 232 wrong answers, 47 are Verified (1 matches gold, 32 cleared, 13 not cleared, 1 wrong), 56 Qualified
(54 with another answer than gold), 129 Unresolved.

### Rule T (post hoc; results/runs/s42/temporal.py)

Of 1,765 releases, 11 answer a question that names a year. In 9 the quoted sentence holds no year (8 right, 1 wrong:
the Dominican Republic item); in 2 it holds the year or a covering range (both right). Rule T would move the 9 to
Qualified and remove the only release that both reviewers called wrong, at a cost of 8 right releases. It was written
after seeing that error, so it proves nothing on S29; it is a fixed secondary analysis on S40 (docs/S40_PLAN.md).

### E4 (run and blind review 2026-11-10; results/runs/s42/E4_result.md)

741 sibling questions (relation changed, subject kept) and their 741 original questions, Wikipedia-only pipeline.
Decoys called wrong by both reviewers: 20/20 (valid).

| Arm | Verified | Qualified | Unresolved | Reviewed releases | Wrong (both) | Rate | 97.5% upper |
|---|---|---|---|---|---|---|---|
| Sibling | 134 (18.1%) | 104 (14.0%) | 503 (67.9%) | 134 | 2 | 1.5% | 5.3% |
| Sibling, with frame check | 97 (13.1%) | | | 97 | 1 | 1.0% | 5.6% |
| Control | 588 (79.4%) | 65 (8.8%) | 88 (11.9%) | 60 (sample) | 0 | 0.0% | 6.0% |

Against the predictions:
- Coverage falls well below the natural level: met (18.1% against 79.4% on the same subjects).
- Wrong rate above 1%, expected 3 to 10%: the rate is 1.5% (2 of 134), below the expected range; the interval (upper
  5.3%) does not settle whether it is above or below 1%. Not confirmed.
- Most wrong releases repeat the original relation's answer: 1 of 2. Not confirmed.
- The frame check removes 1 of the 2 wrong releases and 36 of the 132 others.
The system mostly declines these questions (68% Unresolved) instead of answering the old relation. The two wrong
releases: a director released as producer (quote says "directed by"; removed by the frame check), and the translator
of a play adapted from the novel released as the translator of the novel (quote is about another work; passes the frame
check). The second is a subject mismatch, the case the subject link S of E7 targets.
E2 kept claims, reviewed on the same sheet: 14 rows, 13 right for both reviewers, 1 wrong (Dominican Republic 2011).
So of the claims counted as wrong against the reference in E2, one is wrong against the facts.
The sample cannot support a bound near 1% (134 releases). E4 shows no large failure; it does not extend P4 to this attack.

### E7 (blind test 2026-11-10; results/runs/s42/E7_result.md; rule W1 frozen in section 9 before any test item was scored)

Test: 1,090 Verified and 284 Qualified items outside the E6 sheet. Sheet 1,161 rows (1,017 Verified witnesses, 84 Qualified
witnesses, 60 new decoys), six parts, two blind quote-only reviewers per part. Decoys misleading for both: 59/60 (valid).
Reviewers gave the same verdict in 1,152 of 1,161 rows.

| Rows | n | Misleading (both 'not') | Rate | 97.5% upper | States for both | 'not' for either |
|---|---|---|---|---|---|---|
| Verified witnesses | 1,017 | 2 | 0.20% | 0.71% | 1,004 (98.7%) | 3 |
| witness is the first span | 883 | 0 | 0.00% | 0.42% | 876 (99.2%) | 0 |
| witness is a later span | 134 | 2 | 1.49% | 5.29% | 128 (95.5%) | 3 |
| Qualified witnesses | 84 | 0 | 0.00% | 4.30% | 78 (92.9%) | 0 |

For comparison, the frozen S19 rule showed the first span unchecked: 12.5% misleading (75/600, E6, upper 15.4%).

Against the predictions:
- (h) share of test Verified items keeping a witness 85 to 95%: met, 1,017 of 1,090 (93.3%). Estimated coverage on S29:
  about 49.0% of questions, against 52.5% for the frozen rule (cost about 3.5 points, above the 35% floor).
- (i) misleading at most 3, upper bound below 1%: met, 2 of 1,017, upper 0.71%.
- (j) at least 90% rated "states" by both: met, 98.7%.
- (k) later-span witnesses not worse than first-span witnesses: FAILED. Both misleading rows are later spans (2 of 134, 1.49%,
  upper 5.29%) against 0 of 883. Both come from pages that are not the page of the question's subject (a page on "Spontaneous
  generation" quoted for "Who wrote Generation of Animals?"; the Galatians quote does not say Paul wrote the epistle).
- (l) Qualified witnesses misleading at most 10%: met, 0 of 84 (upper 4.3%).
Reading: the reader-and-lexical witness rule removes misleading quotes at a cost of about 7% of releases; the quote a person
re-checks states the answer in 98.7% of cases and is misleading in 0.2% (upper 0.71%). Not claimed: zero. The later-span
witnesses carry the residual risk; a restriction to first-span witnesses would be a post hoc rule and would need its own
fresh test. Development numbers for W1 are optimistic (127 combinations seen); the test numbers are not.

### E6 interim (2026-11-10; review and frame check only; results/runs/s42/E6_result.md)

The eight blind verdict files are in; the quote-only reader G had not run when this was written (the GPU was held by E4).

- Decoys: 60 of 60 misleading for both reviewers (valid). Same verdict in 789 of 797 rows.
- Verified random sample (n = 600): the displayed quote does not state the answer for both reviewers in 75 rows
  (12.5%, 97.5% upper bound 15.4%); 18 more need the page (3.0%). **Prediction (a), 1 to 6%, failed.** Prediction (b),
  8 to 25% for the two together, was met (15.5%).
- Qualified random sample (n = 100): 55 misleading (55.0%, upper bound 65.0%), 9 need the page. **Prediction (c),
  5 to 20%, failed.** All 26 death-year items and 16 of 23 office items are misleading.
- The answers are mostly right: 72 of the 75 misleading Verified rows match the gold. The failure is right answer,
  wrong evidence. The gate quotes the first place where the answer string passes its type checks, and that place is
  often a page about someone or something else, a title line, a list line, a table row or an incidental mention.
- By relation (Verified, misleading / n): death year 22/61, author 14/96, birth place 21/168, birth year 7/145,
  director 6/120, capital 3/8, office 2/2.
- Frame check F on the Verified sample: removes 71 rows (11.8%; met), catches 49 of 75 (65%; met), leaves 26 misleading
  among 529 (4.9%, upper bound 7.1%). **The third part of prediction (d), at most 1.5% left, failed.**
- Dominican Republic 2011: 'not' for both reviewers and removed by F, as predicted in (g); G pending.

Consequence for the claim. R1 (the quote exists) held without exception. R2 (the quote states the answer) fails in about
one release in eight on S29, so the system as frozen does misattribute: a person who re-checks the quote finds that it
does not say what the output says, even though the answer is usually true. Under the target of section 7 this is the
defect to remove, and it was invisible to every earlier review because those reviews judged the answer, not the quote.

### E6 final (2026-11-10 11:10; reader checks added; results/runs/s42/E6_result.md)

Verified sample, n 600, 75 misleading rows:

| Check | Passes, all 1,765 | Removed from sample | Misleading caught | Misleading left | Rate left | 97.5% upper |
|---|---|---|---|---|---|---|
| F frame check | 1,547 (87.6%) | 71 (11.8%) | 49/75 | 26 | 4.9% | 7.1% |
| G reader with swap (4B) | 1,097 (62.2%) | 216 (36.0%) | 72/75 | 3 | 0.8% | 2.3% |
| G step 1 only (no swap) | 1,521 (86.2%) | 80 (13.3%) | 70/75 | 5 | 1.0% | 2.2% |
| Strict rule, F and G | 1,061 (60.1%) | 228 (38.0%) | 73/75 | 2 | 0.5% | 1.9% |
| G with Phi-4 (secondary, reviewed rows) | | 190 (31.7%) | 74/75 | 1 | 0.2% | 1.4% |

Qualified sample, n 100, 55 misleading: the strict rule passes 32 rows, 1 misleading (3.1%, upper 16.2%).

- (e) G removes 10 to 30%: FAILED (36.0%). Catches at least 80%: met (72/75). Leaves at most 1%: met (0.8%).
- (f) Strict rule leaves 0 misleading rows: FAILED (2 of 372, upper 1.9%).
- (g) Dominican Republic 2011: 'not' for both reviewers, removed by F and by G. Met.
- Targeted stratum: the strict rule removes 20 of 37 and all 4 of its misleading rows.
Reading: checking the first quote and dropping the item when it fails costs 40% of the releases (coverage 52.5% to about
31.6%, under the 35% floor) and still leaves 2 misleading rows. The swap step is what costs coverage (13.3% removed
without it, 36.0% with it). This is the reason for E7: keep the item and change the quote.

## 7. Amendment 2026-11-10 10:35: the target is zero misrepresentation of the source (E6)

Written before any output of E4, any E4 or S41 review verdict, and any E6 item was read.

**Target, as the user states it.** That an answer is never wrong cannot be proved and is not the target. What has to be
removed completely is made-up content and saying that a source says something it does not say. The test is practical: a
person who re-checks a released statement against its quote must not find that they were misled, because that check then
costs more work than it saves.

**What this asks of each output.**

- R1, existence: the quote is verbatim in the pinned page. Machine-checked, exact, 0 exceptions so far.
- R2, sufficiency: the quoted sentence, read with the page title, states the released answer to the question as asked:
  same subject, same relation, same time. Nothing checks this today. The gate checks the type of the span and words of
  the question, not that the sentence states the relation. A violation of R2 is exactly the case the user names: a real
  quote presented as saying something it does not say.
- R3, labels: a Qualified output asserts only "the page says"; R2 applies to it in the same way.

**What the evidence so far covers.** R1 only. Every review so far judged the answer against the facts, not the quote
against the answer. One known R2 violation: the Dominican Republic 2011 release, whose quote holds no year.

### E6. Re-check audit of quotes (S29 outputs; CPU build, blind review, small-model checks on the GPU)

Population: the 1,765 Verified releases of S29 and the 384 Qualified items of E3. The displayed quote is the sentence or
table row holding the span, cut to at most 300 characters around the span.

Review sheet (seed fixed in e6_build.py): 600 Verified and 100 Qualified drawn at random; a targeted stratum outside the
rates (the Verified releases whose answer does not match the gold and that the random draw missed); 60 decoys (30 with the
answer replaced by the answer of another question of the same relation, 30 with the question replaced by a question of
the same relation about another subject). A reviewer sees the question, the answer, the page title and the quote, has no
other source, and gives one of:

- states: the sentence, with the page title as its subject where it names none, says that this is the answer to this question;
- incomplete: same subject and relation and consistent with the answer, but a part of the question is not in the sentence
  (the year, which office, which of two people), so the reader has to open the page;
- not: the sentence is about another subject, relation or time, or does not say this.

Two blind reviewers per row. A row is **misleading** when both say "not", and **needs the page** when neither says
"states" and it is not misleading. Decoys are valid if at least 90% are misleading.

Two mechanical checks, fixed now and scored against the review:

- F, frame check: the lexical check of E4 (a word of the relation in the quote; for office questions the year or a
  covering range; life-span ranges for birth and death years).
- G, quote-only reader with a swap: the 4B model gets only the page title, the quote and the question, and must return the
  released answer; then the span in the quote is replaced by the span of another item of the same relation, and the
  model must return the replacement. The second step removes answers the model gives from memory instead of from the
  sentence. Phi-4 on the reviewed rows is a secondary reader.

Strict rule = frozen rule and F and G. Items that fail move out of Verified (Qualified items that fail become Unresolved).

Predictions (S29 is an opened set, so E6 is a design study; the strict rule is frozen after it and applied to S40 before
any S40 output is read):

- (a) Verified sample: misleading 1 to 6%; so the current system does not meet the target.
- (b) Verified sample: misleading or needs the page 8 to 25%.
- (c) Qualified sample: misleading 5 to 20%.
- (d) F removes 5 to 20% of the Verified sample, catches at least 60% of the misleading rows, and leaves at most 1.5% misleading.
- (e) G removes 10 to 30%, catches at least 80%, and leaves at most 1% misleading.
- (f) Strict rule: 0 misleading rows among the sampled Verified items that pass it (the upper bound is reported with the count).
- (g) The Dominican Republic 2011 release is not rated "states" by either reviewer, and F and G both remove it.

If (f) fails, the next step is a wider quote (the sentence plus its neighbours or the table header) chosen as the smallest
window that passes G, registered with a date before it is run.

## 8. Amendment 2026-11-10 10:45: choosing the witness (E7)

Written after the interim E6 result above and before any output of the quote-only reader G was read.

**Cause.** `release2` returns the first accepted span. Listing every accepted span of the same answer in the pinned pages
(results/runs/s42/e7_cands.py, CPU) gives 11,148 spans for the 2,149 items, 5.6 per Verified item. A sentence that
states the answer usually exists; the gate does not look for it.

**Split.** The S29 items on the E6 sheet (600 Verified, 100 Qualified, 37 targeted) are development data: their verdicts
have been read and rules have been tried on them; the items that the 60 decoys were built from count as development
data too. The 1,090 Verified and 284 Qualified items outside the sheet are the test set. No verdict exists for them and
none of their quotes has been read.

**Rule family.** The witness of an item is the first accepted span, in page order, whose displayed quote passes every
check of a fixed list. An item with no witness leaves Verified and is shown as Unresolved; nothing is quoted for it.
Candidate checks:

- F, the frame check of section 7;
- S, subject link: every content token of the question (question words, relation words and years removed, accents
  folded) occurs in the page title or in the quote (results/runs/s42/e7_lib.py);
- G, the quote-only reader with swap of section 7, and variants of it that ask a contrasting question of the same quote;
- P, the page is the subject's own page (its title occurs in the question).

**Tried on development data so far (lexical checks only, first span).** F and S: 502 of 600 rows pass, 5 misleading
(1.0%). F, P and "the quote is a sentence, not a list or table line": 421 pass, 1 misleading. The misleading rows that
survive name the subject as a secondary entity (a death year of the person's companion; a twin's birth year) or say
"from X" where the question asks "born in X". Lexical checks do not read; whether G removes these is the open question.

**Procedure.** (1) Score G on the development rows when the E6 reader step finishes. (2) Fix one list of checks, write
it here with its predictions and a date. (3) Only then compute witnesses on the test set, draw the blind sheet (all test
Verified items that have a witness, a sample of test Qualified items, new decoys, same instructions as E6) and run two
reviewers per part. (4) Unblind.

**Endpoint, fixed now.** Among test Verified items with a witness: number misleading for both reviewers and its 97.5%
upper bound. The target of section 7 is zero; the criterion for calling the defect removed at the scale this set can
show is an upper bound below 1%, which about 900 rows meet with at most 3 misleading. Second endpoint: share of the
1,090 test Verified items that keep a witness; below 67% the selective coverage on S29 would fall under the 35% floor
of L2 and the rule costs too much. Both are reported whatever they are.

## 9. Amendment 2026-11-10 11:14: the frozen witness rule (E7), written before any test item was scored

Development scoring (results/runs/s42/E7_dev.md, E7 dev only, E6 sheet rows, first-span quote against the blind review;
127 check combinations were looked at, so the numbers below are optimistic):
- Verified, n 600, 75 misleading: F and S and G leaves 0 misleading among 492 passing rows (97.5% upper 0.75%) and keeps
  489 of the 503 rows both reviewers rated "states". The same pass without the reader (F and S) leaves 3 or more from the lexical
  side; G alone leaves 5; adding W costs 126 passing rows (366 left) for no gain over F+S+G beyond one extra row.
- Qualified, n 100, 55 misleading: F and S and G passes 37 rows with 0 misleading (upper 9.5%).
- Witness availability on dev Verified (script e7_dev_witness.py): 492 items (82.0%) keep their first span; 67 more keep a
  later span; 559 of 600 (93.2%) keep a witness.

Frozen rule W1 (small, no search over combinations on the test set):
1. Candidates: the accepted spans of the item in page order, at most four per item (the first span, then the next three
   that pass F and S), exactly as run by e7_run.py.
2. A candidate is the witness if it passes F (frame check), S (subject link) and G (Qwen3-4B, quote only, returns the
   answer). The first such candidate in page order is shown; its displayed quote is the one reviewed.
3. No witness: the item is Unresolved and nothing is quoted. W, I, C and P are not part of the rule (reported only).

Test set: the 1,090 Verified and the 284 Qualified items of the S29 outputs that are not on the E6 sheet (E6 sheet items
including decoy sources are development data). Run: `bash results/runs/s42/run_e7.sh test`.

Predictions (fixed now):
- (h) Share of the 1,090 test Verified items that keep a witness is between 85% and 95% (dev 93.2%, expect lower on fresh items).
  Below 67% would put coverage under 35% and fail the cost endpoint.
- (i) Blind review of all test Verified witnesses: misleading (both reviewers "not") at most 3 of about 950, so the
  97.5% upper bound is below 1%. If the count is 4 or more, W1 fails the endpoint and is reported as failed.
- (j) At least 90% of witnesses are rated "states" by both reviewers.
- (k) Among witnesses that differ from the first span, misleading is not above the rate for first-span witnesses.
- (l) Qualified items with a witness: misleading at most 10% (a sample of at most 100 is reviewed).

Review: two blind reviewers per part, same instructions and decoys as E6 (60 new decoys: 30 answer, 30 question), new
sheet, default model reviewers with web search not needed (quote only). Verdict files stay out of the release.

