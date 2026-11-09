# Revision of the L1 criterion (2026-11-09; written before any S29 sealed result is seen)

## Original criterion (target.txt)
L1: at the same answer coverage and compute budget, the silent-error rate (SER) is at least 50% below a strong baseline, and the yield of correct answers does not fall.

## Why it is revised
1. **It cannot be measured at the error level the system reaches.** S36 (docs/S36_L1_RESULT.md) compared the frozen system with the strongest baseline we have (the same evidence and the same seven generations, released by an agreement score, at exactly matched coverage). Truth-relative errors on FRESH-5, Mintaka test and PopQA test: system 3, baseline 8.0 (point estimate 63% lower), with 9 errors made by only one of the two. To show "at least 50% lower" with 80% power at the observed ratio, about 86 such errors are needed, which at 0.16% per question means about 55,000 questions. The better the system meets L2, the less measurable a relative reduction becomes: near zero, "half" is a difference of a few errors.
2. **"Strong baseline" was not defined.** target.txt lists the raw model, prompting with abstention and standard RAG. The baseline used in S36 is stronger than any of these: it is the system without its gate. That comparison is the right ablation, but it answers a narrower question (does the gate add anything beyond agreement) than the one L1 was meant to answer (is the low error rate due to the method).
3. **Matched coverage plus "yield does not fall" excludes the standard baselines**, which answer far more questions; only a rankable baseline can be matched, which again means the ablation.

The original result is kept and reported: **original L1 not established** (point estimate 63% lower, discordant test p = 0.38, power analysis above).

## Revised criterion
**L1-a, against standard approaches (does the method matter?).** On the S29 sealed set, the frozen system's SER over all questions is lower than that of each standard baseline, each at its own operating point:
- B0 raw model: Qwen3-4B-Instruct-2507, closed book, prompt "Answer the question with a short answer only.\nQuestion: {q}\nAnswer:" (always answers);
- B1 raw model with abstention: closed book, prompt "Answer the question with a short answer only. If you are not sure of the answer, reply exactly: I don't know.\nQuestion: {q}\nAnswer:";
- B2 standard RAG: the 4B plain reader on the combined passage (combo_plain, from the main run);
- B3 RAG with abstention: the 4B cautious reader on the combined passage (combo_cautious).
Closed-book outputs: greedy, 40 tokens, original parser, generated once on the sealed set after the main run (results/runs/s29/run_fsm/wd_closed.jsonl). Errors are gold-relative (the alias-aware judge) for every rule. Test per baseline: one-sided exact McNemar test on per-question silent error (system wrong-and-released vs baseline wrong-and-answered), p < 0.05 after Holm correction over the four baselines. Robustness: the same comparison after multiplying each baseline's errors by the truth-relative share of a blind review of 40 random gold-wrong answers of that baseline (two reviewers, same rubric as S35/S36), and the system's by its own reviewed share.
**L1-b, against the strongest ablation (does the gate cost anything?).** At exactly matched coverage (the S36 edge interpolation), the system is not worse than the agreement-score baseline:
- SER: one-sided 95% upper bound of SER_sys - SER_base below +0.25 percentage points (paired bootstrap over questions, 10,000 draws, seed 0, edge share drawn at random in each replicate), using truth-relative errors from the S36-style blind review of all gold-wrong releases of both rules;
- correct-answer yield: one-sided 95% lower bound of yield_sys - yield_base above -1 percentage point (same bootstrap; correct = released and not a truth-relative error).
Point estimates of both differences are reported.

L1 (revised) holds if L1-a holds for all four baselines and L1-b holds. The original-criterion test on S29 (pre-registered in S36_L1_RESULT.md) is run and reported as well.

## What this changes in the claim
- Claimable if met: the low, bounded error rate comes from the method (much lower than standard approaches), and the deductive gate gives provenance at no cost in errors or yield relative to the strongest ablation.
- Not claimable: that the system halves errors relative to the ablation. The point estimate is reported, with the power analysis, as not established.

## Reference (already-seen data, not evidence for the revised criterion)
On FRESH-5, Mintaka test and PopQA test (S36), L1-b is computed in results/runs/s36/s36_l1b.py for information; only the S29 sealed result counts.
