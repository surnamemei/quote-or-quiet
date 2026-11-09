# From one result to a general one: plan (2026-11-09)

## What "general" can mean
A single error rate cannot be universal: L2 is a statement about one question distribution. What can generalise is
(1) the guarantee structure (L3: a released answer is a verbatim span of a pinned source, given stated assumptions),
(2) a certification protocol anyone can run on their own distribution (sealed sample, pre-declared rule, corrected one-sided bound),
(3) a decomposition of silent error into assumption failures (A_S source true, A_M question mapped correctly, gold/time, mention
extraction) whose rates can be measured per domain and used to predict SER on a new distribution.
The claim to aim for is a map of where the guarantee holds and where it fails, with the failure causes named, not "hallucination solved".

## Axes to vary (one at a time, then jointly), each against a frozen method
| axis | now | next |
|---|---|---|
| reader / verifier model | Qwen3-4B + Phi-4 | other dense sizes, a MoE, another family (system rules are expected to transfer; internal-mechanism claims are not) |
| evidence corpus | FineWiki Aug 2025 + web | a closed domain corpus (biomedical abstracts, statutes, product docs) with the same gate |
| question type | single-hop lookup | numeric / computed (certificates), list, multi-hop |
| gold quality | SimpleQA, Mintaka, PopQA (noisy) | clean gold: closed-evidence formal tasks (exact answer by program), time-anchored facts |
| language | English | Chinese, one more |
| time | fixed snapshot | questions after the snapshot date (needs a refreshed corpus) |

## Prerequisite: new sealed data
All original SimpleQA items and the Mintaka / PopQA test samples are spent as design data, and their gold is noisy. Every cross-model
or cross-domain claim needs new sealed items with checked gold. Options, in order of cost: (a) closed-evidence tasks generated with a
program (gold exact, no noise, covers the L3 end); (b) time-anchored questions built from stable Wikidata/Wikipedia facts, gold verified
against a second source and by the blind adjudication protocol already built; (c) human-written questions (expensive, best).

## Steps
1. Decompose and predict (no new data): for FRESH-5, Mintaka, PopQA, estimate the assumption-failure rates from the error classes
   already assigned; write the predictive rule for SER on a new set before it is run; the next sealed set tests the prediction.
2. Build the sealed sets in (a) and (b) above with the freeze/hash protocol; sizes chosen by power (L2 needs about 1,500 items per
   cell for k <= 6; L1 at 50% needs about 50 baseline plus system errors in total).
3. Freeze the system, pre-register the matrix (model x corpus x question type), run once per cell, report every cell, pass or fail.
4. Head-to-head baselines on the same evidence at the same coverage: reader agreement (done), conformal risk control / Learn-then-Test,
   semantic entropy or a sufficiency gate.
5. Replace LLM adjudication with human adjudication on a subset to calibrate it.
6. Release the protocol, hashes and code so others can run the certification on their own distribution.

## What would not follow even then
Open-world truth, multi-turn dialogue, adversarial inputs, and Goal B (model-internal mechanisms) need their own evidence.

## Status (2026-11-09)
- Step 1 done on existing data: docs/GENERALITY_STEP1.md (system-attributable error 0.44% of releases, 0.18 to 0.91%, stable across three
  benchmarks; benchmark-specific classes vary tenfold; predictions P1 to P3 fixed).
- Step 2a started: docs/CLOSED_EVIDENCE_SPEC.md, generator results/runs/s24/gen_closed.py, DEV set closed_dev (200 items, hashes written).
  
- Step 2a done: closed_test (1,500 items, one run): 0 silent errors, upper bound 0.25%, coverage 54.2%, all six predictions held (docs/S24_CLOSED_TEST_RESULT.md).
- Reader-role swap (docs/S24_CONFIG_B_RESULT.md): closed_test2, Phi-4 readers + Qwen3.8-27B veto: 0 silent errors, coverage 56.9%, six of seven predictions held.
- Step 2b (time-anchored real questions) and steps 3 to 6 not started. S23 (independent retrieval on DEV) is finishing on the GPU.
