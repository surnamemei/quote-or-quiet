# Theory status and open conjectures (2026-11-07, written while S19 runs; FRESH-5 not touched)

Purpose: state what is proven, what prior work already has, and which conjectures remain, each with a prediction that can fail,
**before** any further experiment is designed. This answers the user's instruction (2026-11-07): first make the theoretical
conjectures clear, then verify them. Numbers marked "post hoc" come from sets that are already used (DEV, FRESH, S18).

## 1. Prior art for the L3 certificate (searched 2026-11-07; abstract-level, full texts not read)
The core construction (release only a verbatim span of a source, checked by plain code) is **not new**:

| work | what it has | what it says about the limit |
|---|---|---|
| Menick et al., GopherCite, arXiv 2203.11147 (2022) | answers with verbatim quotes from retrieved documents, constrained to exact quotes; abstention | "not all claims supported by evidence are true" (TruthfulQA analysis) |
| Rashkin et al., AIS, arXiv 2112.12870, Computational Linguistics 2023 | the attribution concept: output verified against an identified source | attribution is a different property from truth |
| Lyu et al., Faithful CoT, arXiv 2301.13379 (IJCNLP 2023) | answer = deterministic execution of a generated program (our "P(σ)") | the guarantee covers execution only; the translation step is unverified |
| Murdock et al., Watson TyCor, IBM J. R&D 2012; Welty et al. ISWC 2012 | answer-type checking against the question's answer type (our V3) | used as soft evidence; reported to beat hard type filters on Jeopardy! |
| Signé et al., CHyD, arXiv 2609.10046 (Sep 2026) | constrained decoding: quoted spans appear verbatim in the context | covers quoted spans only; no claim about relevance or correctness |
| Recski et al., ACL-Verbatim, arXiv 2605.21102 (May 2026) | extractive QA returning verbatim spans ("hallucination-free") | best span selection only 53.6 word-F1: choosing the right span is far from solved |
| Zhang et al., "Verifiable by Construction", arXiv 2609.15964 (Sep 2026) | 12 LLMs attach verbatim guideline quotes to claims | one frontier model quotes 98.0% of claims but the quotes fully support only 37.1% |
| "Selective Extraction", IEEE (ieeexplore 11700668) | LLM proposes spans, character-level verifier keeps exact ones | **not verified**: the page returned HTTP 418; known only from a search summary |

Verdict:
- Verbatim grounding, deterministic checking, answer typing and program execution are all prior art. Our L3 theorem is
  an instance of a known pattern and must be cited as such.
- Every one of these works names the same gap: **provenance is not relevance**. That gap is exactly our A2 (and R in docs/THEORY.md T4).
  2609.15964 is an independent measurement of how large it is for frontier models at claim level.
- Possibly ours (not claimable as novel until full texts are read): the combination of a hash-pinned corpus, period
  consistency (V4), the explicit union bound over named assumptions with each ε measured under a sealed protocol, and a
  finite-sample L2 test on top. No search hit combined a deductive release condition with a sealed statistical test.

## 2. What is proven (unchanged)
- **T1** (textbook): any gate is a point under Y*(ε) = π·ROC(ε/(1−π)); yield → 0 as ε → 0 for a fixed signal.
- **T4 / L3**: a release is a verbatim, typed, period-consistent span of a hash-pinned page; fabrication = 0 by construction;
  P(false release) ≤ ε_A1 + ε_A2 + ε_A3.
- **T5**: about 3/n is the best demonstrable rate with 0 errors in n.

## 3. Conjectures (each with a prediction that can fail)

### C1. A2 errors are relation/qualifier mismatches, not entity mismatches
Statement: given a release that passed V1–V5, the span almost always sits in a sentence about the **asked entity**; the error
is that the sentence states a different relation or qualifier of it (announcement vs launch, employment vs invention,
a match score vs goals scored, another appointment of the same person).
Why it matters: it explains why lexical-overlap checks (V6) separate badly. Entity words overlap in errors as much as in
correct releases, so overlap cannot see the mismatch, which lives in the predicate.
Predictions:
- (a) In the post hoc S18 A2 errors, the asked entity occurs in the span's sentence in most cases (≥ 10 of 15).
- (b) A check on the predicate (does the span's sentence contain the question's relation word or a synonym) separates errors from
  correct releases better than entity overlap does (higher AUROC on the same releases).
Falsified if: most A2 errors come from sentences about a different entity, or the predicate check is no better than V6.

### C2. Error = evidence-induced part + reader-specific part; agreement only removes the second
Statement: for a fixed evidence passage, the chance that a reader misreads it splits into a part common to all competent readers
(the passage states a nearby fact in the answer slot) and a reader-specific part. Requiring K readers to agree multiplies the
reader-specific part by roughly q^(K−1) but leaves the evidence-induced part unchanged.
Post hoc support: S18 V1–V5 G3 errors went 15 → 9 with the Phi-4 veto, and only 9 → 8 with Mistral added; Gemma barely helped.
- Implied veto signal quality (binormal, from 6 of 15 errors and 17 of 743 correct removed): **d′ = 1.74, AUROC ≈ 0.89**,
  inside the 0.64–0.94 range of every signal in T2.
- With that signal used as a graded score instead of a yes/no veto, T1 gives at most about 0.35% graded-wrong at the 35% floor
  (n = 2000, post hoc). A graded score alone is therefore at the edge of L2.
Predictions:
- (a) A third reader on the **same** evidence removes less than 20% of the remaining errors.
- (b) A reader that sees **different** evidence (a document not textually derived from the first) removes clearly more of the
  evidence-induced part, but only when the two texts are not near-duplicates.
- (c) With DuckDuckGo evidence, mostly Wikipedia and its mirrors, "3 sources agree" filters less than it did with Serper evidence:
  a larger share of G3 errors has all three sources quoting the same sentence.
Falsified if: a same-evidence reader removes a large share (≥ 40%) of the post-Phi-4 errors, or different evidence helps no more.

### C3. Under the gold-relative rule there is a floor no reader can remove
Statement: graded SER ≥ coverage × g_rel, where g_rel is the rate of wrong or over-strict gold among released items.
Post hoc: 4 of the 9 errors are gold or strict-grading disputes, about 0.2% of all items (g_rel ≈ 0.55% of releases).
Gold disputes are correct answers, so no veto removes them: the T1 calculation in C2 applies only to the misreadings.
Prediction for S19 (consistent with the frozen P2 ≈ 35%): the gold-relative endpoint fails unless misreadings fall below about
0.2%. The adjudicated endpoint can pass only if adjudication removes most disputes **and** misreadings stay at or under about 0.39%.
Falsified if: S19's graded-wrong releases contain no gold disputes at all (blind adjudication removes none).

### C4. A deductive check of R only moves the error into a semantic mapping (no free lunch)
Statement: R ("the span answers the question") is a relation between natural-language meanings. A decidable checker sees only
strings, so it can certify R only relative to a formal semantics M: a parser that maps question and sentence to typed frames
(entity, relation, qualifier, time). Then P(¬R ∧ release) ≤ P(M wrong on x or on the sentence). Faithful CoT has the same
structure: execution is verified, translation is not.
Consequence: an L3 statement about R is possible only with "reliable semantic mapping" as an explicit assumption. target.txt
already lists that assumption. The research question becomes whether M can be made **narrow and auditable** (a small set of frame
templates per question type, each checkable by hand) so that its error is measurable and small, rather than whether R can be proven outright.
Prediction: a template-frame checker, built on DEV only, rejects most of the C1-type errors (relation mismatch) while keeping
≥ 90% of correct releases. Its own error then shows up as template misses, which can be counted.
Falsified if: frame templates cover too few questions (coverage drops below the floor) or miss most relation mismatches.

## 4. How to test without spending sealed data
After S19, no untouched SimpleQA pool is left. Tests of C1–C4 therefore need data where the truth is known without a gold
dispute:
1. **Used sets, exploratory only** (DEV, FRESH, S18): C1(a), C1(b), C2(c). These are cheap, reported as post hoc, and decide nothing.
2. **Controlled synthetic pages** (truth known by construction): take a real page and insert k type-compatible distractor
   sentences that share the entity but change the relation or qualifier, for k = 0, 1, 2, 4. Each prediction can fail:
   - C1: P(¬R) rises with k for relation distractors and much less for entity distractors.
   - C2: agreement between readers does not fall as k rises, because the misreading is shared.
   - C4: the frame checker's rejection rate on relation distractors stays high.
   Pre-register the predictions before generating the pages.
3. **A new clean natural set** (if L2 must be re-tested after S19): questions written from pages dated after the corpus freeze, or
   a fresh slice of a verified benchmark. That is a separate decision for the user.

## 5. What this changes now
- Nothing in S19: it is frozen and running, and it tests the L2 system as pre-registered.
- The write-up must cite GopherCite, AIS, Faithful CoT, TyCor, CHyD, ACL-Verbatim and 2609.15964 as prior art for the L3
  construction. The claim narrows to: a pinned-corpus certificate with measured assumption rates and a sealed L2 test.
- The next design work is C1/C4 (relation-level checking with an explicit semantic-mapping assumption), tested first on synthetic
  pages, not more readers (C2 predicts they are nearly used up).

## 6. Proof plan: what must be established for the target theorem to follow (added 2026-11-07 ~14:00)
The user asked: setting aside whether it will succeed, which assumptions and proofs have to be completed so that the
claim is proven? This section answers that without regard to feasibility.

### Target theorem T*
For every question x, F(x) is one of Verified(y, κ), Qualified(conflict list), or Unresolved. Under the assumptions A_M, A_S and A_R below,
**if F(x) = Verified(y, κ), then y = y\*(x)** (the true answer). Corollary (L2 form): P(silent false claim) ≤ ε_M + ε_S + ε_R.

Notation: φ(x) = (entity e, relation r, qualifiers q, answer type τ) is the meaning of the question; φ(σ) = (e', r', q', value v)
is what the sentence containing span σ states.

### Deductive lemmas (plain code, proven or checked for every input)
| | lemma | status |
|---|---|---|
| D1 | Provenance: σ is a verbatim span of document d, and d is in the hash-pinned corpus | **done** (V1, V2; unit and property tests) |
| D2 | Derivation and type: y = P(σ) for a program P in a fixed language (normaliser, date/number parsing), and y has type τ | **done**, relative to τ (V3; tests, not machine-checked proof) |
| D3 | Frame match: release only if e' = e, r' = r (or a listed synonym), and q' agrees with q (incl. the period, which V4 handles today) | **not built**: this replaces most of A2 |
| D4 | Conflict → Qualified: if another retrieved source states v'' ≠ v for the same frame, output Qualified, never Verified | **not built** (the source-agreement rule is a weak statistical stand-in) |
| D5 | Rendering: the final text contains only (y, κ), with no new facts | **done** for short answers (template output) |

### Assumptions (cannot be proven; stated, then bounded by measurement)
| | assumption | how it is bounded |
|---|---|---|
| A_M | Semantic mapping: when the parser outputs φ(x) and φ(σ), both are the intended meanings. **Fail-closed**: on ambiguity it outputs nothing, and the system abstains. | hand audit of a random sample of parsed frames; frames are short and human-readable, so ε_M is directly countable |
| A_S | Source truth: the source's statement is true, v = y\*(x) | gold audit / adjudication; made visible by attribution (κ names the page and sentence) |
| A_R | Conflict visibility: if a credible conflicting source exists, retrieval finds it (needed only for D4) | if it fails, the error falls under A_S; measure how often a second source changes the outcome |

### Proof of T* given D1–D5 and A_M, A_S
A_M says φ(x) is what x asks. D3 says the sentence states value v for exactly that frame. D1 and D2 say y is that stated value,
in the asked type. A_S says the statement is true, so y = y\*(x). D5 says nothing else is asserted. If sources conflict, D4
outputs Qualified, so no unqualified claim is made. ∎
Soundness does not need parser coverage: a question the grammar does not cover gets no frame and ends as Unresolved. Coverage
costs yield (L1), not safety.

### Counting what is left
- **Two deductive components to build and verify: D3 and D4.**
- **Three assumptions to state and measure: A_M, A_S, A_R.** A_S and A_R are already measured in spirit (gold audit, agreement).
  A_M is new: it **replaces A2 and A3**. Today's A2 bundles three things: no frame match exists (D3 missing), the question
  is misread, and the source is misread. After D3, only the last two remain, as an explicit, countable parser error.
- **One measurement lemma** for the L2 corollary: grader false-credit f_up and gold adjudication (already in S18/S19).
- One supporting proposition (C4): no checker that sees only strings can certify "the span answers the question" without some
  semantic mapping. So A_M cannot be removed, only narrowed and measured. This makes T* the strongest form of L3 available for
  open-world factual QA.

### Optional strengthening of A_S (independent sources)
If two sources are conditionally independent given the frame (assumption I: near-duplicate texts merged, so mirrors count once) and
each is wrong with rate ≤ ε_S, then agreement on the same wrong v has probability ≤ ε_S². Conjecture C2 says I fails for Wikipedia
mirrors, so I must be enforced by construction (for example a text source plus a structured source such as Wikidata), not assumed.

## 7. First evidence on C1 (post hoc, design data; from the Kimi session, 2026-11-07 ~14:50)
Kimi's tiered checker on S19 DEV + FRESH: 28 kept wrong drafts = 9 distinct errors (E:\Models\halluc_runs\conj_mech_kept.json).
- Every residual error is a value that the checker's evidence states verbatim (28/28); none of 58 absent wrong values got through.
  Fabrication is already zero; the residual is A2 or A1.
- C1(a): asked entity (or a clear coreferent) in the same sentence: 7 of 9 (partly supported).
- A2 relation/qualifier mismatch: 5 of 9, of which 2 are entity/event mismatches ("Federation tournament", a nano-satellite without
  "India's first"), 3 are qualifier or predicate mismatches ("second sale", "first convention" vs "first keynote by a woman", a group list).
- Source states the asked relation with another value (A1, temporal change or gold noise): 3 of 9. D3 cannot fix these; they need D4.
- Incomplete answer: 1 of 9.
Design consequence: D3 checks qualifiers (ordinals, years) as well as the relation (results/runs/s20/frames.py).
