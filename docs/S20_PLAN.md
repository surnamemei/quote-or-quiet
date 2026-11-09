# S20 plan (DRAFT 2026-11-07 ~14:15; nothing run, nothing frozen): build D3 (frame match) and test C1/C2/C4

Direction chosen by me under the user's delegation ("you decide the direction, I trust you"). Basis: docs/THEORY_CONJECTURES.md,
section 6. The target theorem T* is missing two deductive components, D3 (frame match) and D4 (conflict → Qualified), and one assumption,
A_M (semantic mapping), has to be stated and measured. D3 comes first because it targets A2, the dominant error term.
No sealed data is used: development on DEV only, exploratory checks on used sets, the decisive test on synthetic pages whose truth is
known by construction.

## 1. Components
**Relation inventory R (closed, hand-written, auditable).** About 30–40 relations that cover SimpleQA question forms, each with
question triggers and sentence triggers. Neighbouring relations are listed explicitly as **competitors**:
launched vs announced/unveiled/ordered; founded vs relocated/incorporated/renamed; invented vs worked at/patented;
goals scored vs final score; appointed (position P) vs appointed (other position); born vs baptised; died vs buried; etc.

**Question parser M_Q (fail-closed).** Deterministic grammar: φ(x) = (entity e, relation r, qualifiers q, type τ). It outputs a frame only if
exactly one relation's question trigger matches; otherwise it outputs nothing, and the item stays on the current path or becomes Unresolved.

**Sentence reader M_S (fail-closed).** For the sentence containing the released span: find relation triggers in the same sentence.
Accept r' = r only if a trigger of r is present **and no competitor trigger is nearer to the span** than it.
Entity: the page is about e (title match) or e is named in the sentence. Qualifiers: every year/position/event in q appears in the
sentence or in its section heading.

**D3 check.** Release under the L3 gate only if M_Q gives φ(x), M_S gives φ(σ), and they match. Plain code, deterministic, tested
like vkg/l3_verify (unit tests plus adversarial records).

A_M is then the only new assumption. ε_M is the rate at which M_Q or M_S outputs a confident but wrong frame, measured by hand-auditing
a random sample of frames. A frame is one line, so auditing is cheap.

## 2. Step A: development and exploratory checks (DEV only for building; post hoc elsewhere)
- Build R, M_Q, M_S and D3 looking at DEV only.
- Report on DEV, FRESH and the S18 sets (all used, so post hoc, deciding nothing):
  - parser coverage (share of questions with a frame);
  - G3 + D3: coverage, graded-wrong, correct releases blocked;
  - C1(a): in how many of the 15 S18 A2 errors does the asked entity occur in the span's sentence;
  - C1(b): AUROC of the predicate check vs the entity-overlap check (V6) on the same releases;
  - C2(c): share of G3 errors on DuckDuckGo evidence where all three sources quote the same sentence.

## 3. Step B: synthetic-page test (decisive; pre-registered before any page is generated)
**Items.** DEV questions where the frozen pipeline released a correct answer from a FineWiki page (truth known: gold, page and
sentence agree). Only DEV is used, so no new data is spent.
**Pages.** For each item, copies of the source page with k ∈ {0, 1, 2, 4} inserted sentences near the true sentence:
- *relation distractors*: same entity, a competitor relation, a fresh type-compatible value ≠ gold ("… was announced on 3 May 1987");
- *entity distractors*: another entity, the same relation, a fresh value.
Sentences come from code templates, with several paraphrase templates per competitor pair, and are not LLM-written, so every
inserted value and its relation are known exactly. Synthetic pages go into a separate corpus D' with their own hashes, so V1 still applies.
**Systems.** 4B cautious reader and Phi-4 cautious reader on wiki evidence from D'; gate V1–V5; G-style agreement; D3.
**Outcome per page.** Release = gold (correct) / release = an inserted value (A2 error by construction) / other / abstain.
**Pre-registered predictions** (priors to be fixed in the frozen version):
- **P1 (C1):** the A2 error rate rises with k for relation distractors, at least twice as steeply as for entity distractors.
- **P2 (C2):** when the 4B releases a relation-distractor value, Phi-4 gives the same value in ≥ 50% of cases (a shared misreading).
- **P3 (C4/D3):** D3 blocks ≥ 80% of relation-distractor releases and keeps ≥ 90% of correct releases at k = 0.
- **P4 (A_M):** on a hand audit of 100 random frames from FRESH questions, confident wrong frames ≤ 2%.
Each can fail. If P3 fails, D3 as designed does not remove A2, and the proof plan needs a different D3.

## 4. After S20
- If D3 works: D4 (conflict → Qualified) with a structured second source (Wikidata statements with qualifiers). That also enforces
  the independence assumption I of section 6 by construction. Wikidata access is a download, so it needs the user's permission first.
- A new clean natural test set for L2 (FRESH-5 is the last SimpleQA pool): its own decision, later.
- Goal B: the synthetic pages double as training data (LoRA on the 4B) for relation-aware reading, with a mechanism probe
  (does the reader attend to the relation word when it misreads?).

## 5. Resources
CPU for Step A. Step B needs the 4B and Phi-4 for about 1–2 h on the local GPU, under the GPU lock rule shared with the Kimi
session, and only after S19 is generated.

## 6. Step A, first result: D3 v0 (2026-11-07 ~15:10; post hoc on used sets, decides nothing)
Table: results/runs/s20/d3_eval.md (script d3_eval.py, frames in frames.py).
| S18 (n = 2000) | coverage | graded-wrong |
|---|---|---|
| G3 V1-V5 + Phi-4 veto | 36.7% | 9 (0.45%) |
| + D3-soft (block only where a frame exists and fails) | 26.6% | 4 (0.20%) |
| + D3-strict (T* form: no frame -> Unresolved) | 11.1% | 1 (0.05%) |
DEV + FRESH: 3 errors -> 0 under either form.
- Safety behaves as the theory says: where D3 fires, errors almost vanish (1 of 221 releases under strict + veto).
- Yield does not: the cost is coverage. Of 743 correct S18 releases: no frame 377, sentence check fails 128, qualifier check fails 107.
  Reasons seen on DEV (where looking is allowed): the fact sits in a **table row** (relation in the column header), the trigger
  is in the **previous sentence**, **synonyms** are missing ("became President" for joined, "lay dying" for died), and
  ordinals like "first"/"original"/"last" describe the question's context, not a qualifier the answer must carry.
- Errors D3-strict still lets through: Turbo, "officially established as a municipality in 1847" vs gold 1840 (what "founded"
  means: A1/gold), and Joanna, "betrothed to Philip of Austria, in the Low Countries". The second is a new class,
  **argument-role mismatch**: the relation is right, but the span fills another slot (part of a name, not the place).
  The S18 "2" from a "2–2 draw" and "90 seconds" for rounds are the same class.
Theory update: the frame needs a **role** component. φ(σ) = (entity, relation, qualifiers, role of the span), and D3 must check that
the span fills the asked slot (for example not inside a larger name "X of <span>", not one side of a score "n–m").
D3 v1 (design on DEV only, to avoid fitting S18): table-aware reading (header = relation, row key = entity), one-sentence
look-back when the subject continues, a synonym list per relation, ordinal check only when the ordinal modifies the asked noun,
and a role check. The decisive test stays the synthetic-page experiment plus a new clean set, since S18 has now been looked at.

## 7. D3 v1 (2026-11-07 ~15:30; post hoc on used sets; tables: results/runs/s20/d3_eval_frames_v1.md)
| S18 (n = 2000) | v0 coverage / wrong | v1 coverage / wrong |
|---|---|---|
| G3 V1-V5 + D3-soft | 27.2% / 5 | **30.1% / 5** |
| G3 V1-V5 + D3-strict (T*) | 11.2% / 2 | **13.0% / 2** |
| + Phi-4 veto + D3-soft | 26.6% / 4 | 29.5% / 5 |
- **Under D3-strict, both remaining S18 errors are A_S (source/gold) cases**: Turbo ("established as a municipality in 1847" vs gold
  1840) and Hullot (page "June 17, 2019" vs gold June 19). The role check removed Joanna. This is what T* predicts: once D1-D5 hold,
  only the assumptions remain, and here only A_S does. It is post hoc on 2 errors, so it is a consistency check, not evidence.
- Soft-mode residuals are all questions **without a frame** (A2 or strict grading outside the inventory: Thierack "become Reich Minister",
  Trebek "shave"/"cut", Wani incomplete name, the DEV "first convention"). The relaxed ordinal rule let the DEV one through.
- Coverage is still below the 35% floor. Correct releases lost: no frame 377 (strict only), sentence check 95, qualifier check 67.
  Lexical triggers have a recall ceiling: the deterministic check is sound, but **M_S as a keyword reader rejects too much**.

### Next: D3 v2, a blind LLM sentence parser into the closed frame vocabulary
The structure of C4 (and Faithful CoT): keep the **check** deterministic and let a model do only the **translation** into frames.
- M_S v2: a reader model sees only the source sentence (plus the previous one) and the marked span. It does **not** see the question.
  It outputs, from the closed inventory, the relation the sentence states for the span and the span's role. Fail-closed: "none" or
  anything outside the vocabulary means no frame.
- M_Q stays the deterministic grammar, or a model call with the same closed output and no access to the evidence.
- D3 then compares the two frames in code. The verifier never sees question and answer together, so it cannot simply agree with the
  reader's reading. That is a different failure structure from the yes/no entailment check that failed E1/E2, and from a second reader (C2).
- A_M is then the parser's error rate on frames. It is countable by hand audit, since each frame is one line.
- Prediction to pre-register: M_S v2 recovers most of the 95 + 67 lexical rejects while blocking the same relation and role mismatches.

## 8. D3 v2 built (2026-11-07 ~17:45), predictions written before any parse is run
Code: results/runs/s20/parse_v2.py. Phi-4 (Ollama, greedy, JSON output) as two blind parsers into a closed vocabulary of 56
relations: the 42 lexical families plus 14 general ones (located_in, named_after, position_held, score, count, creator, owner,
parent, member_of, amount, duration, event_date, ...). M_Q sees only the question; M_S sees only the page title and the span's
sentence (plus the previous one) or table row and header, with the span marked, never the question. Code compares them.
Cases: every G3 V1-V5 release on DEV (141), FRESH (84), S18 (758), FRESH-5 (589); all used sets, so all of this is post hoc.
Written before running (so it can fail visibly, even though nothing here is confirmatory):
- Q1: v2-soft + veto keeps coverage ≥ 35% on S18 and on FRESH-5 (v1-soft: 29.5% / 29.9%).
- Q2: v2-soft + veto has no more graded-wrong releases than v1-soft + veto (S18 5, FRESH-5 3).
- Q3: v2-strict covers more than v1-strict (S18 13.0%, FRESH-5 11.7%) and its residual errors stay A_S / gold-type cases.
If Q1 fails, a blind closed-vocabulary parser cannot carry the coverage, and D3 stays a strict, low-coverage mode (Qualified output).

## 9. D3 v2 result (2026-11-07 ~18:10; post hoc; table results/runs/s20/d3_v2_eval.md, errors d3_v2_errors.json)
| + Phi-4 veto | S18 coverage / wrong | FRESH-5 coverage / wrong |
|---|---|---|
| G3 V1-V5 (no D3) | 36.7% / 9 | 37.2% / 4 |
| v1-soft (lexical) | 29.5% / 5 | 29.9% / 3 |
| v2-soft (blind LLM parsers) | 20.2% / 3 | 20.8% / 2 |
| v1-strict | 13.0% / 2 | 11.7% / 1 |
| v2-strict | 17.2% / 3 | 18.0% / 1 |
- **Q1 fails** (v2-soft coverage about 20%, below v1 and far below 35%). **Q2 holds** (3 ≤ 5, 2 ≤ 3). **Q3 partly**: v2-strict covers
  more than v1-strict, and 4 of its 5 residual errors (all sets, with veto) are A_S / gold (Turbo, Hullot, Zonfrillo, a 1-second time
  difference), but one is an **entity** mismatch: Yoido church membership read from another church's table row (the frame has no
  entity slot). So Q3 fails as written.
- Why coverage falls: of 743 correct S18 releases, 256 have a relation **mismatch** and 118 a role that is not "whole". The top
  mismatch pairs are announced/event_date, released/announced, released/event_date, appointed/elected, position_held/appointed.
  These are exactly the competitor pairs D3 is meant to separate. A blind labeller blurs the distinctions that matter most.
- **Theory consequence (sharpens C4).** The semantic mapping has a granularity/reliability trade-off: a vocabulary fine enough to
  separate competitor relations is one an automatic parser cannot apply consistently on both sides, and a coarse one does not
  remove A2. Soundness of the check is not the bottleneck; the reliability of M at the needed granularity is (ε_M rises, or coverage
  falls). The frame also needs an entity slot (Yoido), as T*'s φ = (entity, relation, qualifiers, role) already says.
- **Decision (rule written in section 8):** D3 does not carry L2 coverage. It becomes the **Verified** tier of Goal A's three output
  states: Verified = D3-strict releases (about 12-18% coverage; residual errors so far only A_S / gold plus one entity case),
  Qualified = other gated releases, shown with their quoted source sentence, Unresolved = abstain. Silent false claims then only come
  from the Verified tier, whose observed errors are source disagreements; that is the T* corollary in practice.
- Next: (1) add the entity slot (page subject or row key must be the question's entity) to D3-strict; (2) the synthetic-page test
  (Step B) to measure C1/C2 by construction, since the natural sets are used up; (3) D4 with a structured second source (Wikidata
  needs the user's download permission) to turn A_S cases like Zonfrillo/Hullot into Qualified ("sources disagree").

## 10. Step B result (2026-11-07 ~18:30; pre-registered in docs/S20_STEPB_PREREG.md, hashes checked OK after the run)
Table: results/runs/s20/synth_result.md (220 items x 7 conditions; 4B plain/cautious, Phi-4 cautious; V1-V5 gate on the page).
- **The readers almost never release an inserted value.** Across 1320 distractor pages per reader: 4B plain 6, 4B cautious 0,
  Phi-4 cautious 2 (all on entity distractors). Distractors cost **coverage, not safety**: abstention rises from 10.0% to up to
  17.7% (4B cautious) and from 14.5% to up to 25.0% (Phi-4), most for relation distractors.
- By the pre-registered rules: **P1 fails** (no rise at all for either kind), **P2 fails** (0/0, undefined), **P3 fails** (0/0
  relation-distractor releases to block; v1-soft keeps 162/183 = 88.5% of correct releases, below 90%), P5 holds trivially (0/0).
  The test did not produce the error it was built to study. That is a floor effect of the manipulation, and I report it as a
  failure of the test design as well as of the predictions.
- **What it does say (C1 refined).** Explicit neighbouring-relation sentences ("X was baptised in 1851") do not fool either
  reader, cautious or plain. So the natural A2 errors are not "a competitor relation is nearby". They come from **implicit or
  underspecified wording** ("officially established as a municipality in 1847" for founded), table/infobox structure, temporal
  cut-offs ("as of 2022"), and source/gold disagreement. That matches the S18 / FRESH-5 error list: 0 of the 4 FRESH-5 errors
  and few S18 errors involve an explicit competitor sentence. C1 in its simple form ("A2 = relation confusion with a nearby
  explicit competitor") is not supported. C2's shared-misreading part could not be tested, because nothing was misread.
- Consequence for the plan: synthetic templated distractors are not a useful training or test signal for Goal B in this form.
  The residual error is dominated by meaning-level ambiguity and A_S, which is where D4 (a second structured source) and the
  Qualified tier act. A better synthetic test would have to paraphrase real error cases (implicit relations, cut-offs), which needs
  an LLM writer and its own validation.
