# S42 related work: has quote sufficiency been done? (2026-11-10)

Question: has anyone already (a) measured that a correct answer is shown with a verbatim quote that does not state it,
and (b) fixed it by choosing the quote and withholding when no quote is sufficient?

Short answer: (a) yes, several times, on other tasks. (b) the parts exist; the combination tested in E7 was not found.

Status column: A = abstract page read; F = full text read in part; S = search summary only (check before citing).

## 1. The finding itself is known

| Work | What it shows | Status |
|---|---|---|
| Lin, Ji, Liu, Sun. Denoising Distantly Supervised Open-Domain QA. ACL 2018 (P18-1161) | A paragraph that contains the answer string often does not answer the question; a paragraph selector is trained | S |
| Min, Chen, Hajishirzi, Zettlemoyer. A Discrete Hard EM Approach for Weakly Supervised QA. EMNLP 2019 (D19-1284), arXiv:1909.04849 | An answer is mentioned several times in a document and only one mention answers the question (their example: five mentions, the fourth is right); the model learns which mention | S |
| Asai, Gardner, Hajishirzi. Evidentiality-guided Generation. NAACL 2022, arXiv:2112.08688 | In 30% of 20 checked NQ cases the passage with the answer string gives no evidence for the answer; evidentiality labels mined by leave-one-out | F |
| Liu, Zhang, Liang. Evaluating Verifiability in Generative Search Engines. Findings of EMNLP 2023, arXiv:2304.09848 | Human audit: about half of sentences fully supported by their citations; about three of four citations support their sentence | S |
| Zhang, Chen, Commodore-Mensah, Oberst. Verifiable by Construction. arXiv:2609.15964 (2026) | 12 models, 222 clinical questions: over 90% of claims carry a verbatim quote, but strict support is 33.8 to 79.0% (claude-opus-5: 98.0% verbatim, 37.1% fully supported). LLM judge, checked on 70 pairs against two people (kappa 0.81 to 0.86) | F |
| Wallat, Heuss, de Rijke, Anand. Correctness is not Faithfulness in RAG Attributions. arXiv:2412.18004 (ICTIR 2025) | Another axis: the cited document is right but the model did not use it (up to 57% of citations) | S |

Our E6 number (12.5% of Verified releases show a quote that does not state the answer; 72 of 75 answers still right)
is a new measurement of a known effect. It is new only for this kind of system: a deductive gate that accepts a typed
verbatim span. The paper must say this and cite the rows above.

## 2. Verbatim quotes with a machine check exist

| Work | What it does | Difference from this project | Status |
|---|---|---|---|
| Menick et al. Teaching language models to support answers with verified quotes (GopherCite). arXiv:2203.11147 (2022) | Answer with a verbatim quote; abstains when unsure; rated high quality 80% (NQ) and 67% (ELI5), 90% and 80% when declining a third of questions | Quote is produced by the model with the answer; support is rated by people, not gated; no bound on misleading quotes | A |
| Guan. Attributable by Construction (CAMS). arXiv:2606.23989 (2026) | Deterministic matcher; claims without a located quote are dropped; says provenance is guaranteed, support is not | No rate of unsupporting quotes; no choice among several quotes | F |
| Recski, Tóth, Verdha, Boros, Kovács. ACL-Verbatim. arXiv:2605.21102 (2026); VerbatimRAG | Answers are verbatim spans; span extractor scored by word F1 (53.6) | No sufficiency test of the span, no abstention reported | A |
| Verifiable by Design (quote-tuning; authors to be checked), arXiv:2404.03862; subsentence citations, arXiv:2406.06125; survey arXiv:2508.15396 | Train models to quote; finer citations | Same gap | S |

R1 (the quote exists, checked by machine) is therefore not new as an idea. Do not claim it as a contribution; claim
only that it holds with zero exceptions in our runs.

## 3. Sufficiency checks and selective release exist

| Work | What it does | Status |
|---|---|---|
| Joren et al. Sufficient Context. ICLR 2025, arXiv:2411.06037 | LLM rater labels context sufficient or not (93% accuracy); selective generation from confidence plus sufficiency; correct share among answered up 2 to 10 points | S |
| Qiu, Han, Huang. SURE-RAG. arXiv:2605.03534 (2026) | Claim-passage verifier (supports, refutes, insufficient); release only when support holds; risk 0.259 to 0.164 at 30% coverage; counterfactual swaps in evaluation; GPT-4o as judge | A |
| DocAttriBench arXiv:2609.20574; arXiv:2512.06476; arXiv:2609.01687 | Evidence-only sufficiency and evidence-masked necessity tests; sufficiency boundaries for multi-hop QA | S |
| Raduta et al. HALO. arXiv:2607.17883 (2026) | Groundedness scored by an LLM judge plus checks against the source; calibrated abstention. The abstract does not say that quotes are verbatim or that a quote must state the answer | A |

These work at passage level with a trained or large judge, and report risk, not a bound near 1%. None works on the
displayed sentence.

## 4. The reader checks of E7 exist one by one

| Check in E7 | Prior work | Status |
|---|---|---|
| G, answer from the quote alone | Perez et al. Finding Generalizable Evidence by Learning to Convince Q&A Models. EMNLP 2019 (D19-1244): select sentences that make a judge model give the answer; people keep about 90% of accuracy on 20% of the text. Caveat they report: selected evidence also sways the judge toward wrong answers (31.1% against 74.6% for right ones on RACE). So "a reader gives the answer" does not prove "the quote states it" | F |
| W, swapped span | Longpre et al. 2021 entity substitution (from memory, not re-read); Faithfulness-QA arXiv:2604.25313; Li et al. arXiv:2409.10955 | S |
| I, inverse question | Alberti et al. Synthetic QA Corpora Generation with Roundtrip Consistency. ACL 2019 (P19-1620), arXiv:1906.05416 | S |
| C, contrast question | SQuAD 2.0 unanswerable questions; contrast sets; RefusalBench arXiv:2510.10390 | S |
| Choosing a better quote after the fact | arXiv:2609.15964 "recovery": a judge is given the claim and all sections read, proposes a span, only verbatim spans count; support rises from 37.1% to 85.1% for one model. Closest to E7's witness choice | F |

## 5. What was not found

No paper found that does all of the following together:
1. lists every span that a mechanical gate accepts and picks the witness by a fixed, frozen list of checks;
2. withholds the answer (Unresolved, nothing quoted) when no span passes;
3. states the rule and predictions before a blind review of fresh items;
4. reports an upper bound on "the reader re-checks and finds the quote does not say it" near 1% together with the cost
   in coverage;
5. uses only small local models (4B) as readers.

The closest is the recovery step of arXiv:2609.15964. It differs in three ways: the span is proposed and judged by a
large model, it is an analysis and not a release rule, and no misleading rate after recovery is bounded.

Searches cannot prove absence. Wording for the paper: "we did not find", with the search date.

## 6. Consequences for the plan

- Do not present "right answer, wrong quote" as a discovery. Present E6 as its size for a deductive gate (12.5%, and
  that the cause is first-match selection, as in Min et al. 2019).
- Do not train a sentence selector (Lin 2018, Min 2019, Asai 2022 did). E7 stays training-free; that is its difference.
- Keep E7 as designed, with one addition taken from Perez et al.: a reader check alone is not accepted as proof. The
  frozen rule must contain at least one lexical check (F or S) beside the reader checks, and the test endpoint stays
  the blind human-style review, not the reader.
- Report the recovery step of arXiv:2609.15964 as the nearest baseline in related work. A direct comparison would need a
  large judge model, which is outside the local-model limit; say so.
- Paper related work gains: Menick 2022, Min 2019, Lin 2018, Asai 2022, Liu 2023, Zhang 2026, Guan 2026, Joren 2025,
  Qiu 2026, Perez 2019, Alberti 2019, Wallat 2025. Every entry marked S above must be opened and checked first.
