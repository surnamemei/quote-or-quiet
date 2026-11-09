# Long-form Quote or Quiet: survey, what transfers, design (2026-11-09; research note, nothing run)

## 1. What exists (read at abstract level unless stated)
- **Evaluation by atomic claims.** FActScore splits a biography into atomic facts and checks each against Wikipedia; SAFE (LongFact) does the same with a search agent; VeriScore checks only verifiable claims; VeriFastScore and FastFact make this cheaper; VeriFact adds recall. Common shape: decompose, then verify each claim.
- **Guarantees.** Mohri and Hashimoto (ICML 2024, "Language Models with Conformal Factuality Guarantees") split the output into sub-claims, score each, and drop the least certain so that, marginally over prompts, the remaining text is fully correct with probability at least 1 - alpha. Follow-ups: coherent factuality (filter well-supported claim subgraphs; ignoring the graph breaks the guarantee), group-conditional and adaptive (prompt-dependent) versions. The known cost: to reach a strict target, much of the text is removed.
- **Claim-level abstention and editing without a formal guarantee.** CURE (2604.12046) trains per-claim confidence and abstains on uncertain claims; FACTOR (2606.22474) adapts verification strictness per claim; compositional selective specificity (2604.17487) rewrites a claim at the most specific level the evidence allows instead of deleting it (LongFact utility 0.846 to 0.913, 94% specificity kept); claim-selective certification for medical RAG (2605.21949) labels a response full / partial / conflict / abstain against its own certificate definition.
- Gap: the guaranteed methods certify "probably correct" from a score; the editing methods have no guarantee; none makes each kept sentence carry a verbatim quote from a pinned source, and none separates the system's error from the reference's error when measuring.

## 2. What transfers from the short-form system
| short form (done) | long form |
|---|---|
| one claim per question | many claims per answer, correlated within an answer |
| verbatim typed span in a hash-pinned page (deductive gate V1-V5) | works only for the claim's value slot (a date, a name, a number); the relation between subject and value needs another check |
| agreement of three sources plus a second reader | per claim, the same idea is affordable only for the claims that carry a checkable value |
| Verified / Unresolved | Verified sentence (with quote) / Qualified sentence (less specific, still quoted) / dropped |
| SER over questions with a Clopper-Pearson bound | false-kept-claim rate over claims, with a bound that accounts for clustering by answer (bootstrap or a per-answer bound) |
| ambiguity floor (T6) | applies per claim: a claim about "Heat" is checked against the page the system names, and the reader sees that page |

## 3. Design: reduce each claim to the short-form gate
1. **Draft.** The 4B reader writes the answer from the combined evidence (web + local Wikipedia), as now.
2. **Decompose.** Split into atomic claims (FActScore-style prompt, a different model from the drafter to avoid self-agreement).
3. **Reduce.** For each claim, ask for the slot form (subject, relation as a short question, value): "Marie Curie was born in Warsaw in 1867" -> (Marie Curie, "Where was Marie Curie born?", Warsaw), (Marie Curie, "When was Marie Curie born?", 1867). Claims with no checkable value (evaluations, summaries, causal statements) are marked as unverifiable.
4. **Verify.** Each slot question goes through the frozen short-form machinery with the claim's value as the only candidate: support from the evidence sources, the verbatim typed span in a pinned page of the subject, and the second reader. Pass -> the claim is Verified and carries its quote.
5. **Rewrite.** Keep Verified sentences with an inline quote and source; for a failed specific value try the coarser value the evidence supports (year instead of date, country instead of city) and keep it as Qualified if that passes (the specificity idea of 2604.17487, but with a quote); drop the rest, or keep unverifiable claims only in a separately marked "not checked" part.
6. **Output.** Text in which every factual sentence has a quote; nothing unquoted is stated as fact.

## 4. How it would be measured
- **Testbed:** FActScore biographies (people with Wikipedia pages; the reference source is Wikipedia, which matches the pinned snapshot), plus a sample of LongFact prompts for open topics.
- **Metrics, per answer and pooled:** (a) false-kept-claim rate = kept claims that are false / kept claims, judged against the facts by blind reviewers (two, with decoys, as S35); (b) retention = kept checkable claims / checkable claims in the draft; (c) FActScore of the final text; (d) share of the final text that is "not checked".
- **Target for a first sealed test (to be fixed before running):** false-kept-claim rate with a 97.5% upper bound below 1% (claims clustered by answer), at retention of at least 50% of the checkable claims.
- **Baselines at matched retention:** the raw draft; conformal factuality (Mohri and Hashimoto) with the same claims and a confidence score from reader agreement; an NLI filter against the same evidence.

## 5. Risks known in advance
- Decomposition and reduction errors: a claim reduced to the wrong question is verified against the wrong slot. The reduction must be checked on a design set before any test.
- Relation errors: the value is on the page but in a different relation (a death year given as a birth year). The typed gate catches some (type of the question), not all; the second reader is the main defence, as in short form.
- Correlation within an answer: one wrong entity (a namesake) makes many claims wrong at once; the bound must be computed per answer, not per claim, or with a cluster bootstrap.
- Cost: seven readings per claim are too many for long answers; per claim the system can reuse the answer's evidence and run only the gate plus one second reading.

## 6. Order of work (after L1 and the tool, per the agreed roadmap)
1. Design set: 50 FActScore people; measure decomposition and reduction quality by hand-checked samples.
2. Freeze; write predictions; sealed set of 200 to 500 people; one run; blind review of kept claims.
3. Compare with conformal factuality at matched retention.

## Sources
- Mohri and Hashimoto, Language Models with Conformal Factuality Guarantees, arXiv:2402.10978.
- VeriScore, arXiv:2406.19276; VeriFastScore, arXiv:2505.16973; VeriFact, arXiv:2505.09701; FastFact, EMNLP 2025 Findings.
- CURE, arXiv:2604.12046; FACTOR, arXiv:2606.22474; Compositional selective specificity, arXiv:2604.17487; Claim-selective certification, arXiv:2605.21949.
- Multi-group uncertainty quantification for long-form generation, arXiv:2407.21057; coherent factuality (Rubin-Toles et al., ICLR 2025).
