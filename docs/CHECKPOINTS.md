# Checkpoints: what must be true before each final conclusion can be claimed

Written 2026-11-05. Definitions come from target.txt sections 5–6. Numbers are on FRESH (200 SimpleQA Verified questions, Wikipedia retrieval) graded with grader 6, unless stated. "Small model" means Qwen3-4B-Instruct-2507.

## 0. Prerequisites for any claim (measurement validity, target.txt Phase 0)

| # | Condition | Status |
|---|---|---|
| P0.1 | The grader is validated on blind labels it was not designed on: false credit (wrong answers credited) has a 95% upper bound ≤ 2%, and misses ≤ 5% | **Met**. Grader 6 on V3: 0/196 false credit (upper bound 1.9%), 0/64 misses. |
| P0.2 | Error-injection test: known-wrong answers made from correct ones are credited ≤ 2% of the time | **Met** (2026-11-06): 2/328 credited (0.6%, upper bound 2.2%); both are in fact still correct (results/grader6/GRADER6_RESULT.md). Floor test: easy corruptions. |
| P0.3 | The labels come from a rater independent of the system and of the grader | **Partly met**. Blind LLM raters (Claude), not humans; the judge is the same model family as the systems. The final L2 claim needs a human audit of a sample, or must disclose this. |
| P0.4 | Answerable, unanswerable and conflicting questions are reported separately | **Partly met**. SimpleQA (mostly answerable), SQuAD2-unanswerable, FaithEval (conflicting) exist; the small-model pipeline is not yet scored on all three with grader 6. |
| P0.5 | A clean, untouched test set exists for the final claim | **Needed**. FRESH has now been used for S8, S9 and grader 6, and DEV was used for design. A FRESH-2 set (new SimpleQA questions beyond 500, same retrieval) must be built once and scored once, at the end. |
| P0.6 | Contamination guard if web search is added | **Planned** (benchmark mirrors blocked, pages containing the question verbatim dropped). |

## 1. L1: measured improvement (target.txt: at equal coverage and budget, SER at least 50% lower than a strong baseline, and correct yield not lower)

Baseline: 4B plain prompt with the same retrieval: coverage 71.0%, correct 61.0%, SER 10.0% (selective risk 14.1%).

| # | Condition | Current best | Status |
|---|---|---|---|
| L1.a | SER ≤ 5.0% at coverage ≥ 71% (paired 95% CI on the difference entirely below 0) | 4B cautious: 4.0% SER but coverage 61% | **Not met**. The SER gain is bought with coverage. |
| L1.b | Correct yield ≥ 61.0%: non-inferior, with the paired CI lower bound ≥ −3 points | Cautious 57.0% (−4.0) | **Not met** |
| L1.c | Cost recorded (extra tokens, seconds and retrievals per correct answer) and within a pre-set budget, e.g. ≤ 3× the baseline | Not measured | **Missing** |
| L1.d | Confirmed once on FRESH-2 (P0.5) | n/a | **Pending** |

What closes the gap: the search-on-abstain loop (S11). It must recover enough abstentions to bring coverage back to ≥ 71% and yield to ≥ 61% while keeping SER ≤ 5%. This is the most important reference point for checking that the direction is right. If S11 cannot move the 4B toward L1.a and L1.b, the direction is wrong and must change.

For reference, the 27B with the strict prompt sits at coverage 65%, correct 63% and SER 2.0%. The strong prompt alone is not enough for L1 either, because coverage is lower than the plain baseline.

## 2. H2: recovery, not just hiding (target.txt)

| # | Condition | Status |
|---|---|---|
| H2.a | Define "recoverable": the gold answer string occurs in some page the search loop could reach. This is measured by code (a gold-in-retrieved-pages check), with the gold used only for this labelling, never by the system. | **To build** with S11 |
| H2.b | Recovery rate: among items the baseline got wrong or abstained on that are recoverable, the share that S11 answers correctly. Target ≥ 30% (pre-registered in S11). | **Pending** |
| H2.c | Harm: among items the baseline got right, the share S11 gets wrong is ≤ 2% | **Pending** |

## 3. L2: statistical reliability (target.txt: 95% one-sided upper bound on SER below 1%, at a pre-set yield)

| # | Condition | Status |
|---|---|---|
| L2.a | Fix the task distribution in advance (for example: SimpleQA Verified questions, Wikipedia evidence, small-model system S*) and the minimum correct yield (for example ≥ 55%) | To decide when S11 is scored |
| L2.b | Sample size: the Clopper–Pearson upper bound is below 1% with 0 errors in 299 questions, 1 in 473, 3 in 773, and 5 in about 1,050. At the best measured SER (27B 2.0%, 4B cautious 4.0%) L2 is out of reach at any sample size. The true SER must first fall to about 0.3% or lower. | **Not met**: SER is 7–13× too high |
| L2.c | Grader error included in the bound: residual false credit must be bounded too. True SER ≤ measured SER + (grader false-credit upper bound × the share of wrong answers among those published). That needs a grader false-credit bound of about ≤ 0.5%, i.e. about 600 more labelled wrong answers with 0 credited, or a human audit of every published answer in the certification sample. | **Not met** (the bound is 1.9% now) |
| L2.d | One independent run on unseen questions (FRESH-2 or larger), with the protocol frozen first | Pending |

Fastest honest route: L2 is realistic only for a restricted slice (for example questions whose answer is a verbatim span or a code-computed value from a retrieved passage, with abstention elsewhere) or after S10/S11-style reductions push SER below 0.5%. Pre-registered risk control can then choose the abstention threshold so that the bound holds by construction (conformal / learn-then-test).

## 4. L3: strict guarantee within a formal scope (target.txt: trusted inputs, correct verifier, reliable semantic mapping, constrained output)

| # | Condition | Status |
|---|---|---|
| L3.a | Computable questions: every published number is produced by executed code from inputs copied verbatim, and the verifier re-runs it | Shown on synthetic formal tasks (VKG_v2) and in S9 compute mode (2 uses). Needs a written scope and proof plus an error-injection test. |
| L3.b | Attribution: every published answer is a verbatim passage span, checked by code | **Met by construction** in S9 (776/776 certificates verified). This guarantees "supported by the source text", **not** "true" or "the right span". The semantic-mapping condition is not met. |
| L3.c | Report the share of real questions that fall inside the formal scope (coverage of L3) | Not reported yet |

## 5. Goal B: fewer hallucinations from the model itself, without an external verifier

| # | Condition | Status |
|---|---|---|
| B.a | Model-only (no checker, no gate): a trained model reaches L1.a and L1.b against its own base model | S6b-trained (DEV): SER 3.0% vs plain 13.0%, but correct 52.7% vs 61.0%, so not at equal yield. S10 is running. |
| B.b | Mechanism evidence: the gain comes from the targeted failure (reading or distractor errors fall in a manual error audit), not from abstaining more | Pending (S10 analysis plans a by-kind breakdown) |
| B.c | H3, transfer across architectures (dense, MoE, hybrid) | Not started; only needed for a cross-architecture claim |

## Order of work, given limited time
1. Finish and score S10 (running).
2. S11, search-on-abstain for the 4B: the decisive direction check for L1 and H2.
3. P0.2 error injection (cheap) and the cost logging needed for L1.c.
4. Build FRESH-2 once and run the final L1 confirmation.
5. Decide whether L2 is reachable (it needs SER ≤ about 0.3%). If not, scope L2 to the verbatim/computed slice and report its coverage.
