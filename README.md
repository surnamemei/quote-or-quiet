# Quote or Quiet

A small local model that answers with a quote you can check, or stays quiet. (Answers with receipts, or silence.)
On sealed SimpleQA questions it gave a wrong answer for 0.76% of all questions or fewer (97.5% upper bound), at 37% coverage.

Most of what is below is how we measured that, and what we found when we tried to push it further.
(Internal programme name: VKG, Verifiable Knowledge Generation. The paper draft is `paper/manuscript.md`.)

**中文简介：** 目标是让模型别胡说：能联网、能核对来源时才给确定答案，核对不了就明说"无法确认"，而不是让用户每次都要二次确认。这个仓库放的是系统、论文草稿和全部评估记录。结论很克制：在 SimpleQA 封存题上，所有问题里"给出错误答案"的占比上界为 0.76%（覆盖率 37.2%）；换到另外两个基准，覆盖率不够，并且发现那里很多"错误"其实是基准自己的金标准过时或问题有歧义。这不是"消除了幻觉"。

## Progress tracker (docs/PROGRESS_TRACKER.md)
The objective is that a model presents nothing it cannot back with a checked quote. It is split into 16 gates with 3 criteria each:
- T: the 97.5% upper bound of the gate's error share is at or below its threshold.
- N: the sample has the minimum size.
- V: the test was registered beforehand, on unseen data, with valid decoys.

The bar counts criteria met. It is not a percentage of hallucination solved.

```
Overall [#################################.......] 40/48 (83%)
```

| gate | area | status |
|---|---|---|
| G1, G2 | templated short facts: wrong answer; quote not stating it | passed |
| G3, G5, G6 | natural questions (quote); ambiguous names; two-hop chains | passed |
| G4 | natural questions: wrong answer under 1% at 35% coverage | failed first test (7 errors, upper 1.20%); second test (1,500 NQ-open questions) running |
| G7, G8 | long-form claims (biographies; other kinds of text) | passed |
| G9, G10 | contested topics: view credited to the wrong party | passed |
| G11 | pages that are not Wikipedia | passed |
| G12 | people agree with the language-model reviewers | open (needs two people) |
| G13 | the quote rule beats standard checkers | passed |
| G14 | applied to drafts of other models (Llama, Gemma, Mistral) | passed |
| G15 | tool stress test: no release without a checked quote | failed first test (208 /bio values not verbatim in their quote); second test on tool v2 registered (docs/S72_G15B_PLAN.md) |
| G16 | replication by someone else | open (docs/REPLICATION.md) |

## What it does
For each question the system reads three evidence sources (web pages, a local Wikipedia snapshot, and both combined) with a 4B model, and releases an answer only if
1. all three sources agree on it,
2. the answer is a verbatim, correctly typed span of a hash-pinned page (checks V1 to V5),
3. a second model (Phi-4) agrees.
Otherwise it says it cannot confirm. The claim it makes is deductive and narrow: the released string is a span of a pinned page. It does not prove the page is true, that the span answers the question you meant, or that the answer is still current.

## Headline results (paper/manuscript.md)
| test set | n | coverage | wrong definite answers over all questions (observed, 97.5% upper bound) | |
|---|---|---|---|---|
| SimpleQA, sealed, one pre-registered run | 1,526 | 37.2% | 0.26%, 0.76% | 1% bound met |
| Mintaka, sealed | 2,000 | 31.0% | 1.40%, 2.08% (after blind adjudication of the gold: 0.45%, 0.92%) | coverage floor missed |
| PopQA, sealed | 2,100 | 19.1% | 0.81%, 1.35% | coverage floor missed |
| synthetic closed-evidence, two sealed sets | 1,500 each | 54.2%, 56.9% | 0, 0.25% | met (synthetic corpus) |
Per released answer, the SimpleQA bound is 2.04% (observed 0.70%): about one wrong answer in 140 answered questions, not zero. Metric definitions and the full scorecard: docs/SCORECARD.md.

## What did not work (reported with numbers in the paper)
- Raising coverage by pinning retrieved pages or relaxing answer formats added answers at 5 to 6% error; retrieving pages without the web cut that to 6.5% on a small design set; a larger veto model (Qwen3.8-27B) did not catch the added errors.
- At equal coverage, agreement among readers filters about as well as the deductive gate on two of three sets (4 against 9 errors on SimpleQA, not significant).
- Derivation certificates for computed answers are sound but cover under 2% of questions.
- Most of the "errors" on Mintaka were stale or wrong benchmark gold (19 of 28), found with a blind, decoy-validated adjudication.

## Does the quote say it? (added 2026-11-10; paper sections 5.10 to 5.17)
A quote that exists on its page can still fail to state the answer, and then a person who re-checks the release is misled. We measured that with two blind reviewers per row (language models that see only the quote) and tried to remove it.

| setting | what was done | result (misleading quote or false claim, both reviewers; 97.5% upper bound) |
|---|---|---|
| templated short questions (Wikidata relations) | quote chosen among all accepted spans by a frame check, a subject link and a quote-only reader (rule W1) | 2 of 1,017 fresh releases misleading (0.20%, 0.71%) against 12.5% for the first accepted span; coverage 49% against 52.5%; on a third sealed set (registered beforehand) 2 of 267 kept quotes misleading (0.7%, 2.7%) against 11.3% for the displayed quote (27B-judge version 0.7%, small judge 1.5%, rule R 2.2%) |
| biographies written by Phi-4 (14B) | claims verified against the subject's own page (rule W4) | closed-book drafts: 4.7% false and 4.7% misleading among kept claims (failed its sealed test); drafts written from the page: 61% of claims kept, 1 of 400 false and 1 of 400 misleading on 50 fresh subjects |
| names that several films or people share | one answer per reading, each with its own quote | 0 false and 0 misleading among 250 readings (1.5%) |
| open questions, no relation frames (rule R) | sentence quote, question numbers present, quote-only judge with a swapped-answer control | SimpleQA-style: 1.0% misleading (3.7%) against 11.3% for the displayed quote, withholds 35%. Natural Mintaka questions: failed, 24.0% misleading (30.6%) against 43.0% displayed; a small judge trained on reviewer labels gave 5.2% (10.0%) there |
| web pages that are not Wikipedia | rule R unchanged | 3.8% misleading (7.3%) against 11.3%; predictions failed |
| two-hop questions (birth place, country) | two checked quotes and a same-place check | 1 of 55 chains misleading, none false (pilot, 71 items, wide bounds) |
| a small judge | 0.6B model trained on 4,595 reviewer labels | AUROC 0.988 on held-out questions; 2.6% not 'states' among accepted against 8.8% for the prompted 4B judge; AUROC 0.897 on the Mintaka rows it never saw; a 27B prompted judge did better still (1.1% on held-out rows, 1.9% on the Mintaka rows); the off-the-shelf MiniCheck-Flan-T5-Large (0.890 AUROC on Mintaka) is close to the trained judge there |

What these numbers are not: they are not rates of false answers (the reviewers judge whether the quote says it), the reviewers are language models, most rows come from design data, and the page can be out of date (August 2025 snapshot).
Every plan and prediction is written before the run and dated in `docs/` (`S42_CLAIM_AUDIT_AND_PLAN.md`, `S43_LONGFORM_AND_AMBIGUITY_PLAN.md`, `S48` to `S51`); failed predictions are marked as failed.
`tool/` is the system as a local service and an MCP server with three tools: `quote_or_quiet` (short questions), `quote_or_quiet_bio` (a person's claims, each quoted) and `quote_or_quiet_readings` (names with several readings); see `tool/README.md`.

## Layout
- `paper/` manuscript draft, figures and the figure script.
- `vkg/` pipeline code: evidence, readers, the gate (`l3_verify.py`, `l3_checks2.py`), judge and metrics.
- `results/runs/` scripts and written results per stage: `s19` frozen system, `s21` transfer test, `s22` adjudication and coverage variants, `s23` independent retrieval and baselines, `s24` synthetic closed-evidence benchmark, `s25` stronger veto, `l3` and `l3cert` entity slot and certificates.
- `docs/` protocols, freeze records, results, literature notes, plans. Start with `docs/POSITIONING_AND_PLAN.md`, `docs/SCORECARD.md`, `docs/REPRODUCE.md`.

## Reproducing
See `docs/REPRODUCE.md`. The synthetic benchmark (generator, seeds, hashes, generated sets) is fully included; the real-benchmark runs depend on third-party questions and live web results, so run records that contain them are not in this repository.

## Status and limitations
Research code and a paper draft, not a product. One real benchmark carries the 1% result, from a single run, graded by a language model whose false-credit rate was measured on human labels. The second real benchmark needs new sealed questions (docs/SEALED_SET_DESIGN.md). Comparison with calibrated-cascade methods in the literature is in different risk regimes and has not been run on the same data (docs/RELATED_WORK_2026-11-09.md).

## Licence and data
Code: MIT (see `LICENSE`). Paper text and documentation: CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/). Third-party benchmark items and web page text are not redistributed, and the terms of the benchmarks and models used remain their own. See docs/AVAILABILITY_DRAFT.md.
