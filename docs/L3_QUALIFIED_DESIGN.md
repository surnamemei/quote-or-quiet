# L3, second half: making the entity slot explicit (Qualified output state). Design, DEV, 2026-11-08

Code: results/runs/l3/qualified.py (decision), qualified_dev.py (evaluation), build_titles.py + titles.db (sense index of the
local FineWiki snapshot, 6,614,655 titles). Hashes: results/runs/l3/qualified_v1_hashes.txt (v1, strict) and
qualified_v2_hashes.txt (v2, adds the mid variant). Design data: popqa_dev, mintaka_dev, SimpleQA dev, fresh. The three
unsealed S19/S21 test sets were scored only after v1 was hashed (16:21); see "Out-of-sample check" for its limits.

## 1. What the first half proves, and what was missing
Every Verified release of the S19 system is a verbatim span of a hash-pinned page that passes V1-V5. That excludes fabricated
answers by construction. It says nothing about whether the page is about the entity the question means. All residual errors
seen so far sit outside the proof: entity choice (PopQA: Lima, Turin, Shaft ...), relation reading (A2), qualifiers and time,
and source or gold disagreement.

## 2. Output states
For a candidate that cleared the S19 gate and veto (span on pinned page P, answer A):
- **Verified** "A": the question's subject mention m has exactly one sense in the sense inventory, or the question names the
  qualifier of one sense, or P's title is a shortened form of a fuller name given in the question.
- **Qualified** "A, assuming m = E": m has two or more senses; E is named explicitly and is P itself, or the sense of the type
  the relation implies (director -> film, author -> book ...) whose page holds A, or the primary topic (bare title) whose page
  holds A, or the only sense whose page holds A; or P is a longer namesake of a single-sense mention (Salaryman -> Salaryman
  Kintaro).
- **Unresolved**: m is ambiguous and no single sense can be named (strict); the mid variant releases as Verified when no sense
  page holds A but P names m.
Sense inventory: local-wiki titles whose core (before a trailing "(...)", or before ", " for place names) normalises to m,
excluding disambiguation, name, list, index and outline pages. Subject mention: the release page's own core if it occurs in the
question (unless a longer question n-gram contains it), else the longest named n-gram matching a title core (possessives stripped;
fragments of a longer capitalised name with no title of its own skipped).

## 3. The extended deductive statement
For every Verified or Qualified output, by construction:
(i) A is a verbatim span of the hash-pinned page P accepted by V1-V5 (first half);
(ii) entity slot: either the sense inventory admits exactly one reading of m (Verified), or the output states the reading E and A
occurs on E's page or P = E (Qualified).
Remaining assumptions, stated rather than proven:
- A_S: the source is true;
- A2: the span answers the asked relation (relation slot);
- time: the question's time frame matches the snapshot (handled separately by the time-sensitivity rule, S22);
- closed-world senses: every reading of m that a reader could intend has a page in the snapshot (an entity missing from the wiki
  cannot make m ambiguous);
- mention extraction: the extracted m is the question's subject. When no mention is found the output is Verified by default; this
  is the main heuristic hole and is reported as such.

## 4. Accounting for L2 (proposed; to be fixed before any confirmatory test)
- **Completion** (counts toward coverage): Verified or Qualified outputs that are correct for the intended reading (graded
  correct against gold, or "gold wrong / both acceptable" under adjudication).
- **Silent error**: a Verified output that is wrong, or a Qualified output whose conditional claim is false ("assuming E, A"
  wrong for E). A Qualified output that is true for its stated E but E is not the intended reading is an **explicit miss**:
  neither completion nor silent error. This follows target.txt Goal A: a stated condition is not a silent claim.
- Guard against gaming: Qualified outputs are reported separately and their share is capped in the protocol (proposal: if more
  than half of releases are Qualified, L2 is reported on Verified alone as well).
- Conditional truth needs a judge: grader 6.1 with the stated sense appended to the question ("Who was the director of Shaft
  (1971 film)?"), or the blind web adjudicator; validated on DEV first.

## 5. Results
Tables: results/runs/l3/qualified_dev*.md (per state), results/runs/l3/accounting.md (all variants). Completion = graded-correct
Verified + Qualified; silent errors as a range: low counts every graded-wrong Qualified output as an explicit miss, high counts it
as an error (conditional truth is not judged yet).

**Design sets (DEV and earlier-used sets):**
| set | n | variant | Verified (wrong) | Qualified (wrong) | Unresolved (correct lost) | completion | silent errors |
|---|---|---|---|---|---|---|---|
| popqa_dev | 300 | strict | 40 (3) | 17 (3) | 2 (2) | 0.170 | 3-6 |
| mintaka_dev | 200 | strict | 37 (1) | 31 (1) | 3 (3) | 0.330 | 1-2 |
| SimpleQA dev | 300 | strict | 118 (0) | 10 (0) | 10 (9) | 0.427 | 0 |
| SimpleQA fresh | 200 | strict | 78 (2) | 5 (0) | 0 | 0.405 | 2 |
| SimpleQA dev | 300 | mid / lenient | 127 / 128 (1) | 10 (0) | 1 / 0 | 0.453 / 0.457 | 1 |
On every design set, the Verified errors that remain are not entity errors (gold incomplete, both acceptable, co-producers,
relation reading); every entity-ambiguity error left Verified (PopQA DEV: Dobra, Jordan, Legion became Qualified). Qualified
senses matched the intended PopQA page in 10 of 17 cases; where they did not, the stated condition was true for the stated sense
in 2 of 3 graded-wrong cases (Dobra (Kupa) is in Croatia; Legion (TV series) is superhero fiction) and false in 1 (Amman is not
"what Jordan is the capital of": a relation-reading error).

**Out-of-sample check on the unsealed S19/S21 test sets (v1 hashed 16:21 before scoring; descriptive).** Limits: the rule was
designed after this session had read the S21 PopQA test errors, and the mid variant was added after seeing v1's test output, so
these numbers are not a confirmatory test.
| set | n | variant | Verified (wrong) | Qualified (wrong) | Unresolved (correct lost) | completion | silent errors |
|---|---|---|---|---|---|---|---|
| FRESH-5 | 1526 | strict | 494 (4) | 43 (0) | 31 (31) | 0.349 | 4 |
| FRESH-5 | 1526 | mid | 523 (4) | 43 (0) | 2 (2) | 0.368 | 4 |
| FRESH-5 | 1526 | lenient | 525 (4) | 43 (0) | 0 | 0.370 | 4 |
| Mintaka | 2000 | strict | 310 (14) | 235 (10) | 75 (71) | 0.261 | 14-24 |
| Mintaka | 2000 | mid | 370 (18) | 235 (10) | 15 (15) | 0.288 | 18-28 |
| Mintaka | 2000 | lenient | 385 (18) | 235 (10) | 0 | 0.296 | 18-28 |
| PopQA | 2100 | strict | 307 (8) | 86 (6) | 8 (5) | 0.180 | 8-14 |
| PopQA | 2100 | mid | 311 (10) | 86 (6) | 4 (3) | 0.181 | 10-16 |
| PopQA | 2100 | lenient | 315 (11) | 86 (6) | 0 | 0.183 | 11-17 |
- PopQA: all 8 ambiguous-subject errors of S21 leave Verified under strict (Turin, Lear, Fin Unresolved; Shaft, Barabbas, Exposed,
  Lima Qualified with the sense named, e.g. "Shaft (1971 film)": Gordon Parks, true for that film). The 8 Verified errors left are
  occupations, genres, a birth town, co-authors and producers: none is an entity error. mid and lenient let Lear and Fin (and,
  lenient, Turin) back into Verified.
- FRESH-5: the 4 S19 errors stay Verified (none is an entity error). Strict costs 31 correct answers (2%) and would put completion
  at 0.349, just under the 35% floor; mid and lenient cost 2 and 0.
- Mintaka: 38% of releases become Qualified, mostly primary-topic statements ("Texas", "Spain"); strict loses 71 correct answers.
- The DEV estimate of strict's cost on SimpleQA (9 of 138 releases, 6.5%) anticipated the FRESH-5 cost (31 of 568, 5.5%).

**Decision.** The L3 design uses **strict**: it is the only variant whose entity-slot statement needs no extra assumption.
mid and lenient release an ambiguous mention as Verified when none of its senses holds the answer, which adds an unproven step
(the link between the mention and the release page). Strict's cost comes almost entirely from mention extraction: in most
"answer on no sense page" cases the extracted mention is a modifier ("American", "Gold Medal", "USA") rather than the subject.
Next DEV work therefore targets mention extraction, not the rule: (a) skip demonyms and generic modifiers as subjects; (b) prefer
the mention nearest to the relation word; (c) let the release page's lead sentence vote for the subject. Target: strict's lost
correct answers on SimpleQA DEV below 2% with no entity error back in Verified on PopQA DEV.
Still to build before any confirmatory use: the conditional-truth judge for Qualified outputs (grader 6.1 with the stated sense
appended to the question), validated on DEV.

## 6. Goal B: what to attack next
Goal B asks to remove the mechanism, not to add checkers. Evidence so far (REPORT.md 3.5-3.6): the 4B's hidden state predicts
whether a passage holds the answer (AUROC 0.89 on retrieved Wikipedia), but gating on it adds little over the prompt's own
abstention; LoRA-trained abstention mostly abstains more. In S19-S21 the residual errors are not the reader inventing answers
but the reader silently choosing an entity, relation or time frame. That suggests a concrete mechanism to target:
**silent resolution**. The model resolves "Lima" to one referent without representing that a choice was made.
Proposal (two steps, both DEV first):
1. *Expose the choice (prompt only, no training).* Ask the 4B for {"entity": <page title it relied on>, "answer": ...}. Measure
   on DEV how often the stated entity equals the sense chosen by qualified.py and, on PopQA, the intended page (meta.s_wiki_title).
   If the model's own entity statement is accurate, the external sense lookup becomes a check of the model's claim rather than a
   reconstruction of it.
2. *Distill the check into the model (LoRA on Qwen3-4B).* Training targets come from the pipeline itself, no gold: Verified
   outputs as "answer", Qualified outputs as "answer, assuming E", Unresolved as "ambiguous: E1 / E2 ...". Test whether the
   trained reader, without the gate, produces fewer silent entity errors at equal coverage than the base reader on held-out
   ambiguous questions (PopQA terciles, unseen subjects). Success criterion to pre-register: silent entity errors halved at equal
   coverage against the base reader with the same prompt; failure is equally informative (the mechanism is not learnable at 4B).
Cost: step 1 needs one 4B generation pass on DEV (about 15 min GPU); step 2 a LoRA run of about 1-2 h on the 5090 plus
evaluation. Both must queue behind S22 on the GPU lock.

## 7. v3: mention extraction (DEV-designed; hashes results/runs/l3/qualified_v3_hashes.txt)
Changes (rule unchanged): (a) demonyms and country codes ("American", "USA") and two-character tokens ("3D") are never the
subject (explicit list; a first attempt with a suffix pattern also skipped "Jordan" and "Salaryman" and was replaced);
(b) a capitalised stop-word may end a name ("Carry On"); (c) if a full name of two or more words in the question appears in the
release page's first 400 characters and has at most one sense, the output is Verified (the page states that it is about the
named subject).
| set | variant | Verified (wrong) | Qualified (wrong) | Unresolved (correct lost) | completion | silent errors |
|---|---|---|---|---|---|---|
| popqa_dev | strict v3 | 41 (3) | 17 (3) | 1 (1) | 0.173 | 3-6 |
| mintaka_dev | strict v3 | 41 (1) | 27 (1) | 3 (3) | 0.330 | 1-2 |
| SimpleQA dev | strict v3 | 122 (1) | 10 (0) | 6 (6) | 0.437 | 1 |
| SimpleQA fresh | strict v3 | 78 (2) | 5 (0) | 0 | 0.405 | 2 |
No entity error returned to Verified on DEV (the one new SimpleQA dev Verified error, "first major American party with a keynote
speech by ...", is a reading error). Lost correct answers on SimpleQA dev: 9 -> 6 of 138 (4.3%; the 2% target is not reached;
the rest would need the unproven "page names the mention" step).
Unsealed test sets, run once after hashing v3 (descriptive, same limits as above):
| set | strict v3 completion | silent errors | correct lost | vs v1 strict |
|---|---|---|---|---|
| FRESH-5 | 540 (0.354) | 4 | 24 | completion 0.349 -> 0.354, back above the 35% floor; k = 4 unchanged |
| Mintaka | 529 (0.265) | 15-24 | 63 | 71 -> 63 lost |
| PopQA | 379 (0.180) | 8-14 | 5 | unchanged; all 8 entity errors still out of Verified |
Reading: with the entity slot made explicit (strict v3), the S19 FRESH-5 result would still meet L2 (completion 35.4%, k = 4)
while every Verified answer now also carries the entity-slot guarantee of section 3. This is a post hoc reading of an unsealed
set, not a new test.

## 8. Next
1. Conditional-truth judge for Qualified outputs (grader 6.1 with the stated sense in the question), validated on DEV labels read
   by hand; needed before Qualified outputs can count in a confirmatory L2 test.
2. A confirmatory test of the extended statement needs a fresh sealed set; coordinate with S22 (which uses the last 1800 Mintaka
   generic items) rather than competing for it: the Qualified layer is a post-processing step on S22's outputs, so it can be
   pre-registered as a secondary endpoint of S22 at no GPU cost.
3. Goal B step 1 (section 6) when the GPU is free.

## 9. v4 and the conditional-truth judge (DEV)
**Qualifier errors found while hand-labelling.** In 9 of 59 DEV Qualified outputs the answer was right for the intended reading
but the stated sense was wrong (the release page was an adaptation: "Pride and Prejudice (musical)", "Neuromancer (TV
series)", "Percy Jackson (film series)"; a non-place comma title "Spain, take this cup from me"; "Ph.D." taken as the subject).
**v4** (hashes qualified_v4_hashes.txt): comma senses only with place-style qualifiers (up to three capitalised words); degree,
title and league abbreviations are never the subject; for authorship questions adaptation senses (film, TV, musical, album,
game ...) are not named. Result: 7 of the 9 cases now name the right sense (primary topic). DEV strict v4: SimpleQA dev lost
correct 5/138 (3.6%), Mintaka DEV 2, PopQA DEV 1; Verified errors unchanged and none is an entity error.
**Accounting refinement.** A Qualified output graded correct against gold counts as completion and not as an error; a wrong
stated sense there is a *qualifier error*, reported separately. The conditional-truth judge is needed only for Qualified outputs
graded wrong against gold: it separates explicit misses (true for the stated sense) from silent errors.
**Judge** (results/runs/l3/cj_judge.py): qwen3.8-27b sees question, stated sense, an excerpt of that sense's page (lead + the
sentences holding the answer) and the answer; letters A supported / B not supported / C unclear. Validation set: the 59 DEV
Qualified outputs (built with v3 senses), hand-labelled by this session (conditional truth: 48 true, 10 false, 1 unclear), plus
58 easy negatives (another item's answer) and 58 hard negatives (another name or number from the same sentence; one of them,
"The Snake", is a gold alias and was relabelled true). Bars set before the run: false credit at most 1% (easy) and 5% (hard);
on system items at most 1 in 10 hand-false items supported and at most 1 in 10 hand-true items not supported.

**Judge result (results/runs/l3/cj_eval.md): FAIL against the pre-set bars.**
| check | result | bar | |
|---|---|---|---|
| easy negatives supported | 0/59 | ≤ 1% | pass |
| hard negatives supported | 1/57 (1.8%); the one ("Taylor" for the musical) may be a labelling error | ≤ 5% | pass |
| hand-false system items supported | 4/10 | ≤ 1 in 10 | **fail** |
| hand-true system items not supported | 1 B + 5 C = 6/48 (12.5%) | ≤ 1 in 10 | **fail** (1/48 if "unclear" is excluded) |
Failure pattern: the judge accepts an original work's author for an adaptation sense (Percy Jackson film series, The Scarlet
Letter miniseries, Jamaat-e-Islami Kashmir) and accepted "Amman" for "What is Jordan the capital of?" with E = Jordan, a relation
reading error, i.e. the dangerous direction (it would turn a silent error into an explicit miss).
Decision: the prompt is not tuned on these failures and re-validated on the same labels (that would fit the validation set).
**Accounting uses the conservative end until a validated judge exists: every Qualified output graded wrong against gold counts
as a silent error** (the "high" end of the ranges above). The blind web adjudicator of S22 (docs/S22_ADJUDICATION_DRAFT.md) can
judge conditional truth with sources and is the route for a confirmatory test; a v2 judge would need fresh hand labels it was not
designed on.
Conservative silent-error counts, strict v4 on DEV: popqa_dev 6, mintaka_dev 2, SimpleQA dev 1, fresh 2.

## 10. Judge v2 (extraction) on an independent held-out set: FAIL, conservative accounting stays

**Design** (results/runs/l3/cj_judge2.py): the 27B is not asked to grade. It answers the question itself, told to assume the
question is about E and to use only the excerpt (shortest exact answer or NONE; 40 tokens, temperature 0, no thinking). The
system answer is SUPPORTED iff vkg agree(answer, reading); NONE gives UNCLEAR. **Held-out set** (cj_items_heldout.jsonl, seed 41,
193 items): all 13 gold-wrong system Qualified outputs on the unsealed tests, 60 sampled gold-correct ones, 60 hard and 60 easy
negatives, hand-labelled before the judge ran (hashes in heldout_hashes_before_judge.txt, 20:03; judge ran 21:57-22:00). Same bars
as v1.

| check | DEV (designed on) | held-out | bar | held-out |
|---|---|---|---|---|
| easy negatives supported | 0/59 | 0/60 (95% upper 4.9%) | ≤ 1% | pass (point) |
| hard negatives supported | 0/57 | 1/59 (1.7%, upper 7.8%) | ≤ 5% | pass (point) |
| hand-false system items supported | 6/10 | **3/9** | ≤ 1 in 10 | **fail** |
| hand-true system items not supported | 4/48 (all UNCLEAR) | 5/64 (1 NOT, 4 UNCLEAR) | ≤ 1 in 10 | pass |

The three held-out false-but-supported items are all wrong-type senses: "Mrs. Robinson in The Graduate" with E = The Graduate
(novel), "main character of The Scarlet Letter" with E = Scarlet (color), "Mark Twain's real name" with E = Mark Twain (book).
The excerpt mentions the answer (an adaptation, a cultural reference), so extraction finds it. v2 removes the yes/no
over-acceptance on easy and hard negatives, but the dangerous failure is unchanged: an excerpt-based judge cannot tell "the answer
appears on E's page" from "the answer is true of E". That is a type question (does E have an actor / a main character / a real
name?), not a reading question.

**Decision.** No judge is validated. For L2 every Qualified output graded wrong against gold counts as a silent error (section 9).
The held-out set is now spent for judge design: any v3 (for example a type-compatibility check between the relation and E's
category) needs new labels. Conditional truth for a confirmatory test goes to the blind web adjudicator.
What this means for the claim: the Qualified layer still pays off under the conservative rule, because it moves entity errors out
of Verified and keeps the Qualified error rate visible; it does not by itself lower the conservative silent-error count.

## 11. Goal B step 1: the 4B states the entity it used (DEV only; written before the generation ran)
Context: S22 will not be run (docs/S22_DEV_FINDINGS.md); the Qualified layer is a post hoc analysis on the frozen S19 releases
(docs/L3_S22_SECONDARY_ENDPOINT_DRAFT.md withdrawn). The S22 session takes the derivation-certificate part (results/runs/l3cert/).
**Experiment** (results/runs/l3/ent_gen.py, launcher run_ent.sh, GPU lock with check-after-write): on every frozen S19 H1 release of
the four DEV sets, the same combo passage and question, new prompt: name the specific thing the question is about (with a short
qualifier when several things share the name), then answer. Raw generations kept in ent_raw.jsonl. Nothing from the sealed or used test
sets is generated.
**Questions and bars, fixed before looking at the output** (ent_eval.py, DEV):
1. Does the stated entity agree with the intended sense where it is known (PopQA DEV, meta.s_wiki_title)? Bar: at least as many
   correct senses as the rule-based Qualified sense (which is right on 15/17 stated senses there).
2. Does the answer the 4B gives with the entity agree with the frozen release (not a new error source)? Report only.
3. Can the stated entity turn Unresolved into Qualified/Verified without admitting an entity error: of the Unresolved-correct items
   on DEV (8 in total), how many does the entity resolve to a sense that holds the answer; and does any gold-wrong entity-error item
   (the 8 PopQA S21 entity errors are test data and are NOT used; DEV has none in Verified) get through. Bar: no new wrong sense in
   Verified; every recovered item must be graded correct.
Decision rule: if (1) and (3) pass, the entity check goes into the gate as an additional input to the entity slot (stated entity must
match the release page sense, otherwise Qualified/Unresolved); otherwise the rule-based layer stays.

### 11.1 Result (results/runs/l3/ent_eval.md): FAIL as specified, a prompt-following failure
| check | result | bar |
|---|---|---|
| Q1: 4B stated entity matches the intended PopQA sense | 18/59 | at least the rule-based layer (Qualified senses right 10/17; Verified pages with the right core 27) | **fail** |
| Q3: Unresolved items recovered | the 3 that "resolve" are spurious | no wrong sense admitted | **fail** |
The 23 mismatches I read: in about half the 4B writes the *answer* or the relation word as the "entity" (Wong Jing, Jon Cleary,
Amsterdam, ice hockey, "occupation", "director of Forget Paris", Constantinople for "capital of Byzantine Empire"); the rest are expanded
names ("Gaziza Akhmetkyzy Zhubanova") or a guessed qualifier ("Dobra River (Croatia)"). The free-text request "name the thing the
question is about" is not followed by a 4B reliably, and a stated entity that is really the answer would make the gate accept an
answer on its own page. 4B answer agreement with the release is 328/351 (93%), so the answers themselves are not the problem.
Decision: free-text entity is dropped. Next variant (DEV, written before running): closed-choice. Show the 4B the question and the
candidate senses of the question's mention (titles with one-line leads, from the same inventory the rule layer uses) plus "none /
cannot tell", and ask which sense the question means; the gate then requires the chosen sense to be the sense holding the release
(or to hold the answer). Bars: choice equals the intended PopQA sense in at least as many items as the rule-based layer; no
chosen sense that disagrees with the rule layer's Verified items without the rule layer being wrong.

### 11.2 Closed-choice variant (results/runs/l3/ent2_eval.md; DEV, 75 releases whose mention has 2+ senses)
| check | result | bar |
|---|---|---|
| pick = intended sense, PopQA DEV (20 asked) | 12 vs rule 10 (pick right where rule wrong 3, rule right where pick wrong 1) | at least the rule | pass, n = 20, not significant |
| Verified releases where the pick disagrees with the rule's page | 4, all graded correct | none without the rule being wrong | **fail** (4 correct answers would be downgraded) |
| graded-wrong releases caught | 0 of 3 (the 4B agrees with the rule on Dobra River, Jordan, Legion) | informative | none |
| pick invalid / "none" | 10 of 75 (mintaka 3, dev 5, fresh 2) | | |
Reading: choosing among candidate senses is far more reliable than free-text entities (the 4B follows a closed task), but on this
data it adds no error detection and costs 4 correct answers, so it does not enter the gate. The only possible use is as a better
labeller of the stated sense in Qualified outputs (+3 / -1 on PopQA DEV, too few to claim). **Goal B step 1 is closed on DEV: the
rule-based entity slot stays; the 4B cannot yet be trusted to state or check its own entity.** The mechanism "silent resolution" is
therefore handled outside the model (output states), not trained out of it; the LoRA idea in section 6 has no DEV evidence behind it.

## 12. v5: recovering correct answers that v4 left Unresolved (DEV-designed; tests post hoc)
Hash: results/runs/l3/qualified_v5_hashes.txt (qualified_v5.py; v4 untouched). Two additions, both only for what v4 left Unresolved:
**R1** when 2+ sense pages hold the answer, and a word (length > 3) of exactly one of those senses' qualifiers occurs in the question
("first Yakuza *game*" -> Yakuza (video game)): Qualified on that sense. **R2** when no sense page holds the answer, the answer is the
release page's own subject, and that page names the mention ("second YouTube video" -> My Snowboarding Skillz): Qualified with
E = the mention's primary topic. Neither rule creates a Verified output.
DEV (designed on these, in-sample): 4 of the 8 Unresolved-correct items recovered (mintaka 1, SimpleQA 3); Verified and Qualified
error counts unchanged (results/runs/l3/v5_dev.log). The other 4 stay Unresolved: Mendoza's capital (6 sense pages hold "Mendoza",
a true ambiguity), Bayonetta clan, Makhdum Khusro Bakhtyar (mention "National Assembly", 59 senses) and Scott Wilson / MOBA (14).
Used test sets, **post hoc, no further tuning** (v5_tests.log): FRESH-5 +2, Mintaka +3, PopQA +0 recovered, all graded correct;
Verified unchanged everywhere; Qualified errors unchanged (0 / 7 / 6). In total 9 correct answers are back (4 DEV, 5 used tests), with no new error.
The gain is small: the bulk of the Unresolved loss on
Mintaka (54 correct) is true multi-sense ambiguity where the answer sits on several senses, and recovering it would need
information the question does not contain.
