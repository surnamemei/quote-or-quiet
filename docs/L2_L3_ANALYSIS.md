# How to reach L2, and the theory for L3 (analysis, 2026-11-06)

All numbers come from DEV (300) and FRESH (200). FRESH-3 stays sealed.

## 0. What the targets require (target.txt, section 6)

- **L2, statistical reliability:**
  - on a clearly defined task distribution, the one-sided 95% upper bound on SER is below 1%;
  - **while keeping a pre-specified task-completion rate**;
  - on enough independent test items ("zero errors on a small test set does not count").
- **L3, strict guarantee:** a *deductive* statement. Given trusted inputs, a correct verifier, a reliable semantic mapping and strictly constrained output, one *proves* that every released factual claim satisfies the stated verification condition. It does not by itself guarantee open-world truth.

**Correction to my earlier labeling.** I called the conformal-risk-control calibrator (vkg/crc.py) "L3". It is not: it gives a *statistical* guarantee (expected risk ≤ α under exchangeability). It is L2 tooling. Its high-probability variant, Learn-then-Test (P(risk ≤ α) ≥ 1 − δ), is essentially the L2 test applied at calibration time. L3 needs the deductive construction in section 2.

## 1. L2

### 1.1 Statistics: how many errors are allowed
Clopper–Pearson one-sided 95% upper bound < 1%. SER counts errors over all n items.

| n | max errors | max observed SER |
|---|---|---|
| 200 | impossible (0 errors → 1.49%) | – |
| 300 | 0 | 0.00% |
| 500 | 1 | 0.20% |
| 1000 | 4 | 0.40% |
| 2000 | 12 | 0.60% |
| 3000 | 20 | 0.67% |

**Consequence 1: Verified alone cannot show L2.** Only 200 Verified items are left, and with n = 200, L2 is out of reach even with zero errors. L2 needs n ≥ 1000, ideally 2000–3000, so it must use the original-SimpleQA pool (2,526 items untouched after FRESH-3) or a newly built clean set.

**Consequence 2: the completion floor binds.** Without it, L2 is trivial: answer nothing, SER = 0. With a floor c on coverage, SER = c × selective risk, so selective risk must be at most (max SER)/c:

| completion floor | n = 1000 (SER ≤ 0.40%) | n = 3000 (SER ≤ 0.67%) |
|---|---|---|
| 30% | ≤ 1.33% | ≤ 2.2% |
| 40% | ≤ 1.00% | ≤ 1.7% |
| 50% | ≤ 0.80% | ≤ 1.3% |

### 1.2 Where we are
- **Best operating point, MS3** (answer only when all 3 evidence sources agree), pooled DEV + FRESH: 4 errors in 240 answered. Selective risk 1.67%, coverage about 48%, SER about 0.80%.
- **At n = 1000 and a 40% floor:** a 1.7x reduction in selective risk is needed.
- **At n = 3000 and a 40% floor:** almost met on paper (1.67% vs 1.7%), but with no margin, and only if gold noise on original-SimpleQA items does not add errors.

### 1.3 Error budget: measured SER is more than model errors
Write coverage c, true model error rate among answered items r, gold-label error rate g, and grader error rates f₊ / f₋. f₊: a correct answer is graded wrong. f₋: a wrong answer is graded correct, which hides errors.

  measured SER ≈ c·[ r·(1 − f₋) + (1 − r)·(g + f₊) ]

- **Gold errors** (g) count as errors even when the model is right. On Verified, g is small by construction. On original SimpleQA, g is unknown and could be around 1–3%. At c = 0.4 that alone adds 0.4–1.2% SER, enough to make L2 impossible regardless of the model. **So L2 on original-SimpleQA items needs a gold audit.**
- **Grader:** about 0.3% disagreement on 260 blind rows; small next to g but not negligible at this precision.
- **f₋ (hidden errors)** biases SER down. It must be estimated, not ignored, so that the bound stays valid.

### 1.4 Gold-audit protocol (pre-registered; symmetric to avoid bias)
- **What gets audited:**
  - every answered item the grader marks wrong (candidate gold error, or grader false negative);
  - plus a random sample of graded-correct answered items, about 10%, to estimate f₋ and wrong-gold matches.
- **Who audits:** blind to which system produced the answer. Two independent checks against primary sources: one human, and one second-family LLM with web access; disagreements go to the human.
- **What is reported:** raw SER (grader 6.1 as is) and audited SER, each with its bound. The primary L2 metric must be named in advance. Proposal: audited SER, with the audit sample's own uncertainty propagated by a union bound or bootstrap.

### 1.5 Reducing model errors: theory of agreement
- **Why independence would help:** if K evidence sources erred independently with probability p and always agreed on the same wrong answer, the joint error would be p^K.
- **Why it doesn't fully:** the observed errors are strongly correlated. In 2 of the 3 MS3 errors on FRESH, all three sources repeated the same wrong fact, because the sources share upstream text (web copies of Wikipedia).
- **Model:** P(err | all agree) = P(err) × q, where q < 1 measures conditional independence. Adding a signal with conditional agreement-on-error rate q′ (the chance that it also says the same wrong answer when the others agree on one) multiplies selective risk by about q′, at a coverage cost equal to its disagreement rate on correct items.
- **What we need:** q′ ≤ 0.6 at < 15% coverage loss gives the 1.7x needed at n = 1000.
- **Candidates, roughly in order of expected independence:**
  1. **A second reader from another model family** on the same passages. It removes reading errors but not source errors. Its q′ can be measured right away on DEV/FRESH from the mini-kimi session's Flash-Next run (same passages via vkg/reader_run.py). Caveat: the Flash-Next build is Qwen3.8, the judge's family, so judge independence needs a second-family judge (agreed in the joint plan).
  2. **Source diversity by construction:** require agreement between a non-Wikipedia-derived web source and Wikipedia, with near-duplicate text across sources counted as one source. This targets the shared-upstream problem directly.
  3. **Typed verification for dates and numbers:** release a date or number only if it appears verbatim, at the asked granularity, in a sentence of a source. Two of the 4 MS3 errors involve wrong or incomplete dates.
  4. **Training (Goal B):** teach the reader to abstain when evidence is indirect. Slow, and measured only after 1–3.

### 1.6 Concrete L2 path
1. Measure q′ for the second reader on DEV + FRESH: Flash-Next run, then score_jsonl, then the agreement analysis. About a day, GPU-bound.
2. Add source de-duplication (2) and the typed date/number check (3). Design on DEV, check on FRESH.
3. Pre-register the operating point: a completion floor, proposed at 40%, unless DEV + FRESH show a different achievable rate.
4. Test set: FRESH-3 (1000) plus about 1000–2000 more from the untouched original pool, sealed now; n = 2000–3000 relaxes the needed SER to 0.60–0.67%. Plus the gold-audit protocol (1.4).
5. One pre-registered run; report raw and audited SER with bounds.

## 2. L3: a deductive guarantee within a stated scope

### 2.1 Construction: constrained, verified extraction
Fix a trusted corpus D: the local FineWiki snapshot (6,614,655 articles, source files verified by SHA-256). Restrict the output space so that the system can release only

  y = (answer a, document id d, character span [i, j)) with d ∈ D.

A small, deterministic verifier V accepts y iff:
- **V1:** d exists in the pinned D (hash of the document text matches the index);
- **V2:** a = N(D[d][i:j]), where N is a fixed, deterministic normaliser (whitespace, Unicode NFC, number formats);
- **V3:** the answer type T(x) required by the question (date at day, month or year granularity; number with unit; person; place) is matched by D[d][i:j] under a fixed grammar for T.

The system F outputs a only if V(x, y) = accept; otherwise it outputs "Unresolved" (target state 3) together with what is missing.

### 2.2 Theorem (soundness of release)
For every input x, if F(x) = a ≠ Unresolved, then there exist d ∈ D and a span [i, j) such that a = N(D[d][i:j]) and that span has the answer type T(x) required by the question.

**Proof.** F's only output path for a non-Unresolved value goes through V. V's checks V1–V3 are decidable string and grammar checks, so acceptance implies the stated conditions. ∎

The theorem is deliberately simple: the content of L3 is the constrained output space plus a verifier small enough to be trusted, because it can be tested exhaustively and its normaliser N and type grammar T could be machine-checked. That is what the target describes: verification conditions are proven, not estimated.

### 2.3 What the theorem does *not* cover (the assumptions), and how L2 connects
A released answer can still be false if:
- **A1:** D itself is wrong at that span (source error);
- **A2:** the span does not actually answer x (the semantic mapping from question to span is wrong, e.g. the right number for the wrong entity or year);
- **A3:** the question's answer type T(x) is misparsed.

**Corollary (end-to-end bound, union bound):**

  P(released answer false) ≤ ε₁ + ε₂ + ε₃,

where εₖ is the rate at which assumption Aₖ fails among released answers. Each εₖ can be estimated with a Clopper–Pearson bound from an audit sample, so L3 (deductive, given the assumptions) and L2 (statistical, on the assumptions) combine into one bound for the system.

### 2.4 Scope sizes measured on DEV
- **Infobox-exact scope**, where the answer is a value of a structured infobox field on a top-5 page: the gold is found in **13.3%** of DEV. Here A2 is easiest to control (mapping from relation to field key).
- **Verbatim-span scope**, where the gold string occurs anywhere in the top-5 page text: **65%** of DEV. Here the theorem still holds, but A2 (choosing the right span) is a learned step, so ε₂ dominates and must be audited.

### 2.5 Concrete L3 path
1. Implement V (V1–V3) as a small module with exhaustive unit tests and property tests; pin D by hash.
2. Make the reader output (a, d, span) instead of free text (span selection by the 4B or a second reader). Anything V rejects becomes Unresolved.
3. State the theorem in the report with assumptions A1–A3, then measure ε₁–ε₃ by audit on DEV + FRESH, and once on the sealed set within the S17 or S18 run.
4. Optional, for rigour: machine-check N and T, for example with property-based tests and, if wanted, a Lean or Coq proof of the normaliser's properties.

## 3. Summary
- **L2:** not reachable on the remaining Verified items (n = 200 is too small). It needs n = 1000–3000 from the original-SimpleQA pool with a pre-registered gold audit, a pre-specified completion floor (proposal: 40%), and about a 1.7x drop in selective risk from the current 1.67%. The most promising lever is a measured, independent second signal: another reader family, source de-duplication, typed date/number checks.
- **L3:** a soundness theorem for constrained, verified extraction from a pinned corpus. The proof is by construction; its assumptions are measured with L2 statistics. The scope is 13% of questions (infobox) to 65% (verbatim span) on DEV.
