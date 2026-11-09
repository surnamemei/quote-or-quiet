# S5 / S6 feasibility study (read-only, 2026-11-05)

Status tags: **VERIFIED** = I ran it or opened the page/file myself in this study; **UNVERIFIED** = from memory, inference, or a summarised fetch that I could not check at source; **ESTIMATE** = my arithmetic or guess, not measured.
Nothing was installed, no process was started or stopped, no LLM was loaded. The only model request was one `/api/embed` call to `qwen3-embedding:0.6b`.
Web pages were fetched through a summarising step (WebFetch), so GitHub file contents below are summaries of the files, not verbatim reads.

## 0. Headline findings
1. **The Python environment cannot run any GPU work today.** torch is `2.14.0+cpu` (CUDA None, empty arch list). peft, trl, bitsandbytes, vllm, llama-cpp-python are all absent. (VERIFIED)
2. **Hidden states are not available through Ollama.** `/api/embed` returns one pooled, L2-normalised vector per input; `/api/chat` exposes logprobs (and documents `top_logprobs`) but no activations. (VERIFIED for embed and for the repo's logprob use; docs page for top_logprobs VERIFIED by fetch, never called on the 27B.)
3. **No Qwen3.8 model smaller than 27B exists on the hub.** Qwen3.8 = {27B, Flash-Next, 2.4T-A95B}. The same-architecture smaller models are Qwen3.5-{0.8B, 2B, 4B, 9B}. (VERIFIED)
4. **27B in 4-bit is feasible on paper (about 19-21 GB) but only with Ollama's 27B and the embedder unloaded** (the GPU currently holds 28.2 of 32.6 GB), and only after installing a CUDA torch build. Not a first step.
5. **S6's cited code is not directly reusable**: no licence file found, Linux/Slurm/vLLM-only dependency pins, trained on MedMCQA/GSM8K/MATH (not open-ended factual QA), reward is exact match with IDK = 0.
6. **The label problem dominates S5**: 31 positives of 500 (greedy). The existing 9-answer data give 84 questions with at least one correct answer, and that is the best graded label that costs no new generation.

## 1. Installed software (VERIFIED: `importlib.metadata` and `pip list`, Python 3.13.9 at D:\ANACONDA)
| package | state |
|---|---|
| torch | **2.14.0+cpu**; `torch.version.cuda` = None, `torch.cuda.get_arch_list()` = [], `torch.backends.cuda.is_built()` = False. No sm_120 support in this build. |
| transformers | 5.17.0 (module `transformers.models.qwen3_5` present, VERIFIED by `find_spec`) |
| accelerate 1.15.0, safetensors 0.8.0, tokenizers 0.23.2, huggingface-hub 1.32.0, datasets 5.0.1, scikit-learn 1.7.2, numpy 2.3.5, scipy 1.16.3, onnxruntime 1.31.0 | installed |
| peft, trl, bitsandbytes, vllm, llama-cpp-python, flash-attn, flash-linear-attention (`fla`), causal-conv1d, triton / triton-windows, sentence-transformers, xgboost, unsloth | **not installed** |
| Incident | A first multi-import check crashed with `OMP Error #15` (duplicate `libiomp5md.dll`, two OpenMP runtimes linked). `import torch` alone worked when I set `KMP_DUPLICATE_LIB_OK=TRUE` for that one process. The variable is documented as unsafe; a clean venv avoids it. |

Install targets that exist (VERIFIED by metadata queries only, nothing downloaded): `torch-2.14.0+cu130-cp313-cp313-win_amd64.whl` on download.pytorch.org (also cu128 wheels up to 2.11); `bitsandbytes 0.50.2` has a `win_amd64` wheel on PyPI; `peft 0.21.2`; `trl 1.17.1` (requires transformers >= 4.56.2, accelerate >= 1.11, torch >= 2.6). Whether bitsandbytes 0.50.2 runs its 4-bit kernels on sm_120, and whether peft/trl 1.17 accept transformers 5.17 with the Qwen3.5 architecture, are **UNVERIFIED**. The CUDA 13 wheel carries sm_120 kernels in principle (Blackwell needs CUDA >= 12.8), also UNVERIFIED until a smoke test.
Recommendation: build a **separate venv**; do not replace the CPU torch in the shared base environment other jobs may use.

Machine state at check time (VERIFIED): `nvidia-smi` RTX 5090, compute capability 12.0, driver 596.49, **28.2 / 32.6 GB VRAM in use** (Ollama has `qwen3.8-27b` Q5_K_M resident, `size_vram` 19.66 GB, and `qwen3-embedding:0.6b` 5.78 GB). Free physical RAM 3.5 GB of 61.4 GB (instantaneous "free", page cache not counted; other jobs are running). Page files total about 168 GB. Disk: F: 545 GB free.

## 2. Weights available locally and on the hub
**Local (VERIFIED, listing only):**
- `models/qwen3.8-27b-bf16-original/`: 18 safetensors shards, about 55.6 GB (the "52 GB" in GiB), `Qwen3_5ForConditionalGeneration`, model_type `qwen3_5`, text: 64 layers (48 `linear_attention` + 16 `full_attention`, every 4th), hidden 5120, FFN 17408, vocab 248320, untied lm_head, 1 MTP layer, plus a 27-layer vision tower. License file present (hub card says Apache-2.0).
- `models/qwen3.8-27b/Qwen3.8-27B-UD-Q5_K_M.gguf`, 19.77 GB (this is what Ollama serves; it generated every label so far).
- HF caches: `~/.cache/huggingface/hub` holds only `refs` for Qwen3.8-27B (no weights), `gpt2`, and unrelated unsloth repos; `data/hf` holds only datasets (163 MB: SimpleQA Verified, SQuAD2 train+validation parquet, FaithEval unanswerable / inconsistent / counterfactual).
- Ollama tags: qwen3.8-27b, qwen3-vl:8b-instruct (Q4_K_M GGUF), qwen3-embedding:0.6b. GGUFs are unusable for activation extraction here (no llama.cpp bindings; Ollama gives no activations).

**Hub (VERIFIED with `model_info`, metadata only). All Qwen entries are Apache-2.0, ungated:**
| model | params | architecture | BF16 size | note |
|---|---|---|---|---|
| Qwen3.8-27B | 27.78B | qwen3_5 hybrid | 55.6 GB | the studied model |
| Qwen3.8-Flash-Next / 2.4T-A95B | 125B+ MoE / 2.4T MoE | | | out of reach |
| Qwen3.6-27B, Qwen3.5-27B | 27.78B | qwen3_5 | 55.6 GB | older generations, same architecture |
| **Qwen3.5-9B** (+Base) | 9.65B | qwen3_5 (same layer pattern family as the 27B) | 19.3 GB | closest feasible stand-in, fits 32 GB un-quantised |
| **Qwen3.5-4B** (+Base) | 4.66B | qwen3_5 | 9.3 GB | |
| Qwen3.5-2B / 0.8B (+Base) | 2.27B / 0.87B | qwen3_5 | 4.5 / 1.7 GB | 0.8B/2B are the only sizes that fit next to the resident Ollama models |
| Qwen3-14B / 8B / 4B (and -Instruct-2507, -Base) / 1.7B / 0.6B | 14.77 / 8.19 / 4.02 / 2.03 / 0.75B | qwen3 (pure attention) | 29.5 / 16.4 / 8.0 GB ... | mature support in peft/trl/bnb; different generation from the 27B |
| Qwen/SAE-Res-Qwen3.5-27B-W80K-L0_{50,100} | | | | sparse autoencoders for the 27B's predecessor (Qwen3.5-27B), exist on the hub; not checked further |

"Same family" caveat: Qwen3.8 has no small members; Qwen3.5 shares the `qwen3_5` architecture but a different training run and knowledge. A probe trained on Qwen3.5-9B tells us about Qwen3.5-9B's own knowledge boundary, not the 27B's.

## 3. Ollama: hidden states and logprobs (this build 0.34.4, VERIFIED version via `/api/version`)
- **Hidden states: no.** One request: `POST /api/embed {"model":"qwen3-embedding:0.6b","input":"hi"}` returned keys `model, embeddings, total_duration, load_duration, prompt_eval_count`; one vector of **dimension 1024, L2 norm 1.0000001**. It is a pooled, normalised output of a dedicated embedding model, not an intermediate layer, and not the 27B. Documentation pages for `/api/chat` (docs.ollama.com) and the older `api.md` mention no hidden states.
- **Logprobs: yes on `/api/chat`.** The docs.ollama.com chat page (fetched) lists request fields `logprobs` (bool) and `top_logprobs` (int), and response `logprobs[]` entries with `token`, `logprob`, `bytes`, `top_logprobs`. `vkg/signals.py` sets `payload["logprobs"] = True` with `format: "json"`, `think: false`, reads `d["logprobs"]`, and `lp_summary` aggregates token log-probabilities over the answer span; all 500 records in `results/runs/s3_signals_raw.jsonl` carry an `lp` dict (VERIFIED by reading the file). `top_logprobs` was never used by the project and I did not call it (UNVERIFIED on this build). The older `docs/api.md` on the main branch does not list these fields, so it is stale.
- Consequence: a "probe" through Ollama is limited to (a) token logprobs / entropy of the answer (already tested in S3: AUROC 0.689 on test, 0.714 pooled), (b) top-k logprob entropy if `top_logprobs` works, (c) a frozen external embedding of question and answer (Section 5 baseline).

## 4. Memory arithmetic for the 27B in 4-bit (bitsandbytes NF4, transformers)
Parameter budget (from config): embeddings 248320 x 5120 = 1.27B; untied lm_head 1.27B; vision tower about 0.4-0.5B; remaining LM body (including MTP) about 24.8B.
| item | GB (ESTIMATE) |
|---|---|
| LM body in NF4 (0.5 B/param + about 0.03 for quantisation constants) | 13 |
| embeddings + lm_head, kept BF16 (bnb does not quantise them by default) | 5.1 |
| vision tower, BF16 (avoidable if a text-only class loads, UNVERIFIED) | 0.9 |
| CUDA context, buffers | 0.7 |
| activations for batch 8 x 300 tokens, forward only, plus 65 hidden-state tensors kept | < 1 |
| **Total, extraction** | **about 19-21 GB** |
| QLoRA training add-on (LoRA r=16 all linears about 0.25B params with fp32 optimiser state, gradient checkpointing, seq 512, batch 1-2) | + 4-7 GB, so about 25-28 GB |

Fits 32.6 GB **only if Ollama's two resident models (25.4 GB) are unloaded**. Today 4.4 GB of VRAM is free.
RAM: safetensors shards are 2-4 GB each; with `low_cpu_mem_usage` the loader reads shard by shard and quantises on the GPU, so peak process RAM should be about 5-10 GB, but the 55.6 GB file read fills the Windows file cache and will evict the other jobs' mmapped models (slows them, may stall Ollama). BF16 27B (55.6 GB) cannot be loaded: 55.6 GB > 32.6 GB VRAM and leaves about 5 GB of 62 GB RAM, so that is excluded (ROADMAP S8 already says not unattended).
Risks, in order of seriousness:
1. No CUDA torch yet; bnb Blackwell 4-bit kernels on Windows untested here (UNVERIFIED).
2. Gated DeltaNet layers (48 of 64) need `flash-linear-attention` + `causal-conv1d` for speed; neither is installed, and both need triton (not available on Windows without the `triton-windows` fork). Without them transformers falls back to a pure-torch path (UNVERIFIED for 5.17) that is much slower; short prompts (under 300 tokens) make this tolerable for extraction but not for generation or RL.
3. NF4 weights differ from the Q5_K_M weights that produced the stored answers; hidden states are those of a third, related model.
4. Shared GPU: another job's OOM or Ollama reloading the 27B mid-run would crash one of the two.
5. Page-cache pressure / commit charge: the machine has 3.5 GB free RAM right now.
**Safe fallback:** Qwen3.5-9B in BF16 (19.3 GB; about 22 GB with activations, still needs Ollama's 27B unloaded) or Qwen3.5-4B (9.3 GB; still does not fit beside 25.4 GB of resident Ollama models). Anything above about 4 GB cannot coexist with the current Ollama residents. Qwen3.5-2B (4.5 GB) is marginal; Qwen3.5-0.8B (1.7 GB) fits and is the right smoke-test model.

## 5. S5 probe study design
**Question.** Does a linear probe on hidden states predict (i) answer correctness and (ii) context-answerability better than the sampling / logprob / external-embedding signals, **out of distribution**?

**Models (in order).**
- M0 smoke test: Qwen3.5-0.8B (checks CUDA, sm_120, hybrid-attention fallback, hidden-state hooks).
- M1 primary: **Qwen3.5-9B** BF16 (or -4B), own-answer labels generated by M1 itself with HF `generate` (greedy, same JSON prompt as `vkg/signals.py`).
- M2 optional, only after M1 shows signal: Qwen3.8-27B NF4 with the **stored Q5 greedy answers teacher-forced** (labels come from the Q5 model; label-model mismatch stated).

**Datasets and labels.**
| set | source | label | n | notes |
|---|---|---|---|---|
| A. closed-book facts | SimpleQA Verified, the 500-question pool in `s3_pool.json` (250 cal / 250 test, disjoint from the 300 forbidden ids by construction: `forbidden = Random(3000).sample(range(1000),300)`, assert in code) + the 200 remaining non-test ids (700 - 500) as extra | (a) greedy correct (`grade_v3`): 31 positives of 500, too few; (b) **knownness** = at least 1 of the 9 stored answers correct: **84 of 500 positive** (counts: 0 correct 416, 1: 31, 2: 18, 3: 11, 4: 2, 5: 5, 6: 1, 7: 2, 8: 1, 9: 13; VERIFIED by running `grade_v3` over `s3_signals_raw.jsonl`); at least 3 of 9: 35; at least 5 of 9: 22 | 500 (+200) | for M1 the labels must be regenerated with M1 (the 27B counts do not transfer) |
| B. context answerability, in distribution | SQuAD2 **train** parquet (cached locally, VERIFIED) for training; SQuAD2 validation minus every id used in the s0 / s1000 / s2000 runs for test | has_answer vs unanswerable (model-independent) | train 4000 balanced, test 1000 | the 150+150 items of each frozen seed stay untouched for S6 |
| C. context answerability, OOD | FaithEval unanswerable (negative) vs FaithEval counterfactual (positive: answer derivable from the altered context); both cached locally. FaithEval has no answerable split of its own and no train split, so it is test-only | answerability from context | 1000 + 1000 | style differs from SQuAD2; this is the shift |
| D. cross-task | probe trained on A, scored on B and C; probe trained on B, scored on C and A | | | tests whether the direction is "I do not know" or "dataset style" |

**Extraction.** Residual stream (hidden_states output) at every layer for M1 (all 33; 4096 x 2 B each, negligible), every 4th layer for M2. Positions: (P1) last prompt token before generation (SEP "token before generation" recipe); (P2) last token of the teacher-forced answer; (P3) mean over answer tokens. Layers 40-75% of depth are the prior; the layer is **selected by 5-fold CV inside the training data only**.
**Classifier.** Standardised L2 logistic regression (C from CV), plus difference-of-means as a sanity check. No MLP (sample size). One probe per (layer, position) with a fixed grid, reported in full, with the selection rule written beforehand.
**Splits.** A: train on `cal` (250) and test on `test` (250) exactly as S3 (so AUROC is comparable to its numbers: sc_emb 0.750 [0.642, 0.848], combo_lr 0.795 on test), plus pooled 5-fold stratified CV with all folds inside the pool. Nothing from the 300 forbidden ids is read, embedded or scored; the code asserts empty intersection with `Random(3000).sample(range(1000),300)`.
**Controls (artifact guard, section 1 item 6 of the ROADMAP).**
1. Logistic regression on the frozen `qwen3-embedding:0.6b` embedding of the question text only (needs about 700 + 2000 tiny `/api/embed` calls, no new software). If this matches the hidden-state probe, the probe is reading topic or entity popularity, not self-knowledge.
2. Lexical baselines for B and C: question-passage token overlap, passage length, bag-of-words LR (RINSE, arXiv 2609.37469, shows overlap and position leak sufficiency labels).
3. Randomly initialised network of the same shape, and label-shuffled probe (AUROC must be 0.5).
4. The S3 signals (sc_emb, logprob, b1_status, combo_lr) on the same questions.
**Metrics.** AUROC with 2000-sample bootstrap CI; risk-coverage and precision at coverage 2%, 5%, 10%, 15% with Clopper-Pearson bounds; the S3 pass criterion (precision >= 30% at coverage >= 2% with lower bound above the base rate, threshold set on `cal`); for B/C accuracy and AUROC.
**Power note (ESTIMATE, Hanley-McNeil).** With 31 positives vs 469 negatives at AUROC 0.8 the 95% CI half-width is about 0.095; with 84 vs 416 it is about 0.06. So A alone can only detect large differences; B and C (model-independent, thousands of labels) carry the OOD test.
**Pass / fail rule (written now, before any run).**
- PASS (worth integrating) only if all hold: (1) on C (OOD) the probe AUROC lower 95% bound > 0.60; (2) the probe beats the best non-hidden-state control on C by at least 0.05 AUROC with a paired bootstrap CI excluding 0; (3) on A-test the probe meets the S3 rule (precision >= 30% at >= 2% coverage, lower bound above the base rate) with the layer and threshold fixed on `cal`, or, if there are too few positives, its AUROC beats `sc_emb` by at least 0.05 with CI excluding 0; (4) shuffled-label and random-init probes at 0.5 +/- 0.05.
- FAIL otherwise; then the probe is reported as a dataset-artifact detector and S5 is closed, as the ROADMAP says.
- AUROC above 0.95 on any set triggers an artifact audit (answer style, pairing, length) before any claim.
**Time / GPU (ESTIMATE, not measured).**
| step | M1 = 9B BF16 | M2 = 27B NF4 |
|---|---|---|
| venv + CUDA torch + smoke test | 1-2 h wall, almost no GPU | same |
| generate M1's own greedy answers (700 questions, 1 sample) | 0.1 GPU h | n/a |
| extraction, about 7000 prompts x about 250 tokens = 1.8M tokens, all layers | 0.3-1 GPU h (pure-torch fallback for linear attention is the unknown factor) | 1-3 GPU h plus 15-30 min model load |
| probes + controls | CPU, under 1 h | same |
Total about 1.5-3 h wall for M1; M2 adds half a day of attended work.

## 6. S6: Mystic-Slice/rl-abstention
**Fetched** (page, README, `requirements.txt`, `constants.py`, plus summaries of `train.py`, `rewards.py`, `data.py`; the `LICENSE` raw URL returned **404**, the repo page shows no licence). UNVERIFIED at the level of source lines: the fetch tool summarised files instead of printing them.
- **What it is.** Code for "Rewarding Intellectual Humility" (arXiv 2601.20126): `train.py` (GRPO or SFT), `eval.py`, `rewards.py`, `data.py`, `utils.py`, `constants.py`, `job.sh` (Slurm), `requirements.txt`. 107 commits, 1 star, 3 forks. README is short: install requirements, edit options at the top of `train.py`, submit with `sbatch job.sh`.
- **Models.** `constants.py`: `GRANITE = "ibm-granite/granite-3.3-2b-instruct"`, `QWEN = "qwen/qwen3-4B-Instruct-2507"`. So a Qwen3 4B instruct model was the tested Qwen size.
- **Data.** MedMCQA (A-D plus an extra "I Don't Know" option), GSM8K (number; "I Don't Know" string), Hendrycks MATH (`\boxed{}`; `\text{IDK}`). One user message, no system prompt; output format `<reasoning>...</reasoning><answer>...</answer>`. SFT completions for wrong cases append one of 20 canned IDK phrases (`IDK_PHRASES` in `constants.py`). It contains no open-ended factual QA.
- **Training stack.** TRL `GRPOTrainer` / `SFTTrainer`, PEFT, vLLM in colocate mode (`gpu_memory_utilization 0.5`, sleep mode), bf16, gradient checkpointing, no quantisation. GRPO settings as read: lr 2e-5, 500 steps, per-device batch 8 x grad-accum 64, `num_generations` 8, `max_prompt_length` 256, `max_completion_length` 2048, `scale_rewards` False, `reward_weights` [1, 2]. Summary flagged that `lora_config` appears to be built but never applied (possible bug, UNVERIFIED).
- **Reward (`rewards.py`, as summarised).** `format_reward`: 1.0 if the `<reasoning>`/`<answer>` regex matches, else -1.0. `accuracy_reward`: extract the answer, **+1 correct, 0 IDK, -1 wrong**; IDK detected by exact match to the `idk_answer` or the case-sensitive substring "IDK". So r_abs is hard-coded 0, not a parameter, and correctness is exact match of a letter, number or boxed string.
- **Dependencies.** Pinned to `torch 2.8.0+cu126`, `vllm 0.10.2`, `transformers 4.56.1`, `trl 0.23.0`, `peft 0.17.1`, `xformers`, `ray`, `uvloop`, `cupy-cuda12x`, `nvidia-nccl`, `triton 3.4.0`. **Linux-only; does not install on this Windows box.** Qwen3.5/3.8 architectures are not what those pins were tested on.
- **Licence.** None found: legally all rights reserved. Safe route: reimplement (reward shape is about 20 lines; TRL itself is Apache-2.0) and cite the paper; optionally ask the author.

**Can it be adapted to a LoRA on a Qwen3 model that fits 32 GB? Yes in principle, as a rewrite rather than an adaptation.** Fitting sizes (ESTIMATE): Qwen3-4B-Instruct-2507 BF16 LoRA about 12-16 GB (the exact model the repo already used); Qwen3-8B about 22-27 GB with gradient checkpointing; Qwen3-14B only as 4-bit QLoRA; 27B QLoRA SFT borderline (25-28 GB) and 27B GRPO not possible on this machine (rollouts need vLLM, absent on Windows; HF `generate` with 4-bit and the torch fallback for linear attention is far too slow).
**Exact changes needed.**
1. Platform: new venv with CUDA torch 2.14+cu130, bnb, peft, trl 1.17.1; disable vLLM (`use_vllm=False`, HF `generate` rollouts; compatibility of trl 1.17.1 with transformers 5.17 UNVERIFIED) or run under WSL2 if it exists (not checked).
2. Output schema: replace `<reasoning>/<answer>` with the existing project JSON `{status: answer|unknown|conflict, answer, evidence_quotes}` so `vkg.systems._parse`, `grade_open.grade_v3` and `metrics.py` work unchanged and the held-out runs are comparable with B1/B2. Short outputs (`max_completion_length` 64-128 instead of 2048) make rollouts cheap.
3. Data builder (new, `vkg/s6_data.py`): for each training question draw 8 samples at T=0.8 plus greedy from **the model being trained**, grade with `grade_v3` (no LLM judge), and label **known** (greedy correct and at least 4 of 8 correct), **unknown** (0 of 8), **drop** the middle (Gekhman et al. 2405.05904; Dang et al. 2511.02626 add: mix a small share of already-known items late in training). SFT targets use the model's own correct sampled answer (no new facts injected) or `status=unknown` for unknowns (replace the 20 canned phrases by the schema). Question pool: not SimpleQA (only 700 non-test ids, and S3 used 500); use PopQA / TriviaQA / NQ-open (downloads not made; sizes small, availability UNVERIFIED) with SimpleQA's 200 spare ids as dev only.
4. Evidence-conditioned items: SQuAD2 **train** (answerable with its supporting sentence as the verbatim quote; human-written unanswerable -> `unknown`), PopQA/TriviaQA questions paired with (a) a passage that contains the gold string (answer + quote) and (b) a retrieved or random distractor passage without it (target `unknown`; reward penalises answering), and `closed_conf` style synthetic contradictions from `tasks.build` (target `conflict`). Ratio roughly 40% closed-book, 60% evidence-conditioned.
5. Ternary reward (replace `rewards.py`): R = +1 correct and, if evidence was given, every quote verbatim (`systems._verbatim`) and the answer inside the quotes; -1 wrong, unsupported, or answered when the item is unanswerable; abstention reward **r_abs as a parameter** (grid {0.0, 0.25}); on items labelled unknown or unanswerable, abstaining earns +1 (that is the intended behaviour); on known/answerable items abstaining earns r_abs (0 to 0.25); `conflict` is correct only on contradictory items. Add a small format penalty for unparsable JSON. GRPO with 8 generations, `scale_rewards` False as in the repo, KL via `beta` small.
6. SFT warm start before GRPO (the paper reports open-ended QA needs it): R-Tuning-style SFT on the schema above, LoRA r=16 all linear layers (apply the config!).
7. Evaluation hook: a runner that loads base + adapter in HF and exposes the same `chat()` interface as `vkg.llm`, so `vkg.run` / `vkg.metrics` score trained and base models identically (the evaluation currently talks only to Ollama).

## 7. Comparison models
- **leoleung04/Abstain-R1** (VERIFIED by fetch + `model_info`): 3B (3,397,103,616 BF16 params), architecture `Qwen2ForCausalLM`, **no model card, no licence, no base model stated, no code or paper link**, 14 downloads last month, created 2026-01-03. The size is consistent with Qwen2.5-3B with an untied head (UNVERIFIED inference). The paper (arXiv 2604.17073) context-unanswerable setting differs from our long-tail setting. Usable only as an unmatched zero-shot comparator, and its licence status is unknown.
- Other open-weight abstention-trained checkpoints found by hub search (metadata only, none has a model card or licence): `resistz/{Answer0..100-Abstain100..0}-SymmetricReward-Qwen3-4B` (Qwen3-4B family, 4.41B params, a reward-ratio grid, created 2026-10-05; same base family as the Mystic-Slice code, would give a free comparison across reward mixes if its format can be scored); `mehuldamani/abstain-v1` (Qwen2.5-7B, TRL, card without licence); `emajoch1/qwen2.5-{0.5,1.5,3,7}b-{dora,pissa,lora,adalora}-abstention`; `eeoonn/qwen2.5-3b-bbq-grpo-abstention`; `fsiddiqui2/Qwen2.5-7B-Instruct-HotpotQA-Abstention-CoT-10000`. `metacognitive-behavioral-tuning/Qwen3.5-4B-MBT-R` (Apache-2.0) is **not** an abstention model (metacognition distillation). None of these was evaluated or opened beyond metadata; treat training recipes as unknown.

## 8. S6 step-by-step plan, frozen evaluation, pass rule
**Base model for the trained arm and the control: Qwen3-4B-Instruct-2507** (the model the cited code ran; mature peft/trl support; BF16 8 GB). Optional second size: Qwen3-8B. A Qwen3.5-4B arm only after a smoke test of the hybrid architecture under peft/trl. Results are labelled "do not transfer to the 27B until tested".
| step | what | GPU h (ESTIMATE) |
|---|---|---|
| 0 | venv, CUDA torch, bnb, peft, trl smoke test on Qwen3.5-0.8B; HF-backed `chat()` adapter for `vkg` | 0.5 |
| 1 | known/unknown sampling: about 8000 questions x (8 + 1) answers x about 20 tokens with HF `generate` (no vLLM) on the 4B | 1.5-3 |
| 2 | build SFT + RL sets (closed-book 40%, evidence 60%), dev split from ids that never enter the frozen sets | CPU |
| 3 | SFT LoRA, 8k examples x 2 epochs | 0.5-1 |
| 4 | **control first**: base 4B with B1 and B2_strict prompts on dev and on the frozen sets (this is the matched control; the 27B B2 numbers are not a control for a 4B arm) | 0.3 |
| 5 | GRPO from the SFT adapter, 300-500 steps (8 prompts x 8 generations, completions of 64-128 tokens, passages up to about 400 tokens), r_abs in {0, 0.25}, 2 seeds | 3-8 per run, 12-30 for the grid |
| 6 | dev-only selection of r_abs and checkpoint (SQuAD2 seed 0, FaithEval seed 0, SimpleQA dev ids outside the 300 test ids) | 0.5 |
| 7 | new freeze entry with predictions, then one frozen run of the chosen adapter and the controls | 0.7 |
Core path (steps 0-4, 6-7 plus one GRPO run): about 8-14 GPU h. Full grid: up to about 35 GPU h (ESTIMATE, depends on HF rollout speed).
**Frozen evaluation (same items for every arm, all disjoint from training data; SQuAD2 training uses the train split, FaithEval is never trained on, SimpleQA training uses neither the 300 test ids nor the 500 S3 pool).**
- SQuAD2 seeds 1000 and 2000 (150 answerable + 150 unanswerable each).
- FaithEval seeds 1000 and 2000 (150 unanswerable + 150 inconsistent each).
- SimpleQA-with-retrieval on the 300 test ids (`openworld_simpleqa_rag`, seed 3000); the closed-book SimpleQA run on the same 300 as the abstention-without-evidence check.
- Arms: base + B1; base + **B2_strict** (matched control; note `b2_strict` only changes the prompt when a passage is present, so on closed-book SimpleQA B2 is identical to B1); SFT-only; SFT+GRPO per r_abs; optional unmatched zero-shot comparators (Abstain-R1, resistz Qwen3-4B variants).
- Metrics: strict SER (silent-error rate), yield (strict-correct share), over-abstain, with the project's paired bootstrap CIs (`vkg/metrics.py`).
**Pass rule (written now).** Trained arm vs the base 4B + B2_strict, per family (SQuAD2, FaithEval, SimpleQA-RAG): the paired 95% CI of the strict-SER difference lies entirely below 0 (point estimate at most -2 points) **and** the yield difference has lower CI bound at least -3 points (equal or better yield, small margin). PASS = condition holds in at least 2 of 3 families, and in the third SER is not worse by more than 1 point. Otherwise FAIL: "training does not beat prompting at this scale"; do not scale up (ROADMAP decision rule). Because B2 gives a single operating point, also report the trained arms' risk-coverage points and whether any B2-prompt variant dominates them. Power: each family has 150 answerable items per seed, so yield CIs are about +/- 7 points per seed; pool seeds 1000 and 2000 to 300 per family.

## 9. Ranked recommendation
1. **Do first, no install, no GPU (about half a day):** the zero-cost S5 baselines on existing data. (a) question-text-only logistic regression on `qwen3-embedding:0.6b` embeddings against the 500-pool labels (greedy-correct, and knownness at least 1 of 9: 84 positives), 5-fold CV, with the S3 signals as comparison. This is the artifact floor any hidden-state probe must beat, and it costs about 500 tiny `/api/embed` requests. (b) `top_logprobs`-based entropy test on a handful of prompts, only if the owner approves a call to the 27B.
2. **Ask for one decision before any S5/S6 compute:** permission to create a separate venv (CUDA torch 2.14+cu130, bitsandbytes 0.50.2, peft, trl; a multi-GB download) and a time window when Ollama's 27B and the embedder are unloaded. Smoke-test on Qwen3.5-0.8B (1.7 GB, fits beside Ollama).
3. **S5 on Qwen3.5-9B BF16 (fallback 4B), model-independent labels first** (SQuAD2 answerability, FaithEval OOD) plus own-answer labels on the SimpleQA pool, with the controls of Section 5. Decide on the Section 5 rule; only if it passes, consider the 27B NF4 teacher-forced variant, attended.
4. **S6 as an SFT-first study on Qwen3-4B-Instruct-2507**: own known/unknown split, evidence-conditioned items, schema-compatible JSON, matched B2 control run on the same base before any training, then one GRPO run with r_abs as a parameter. Reimplement the reward; do not run the repo as is.
5. **Do not attempt on this machine:** loading the BF16 27B; any 27B GRPO / RL (no vLLM on Windows, no fast linear-attention kernels, 27B QLoRA SFT is borderline at 25-28 GB); running the repo's `job.sh` or its pinned requirements; installing CUDA torch into the shared base environment; loading any HF model while Ollama's 27B occupies 20 GB of VRAM; using the 27B B2 results as the control for a smaller trained model; treating AUROC near 1.0 on paired-label sets as a result; re-using the 300 forbidden SimpleQA ids or the frozen SQuAD2/FaithEval seeds for training or layer selection.
6. Treat the Abstain-R1 and resistz checkpoints as optional unmatched comparators only (no card, no licence, base model unstated).
