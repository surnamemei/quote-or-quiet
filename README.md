# Quote or Quiet

A small local model that answers with a quote you can check, or stays quiet. (Answers with receipts, or silence.)
On sealed SimpleQA questions it gave a wrong answer for 0.76% of all questions or fewer (97.5% upper bound), at 37% coverage.

Most of what is below is how we measured that, and what we found when we tried to push it further.
(Internal programme name: VKG, Verifiable Knowledge Generation. The paper draft is `paper/manuscript.md`.)

**中文简介：** 目标是让模型别胡说：能联网、能核对来源时才给确定答案，核对不了就明说"无法确认"，而不是让用户每次都要二次确认。这个仓库放的是系统、论文草稿和全部评估记录。结论很克制：在 SimpleQA 封存题上，所有问题里"给出错误答案"的占比上界为 0.76%（覆盖率 37.2%）；换到另外两个基准，覆盖率不够，并且发现那里很多"错误"其实是基准自己的金标准过时或问题有歧义。这不是"消除了幻觉"。

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
No licence has been chosen yet. Third-party benchmark items and web page text are not redistributed. See docs/AVAILABILITY_DRAFT.md.
