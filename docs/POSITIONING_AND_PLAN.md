# Positioning, the system we present, and the plan after S25 (2026-11-09)

## 1. What the paper is (one sentence)
A frozen local question-answering system whose released answers are verbatim, typed spans of hash-pinned pages, certified once on sealed SimpleQA questions to a 1% silent-error bound
(0.76% of all questions at 37.2% coverage), with a measured error budget across three benchmarks and an account of what stops the certificate from transferring.
It is an empirical and methodological paper, not a new-model paper. It does not claim to beat BalanceRAG-style calibrated cascades (they work at 5 to 30% risk on other data; nobody has run both on the same data),
and the bound itself is not new. Its content: (a) a pre-declared single-run certificate of a frozen deductive system, (b) the separation of system error from benchmark error with a decoy-validated blind adjudication,
(c) negative results with numbers: coverage and precision trade, agreement is as good a filter as the gate on two of three sets, derivation certificates add little, independent retrieval reduces but does not remove the added error,
(d) a synthetic closed-evidence test (two sealed sets, two model assignments) where the machinery gave no wrong definite answer.

## 2. The system model we present
"System of record" = the frozen S19 pipeline (nothing else is part of the headline claim):
1. Evidence: web (8 pages), local Wikipedia top-5 (Aug 2025), combined passage.
2. Readers: Qwen3-4B-Instruct-2507, plain and cautious prompts on each source (6 candidates); release needs support from all three sources.
3. Gate: the candidate must be a verbatim span of a pinned page and pass type and consistency checks V1 to V5.
4. Veto: Phi-4 cautious reader must agree.
Outputs: Verified (released with its span) or Unresolved. That is the whole headline system.
Evaluated extensions, each reported with its own status (none changes the headline):
| extension | status |
|---|---|
| pinned pages + format-relaxed gate | more coverage, 5 to 6% error on the added answers; not run on sealed data; reported as a negative result |
| independent title retrieval | added error 6.8% on DEV, rule (3%) not met; stopped; reported |
| entity slot, Qualified lists (L3 fork) | DEV and post hoc only; works on the synthetic corpus (sealed test, 0 wrong); not claimed on real data |
| derivation certificates | sound, adds almost nothing on Mintaka; works on the synthetic corpus |
| Qwen3.8-27B veto (S25) | rule not met (wrong added releases 18 with Phi-4, 18 with 27B, 16 with both); line stopped; docs/S25_RESULT.md |
| closed-evidence configuration (BM25 over a synthetic corpus, two readers + veto + gate + slot + certificates) | separate configuration, tested on two sealed synthetic sets |
We do not present a trained model. Goal B (model-internal mechanisms) has not started; its only attempt so far (the 4B stating its own entity) failed.

## 3. What is established, what is not
Established: SimpleQA L2 certificate (one run); error budget (system-attributable error 0.44% of releases, benchmark-specific classes 0.4% to 3%); coverage floor missed on Mintaka and PopQA; coverage costs precision;
no wrong definite answer on the synthetic closed-evidence sets.
Not established: L1 (4 against 9 errors on FRESH-5, not significant); L2 on a second real benchmark; transfer to other corpora or languages; any comparison with BalanceRAG-style methods on the same data; Goal B.

## 4. Plan after S25 (S25 result: the stronger veto did not catch the added errors; the coverage-raising line stops and the paper keeps v1)
Parallel tracks (no GPU):
A. Paper to submittable shape: full-text check of the cited sources (only abstracts so far), data and code availability statement, regenerate figures with the synthetic result, submission audit, one more pass on length and claims.
B. New sealed real questions (needed for any further L2 or L1 claim): time-anchored questions with gold regenerated from Wikidata queries (the PAT-Questions approach), adjudicated by the blind protocol; size by power (L2: about 1,500 items for k <= 6; L1: about 50 baseline plus system errors).
C. Same-data baseline: our LTT baseline exists; a two-branch BalanceRAG-style calibration needs an LLM-only branch score we have not generated (one 27B or 4B no-retrieval run on the SimpleQA design sets).
D. Package the system: a runnable repository (pipeline, gate, certificate protocol, hashes, generators of the synthetic sets) so the certification can be repeated on another distribution.
Not now: Goal B, other languages, larger models as a headline.

## 5. Decisions that are yours
1. Paper type and venue: empirical/methodology paper with a negative-results section (my recommendation) versus waiting for a stronger v2 result.
2. Whether to build the new sealed real-question set (track B). Without it there is no further L2 or L1 claim.
3. Whether the deliverable "model" is the packaged system (my recommendation) or a trained model (Phase 4, no evidence yet that it is needed).
