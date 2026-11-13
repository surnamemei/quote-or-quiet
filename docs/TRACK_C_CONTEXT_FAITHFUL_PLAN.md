# Track C: answering faithfully from material the user provides (plan, 2026-11-12)

Source of the direction: suggestions passed on by the user (written by another assistant), read against the project's actual state. Track C is a new problem, separate from the 16 gates (which measure answers checked against public sources, mainly Wikipedia).

## The distinction
- Public fact checking (gates G1 to G16): is a released answer supported by an outside page that the system finds?
- Context faithfulness (Track C): does an answer reflect the files, text or conversation the user has given? Wikipedia and web search are not used as a substitute for the given material; whether the material is itself true is a separate question.
The progress bar (docs/PROGRESS_TRACKER.md) is a count of met test criteria for the first problem. It is not a percentage of hallucination solved, and it says nothing yet about Track C.

## What can be reused
Span location in a pinned text, source records (title, hash, offsets), number and entity checks, the swapped-answer control, the 27B quote-only judge, the Unresolved state, registration before runs, blind review with decoys. The judge prompt is already "does this sentence state that this answer is the answer to this exact question", which applies to any text, not only Wikipedia.

## Diagnosis first (no new method before it)
1. Run the current tools on given material: the quote check (qoq_v2.check with the page replaced by the user's text) and the plain models, and record failures by type: (1) locating: the answer is in the material and is not found; (2) extracting: right passage, wrong number, entity or condition; (3) misattribution: facts of two people, files, experiments or times mixed; (4) unsupported addition: the material does not say it and the model states it; (5) conflict: the material disagrees with itself and only one side is given; (6) inference: right facts, wrong calculation, condition or cause; (7) final wording: the evidence was right and the final answer adds or changes something; (8) task: part of the question missed or misread.
2. Engineering checks before blaming a model: is the material parsed in full, truncated, mis-encoded or mis-split; are context length and inference settings what they are supposed to be.

## Evaluation (built before the candidate method is tuned)
- Development set first, from material of the kind the user meant: reports, files and multi-turn conversations, long contexts with scattered facts, Chinese questions on English material, numbers, units, dates, names and file names, unanswerable and partly answerable questions, conflicting material, look-alike entities and values, questions needing a simple calculation or explicit inference. Public sets considered for reuse (to be checked for fit before use; downloads under the user's permission): FaithEval (unanswerable, inconsistent and counterfactual contexts), SQuAD 2.0 (unanswerable), RAGTruth (response-level hallucination in RAG), LongBench-style long-document QA, a Chinese reading-comprehension set (e.g. CMRC or DuReader). Not only synthetic items and not only verbatim-copy questions; gold answers and evidence checked, several acceptable answers recorded as such.
- Systems compared on the same items: (1) the model answering directly; (2) the model told to answer only from the material; (3) locating relevant passages, then answering; (4) the candidate: locate, organise evidence with its positions and gaps, answer while separating stated, inferred, missing and conflicting, check entities, numbers, units, conditions and support before output, else Unresolved or a partial answer. The judge used inside (4) is reported, so that a gain from a stronger checker is not credited to the procedure alone.
- Measures, each with numerator, denominator and labelling rule, per type and with uncertainty (questions from the same document or conversation treated as clustered): unsupported or contradicting answers; correct completion of answerable questions; correct recognition of missing information; correct recognition of conflicts; unnecessary refusals and omissions; end-to-end latency and GPU memory.
- The final evaluation is on the user-visible answer, including whether an assistant restates an unverified candidate as fact.
- Development, tuning and a sealed test are kept apart; the sealed test is fixed (system version, items, judging rules) before it runs; failures are kept.

## Models
Measured, not assumed: the models actually deployed. Locally available now: qwen3.8-27b (Q5_K_M GGUF in Ollama), Qwen3-4B-Instruct-2507, Phi-4, Llama 3.1 8B, Gemma 3 12B, Mistral Nemo 12B. The user's deployed models are in E:\InfernixTest (located 2026-11-12) and are served by the user's Infernix runtime (infernix-serve.exe, build windows-2026.11.01; OpenAI Chat Completions and Responses and Anthropic Messages APIs on a local port):
- Qwen3.8-Flash-Next (config: model_type qwen4_exp_text; 48 layers, hidden size 2560; mixture of experts with 512 experts, 10 active per token; hybrid attention, every fourth layer full attention and the others linear attention; 262,144-token context). Artifacts: Uncensored-NVFP4-Infernix (3 parts, 72 GB), NVIDIA-NVFP4-Infernix (.ngram, 49 GB), a DFlash2 drafter (741 MB) for speculative decoding.
- Qwen3.8-27B Uncensored NVFP4 (.ninfer, 23 GB), besides the Q5_K_M GGUF of the 27B in Ollama used so far.
Serving facts from the runtime's own logs and help: the Flash Next engine fills nearly all free GPU memory with an expert cache and keeps about 22 GB of experts in system RAM, so it runs alone on the GPU (under the project lock, never beside the 4B server, Ollama models or the user's own Infernix session); its default fast paths make a request's output depend on the requests running beside it, so Track C runs use --reproducible (same bits on every run of the build), one request at a time, temperature 0, and record the flags, the artifact, the context limit (--max-context) and the speculative-decoding setting. Memory and latency are logged per run. Which artifact and settings the user actually uses day to day is asked before the sealed test. Architecture claims (dense, MoE, hybrid) only from the models actually loaded and their results.

## People
AI reviewers are not independent human checks. Disagreements and high-risk cases go to people when available (gate G12's sheet exists); until then, the gap is reported, and random samples (for rates) are kept apart from hard-case samples (for finding failures).

## Order
After the running jobs (G4 second test S68, cross-family check S69) and the tool v2 self-test: C1 diagnosis on a small development set (CPU and GPU, a day); C2 evaluation set and baselines 1 to 3; C3 candidate system; C4 sealed test. The related-work check for a paper on this track comes after results are stable.

## Revised order after a second set of suggestions (2026-11-12)
The aim stays a measured reduction of each failure type with the external check kept as the last guard; no single switch is expected to remove all of them.
- C1 Evidence-sensitivity suite (first; mostly CPU to build): for one question, controlled versions of the material whose correct behaviour is known by construction: (A) original evidence; (B) the key value replaced by another of the same type; (C) the answer sentence removed (the answer is not stated); (D) two records with different values (conflict); (E) a look-alike entity with another value added (binding). Each version also at different positions and lengths of a long context (filler from unrelated pages), and with the question in Chinese for English material. Scoring is mechanical (which candidate value the answer contains; whether it says not stated or conflicting), so no judge is needed and the same judge is never both labeller and scorer. It tells apart the causes: input lost (parsing, truncation), not located, overridden by prior knowledge (B fails while A passes), binding (E), guessing when absent (C), conflict (D), position (length and position).
- C2 Baselines on the suite and on real-style material: direct answer; told to answer only from the material; locate then answer; the existing quote check as a filter. Models: the user's Flash Next and 27B through Infernix (reproducible route), plus the local 4B.
- C3 Training, only after C1 shows which failures dominate: a replication of a published context-faithfulness method (to be checked at the original source before use; claims by assistants about papers are not taken as given), then training data aimed at the observed failures, with negatives taken from the model's own real errors. Trainable weights: the project has trained LoRA adapters on the 4B; a bf16 copy of the 27B exists locally (models/qwen3.8-27b-bf16-original), so QLoRA on the 27B is to be tested for fit; the Infernix formats (NVFP4) are for inference and Flash Next has no trainable weights here, so it is evaluated, not trained. Every trained model is tested on unseen topics, with general ability checked for loss.
- C4 Decoding-time interventions (context-weighted decoding, attention-based) on models run under transformers (4B, 27B bf16), since Infernix exposes a chat interface only.
- C5 Mechanism study (optional, for a paper): paired inputs differing in one value, locating where the evidence is lost.
- C6 Sealed test of the final combination (model plus the external check), fixed before it runs.

Note (2026-11-12): D:\Models holds Flash Next add-ons only (a BF16 vision projector, an incomplete second projector, and a multi-token-prediction draft head in Q2 GGUF with its tensors); no full Flash Next weights in a trainable format were found on E: or D:, so Flash Next stays evaluation-only.

Note (2026-11-12): E:\Models\models holds NVIDIA's FP4 checkpoint of Flash Next in safetensors (nvidia--Qwen3.8-Flash-Next-FP4-Local: 102 GB, 375,487 tensors, ModelOpt mixed precision) and a 120 GB NVFP4 repack (Strata). This is the only standard-format copy; at 102 GB in 4-bit form it is about three times the GPU memory, so fine-tuning it locally is not practical: Flash Next stays evaluation-only. infernix-serve offers --greedy, --top-k and --logits-dtype but its help lists no option to return token log-probabilities; whether its API accepts a logprobs parameter is to be tested when it runs, which decides whether decoding-time interventions (C4) can use Flash Next.

## Decisions by the user (2026-11-12)
- Daily models: the Infernix builds. Track C's primary models are Flash Next Uncensored-NVFP4-Infernix (with the DFlash2 drafter, as the user runs it) and the 27B Uncensored-NVFP4 (.ninfer), served by infernix-serve with --reproducible; the Ollama Q5 GGUF of the 27B and the 4B are comparisons.
- No people available for review. Alternatives, none counted as human review: (1) gold by construction wherever possible (the C1 suite needs no reviewer); (2) agreement of the project's reviewer protocol and the 27B judge with existing human labels in public datasets (claim support: FEVER, VitaminC, an attribution benchmark with human labels; answerability: SQuAD 2.0), reported as a separate measurement; (3) reviewers of other model families (S69). Gate G12 stays open and is reported as open.

## C1, first run and a construction error (2026-11-12)
Suite v1 (results/runs/s70/esuite_build.py) took, for each question, any sentence of the subject's page that contains the gold string. Run on the 27B (Ollama, material-only prompt; 2,718 prompts, ESUITE_esuite_result.md): missing answers were handled almost perfectly (599 of 600 'not stated'), but 30 to 50% of answerable items were answered 'not stated'. Inspection showed the suite was at fault: many base sentences contain the answer string without stating the answer to the question (a sentence saying who directed a film, for a question about the screenwriter) or refer to the subject only as 'it' or 'the EP', with no title given. v1 is kept as a failed design and is not used to describe the model.
Suite v2 (esuite_build_v2.py): base sentences are G14 witness quotes that both reviewers judged to state the answer to the question, and every record carries its page title ('[Broken (EP)] The EP was produced by ...'), as a document's heading would; 200 base items, 2,763 prompts. The Infernix run that had started on v1 was stopped before any request was sent.

## C1 v2 on the 27B (Ollama Q5, material-only prompt; 2026-11-12, results/runs/s70/ESUITE_esuite_v2_result.md)
Correct by version (short English / short Chinese question / long context): A original 98% / 90% / 89%; B value replaced 80% / 66% / 81% (errors mostly 'not stated', some other values); C answer removed, 'not stated' required 97% / 98% / 100%; D conflict 98% / 97% / 96%; E look-alike 63% / 67% / 90%.
E was found to be built badly after the count: the distractor sentence was the original sentence with only the subject's title replaced, so it kept aliases, dates and titles of the original subject ('Entente de Sour El Ghozlane ... known as Guyana women's national field hockey team'), and 'the records conflict', the model's usual reply, is a defensible reading. E is kept in the record but not used to describe binding. Version F replaces it: the distractor is the real stating sentence of another item of the same relation, under its own title (600 prompts added to esuite_v2.jsonl, seed 7002). B is synthetic too (the value replaced inside the original sentence); its drop from A (98% to 80%, 66% with a Chinese question) is the first candidate finding: when the material contradicts what the model knows, it often says the material does not state it. To be confirmed on the Infernix models and on less synthetic material.

Note (2026-11-12 12:5x): infernix-serve answers a request with logprobs=true with the error "logprobs_not_supported" ("Infernix does not provide per-token log probabilities"), so decoding-time interventions (C4) cannot use the Infernix builds; they run on models under transformers (4B, 27B bf16). The first Flash Next C1 attempt failed because the request named the model "default" (the API wants the served name); fixed (the name is read from /v1/models), empty answers are re-asked.

C1 v2, version F on the 27B (Ollama): correct 93% (short English), 91% (short Chinese), 90% (long); the distractor's value was given in 1, 0 and 1 of 200; the remaining errors are 'not stated' replies (11 to 16 of 200). Binding to the right subject is therefore not a weakness of this model on this material; the E failures were the construction. Summary for the 27B (Ollama, material-only prompt): reading given evidence 89 to 98%, refusing to guess when the answer is absent 97 to 100%, reporting conflicts 96 to 98%, binding 90 to 93%; the clear weakness is evidence that contradicts what the model knows (B: 80%, 66% with a Chinese question), mostly answered 'not stated'.

## C1 result: Flash Next on Infernix (2026-11-12, 18:47 to 22:06)
Run through the user's own running infernix-serve (port 12689; their settings: Uncensored-NVFP4, DFlash2 drafter, n-gram volume, int8 KV cache, max concurrency 2), thinking off, one request at a time; no model of mine loaded. Short contexts for both prompts (2,242 each); long contexts for the first 100 base items, material_only only (563). Median 0.6 s per request (material_only), 1.7 s (direct); long prompts about 6 to 10 s. Outputs out_esuite_v2_infernix_flashnext_user_*.jsonl; table in ESUITE_esuite_v2_result.md.

| version (English, short) | material_only | direct (no instruction) |
|---|---|---|
| A original | 99% | 98% |
| B value changed in the material | 89% (13 gave the model's own value) | 40% (115 gave the model's own value) |
| C fact removed (should say not stated) | 96% (7 guessed) | 64% (73 guessed) |
| D two records conflict (give both) | 97% | 98% |
| F real distractor sentence | 96% | 98% |
Long context (material_only, 100 items): A 100%, B 93%, C 100%, D 99%, F 100%.
Chinese questions: the low material_only scores (A 54%, F 56%) are mostly a scoring artefact: the model answers in Chinese (德黑兰 for Tehran, 雅典 for Athens), and the mechanical scorer looks for the English value. Not counted as errors until scored with Chinese value names.
Reading: the main model-level failure is the same as for the 27B, and much larger without an instruction: when the material contradicts what the model knows, Flash Next answers from memory (B direct 58% wrong value) and fills a removed fact from memory (C direct 37% guessed). The material_only instruction removes most of it (B 6.5% wrong value, C 3.5% guessed) but not all. This is the target for C3 (evidence-change training) and C4 (decoding interventions), and the direct column is the baseline a deployed model shows when the user just pastes material.

## C1 result: 27B Uncensored-NVFP4 on Infernix (2026-11-13, 01:09 to 01:52)
My own infernix-serve on port 11951 (--reproducible, --max-context 16384, --vram-headroom-mib 6144: the 10,240 MiB reserve left no room for the KV cache after 21.1 GiB of weights), thinking off, full suite for both prompts (3,363 each). Median 0.1 s (material_only), 0.5 s (direct) per request.

| version (English) | material_only short / long | direct short / long |
|---|---|---|
| A original | 98% / 94% | 99% / 98% |
| B value changed in the material | 80% / 83% (8 / 9 own value; 27 / 17 abstained) | 50% / 63% (99 / 73 own value) |
| C fact removed | 96% / 98% | 50% / 61% (100 / 78 guessed) |
| D conflict | 98% / 95% | 100% / 86% (26 picked one, long) |
| F real distractor | 94% / 95% | see table |
Same pattern as the 27B on Ollama and as Flash Next: with the instruction, the remaining B failures are mostly abstention ('not stated' when the material contradicts the model), not the model's own value; without it, half of the changed-value and removed-fact items are answered from memory.

## C1 summary across the three models (English, short context)
| | B own value, direct | C guessed, direct | B own value, material_only | C guessed, material_only | B abstained, material_only |
|---|---|---|---|---|---|
| Flash Next (Infernix, user's server) | 58% | 37% | 6.5% | 3.5% | 3% |
| 27B NVFP4 (Infernix) | 50% | 50% | 4% | 3.5% | 13.5% |
| 27B (Ollama, Q-quant) | not run | not run | 3% | 3% | 14.5% |
Conclusion for C2 to C4: the model-level failure is real and large when material is pasted without an instruction (half of contradicted or removed facts answered from memory); an instruction cuts it to 3 to 6.5% but trades part of it for abstention on the 27B. The target of C3/C4 is the material_only residue (own value and guesses, 3 to 7%) without raising abstention, and the direct-prompt behaviour.

## C1: Chinese questions rescored with Chinese value names (2026-11-13; results/runs/s70/zh_rescore.py, ESUITE_zh_rescore_result.md)
Chinese labels and aliases for the 226 answer values from Wikidata (zh_names.py: English label search, top hit; 215 of 226 got a name; names of one character not used). Same scoring rule, a value now counts as named in its English form or any Chinese name. Short context, Chinese question, correct before / after:
- Flash Next, material_only: A 54% / 94%, B 75% / 90% (12 own value), C 94% / 94%, D 88% / 97%, F 56% / 92%.
- Flash Next, direct: B 62% / 42% (116 of 200 own value, 58%), C 46% / 44% (112 guessed).
- 27B NVFP4, direct: B 70% / 55% (89 own value, 44.5%), C 46% / 41% (118 guessed); material_only: A 96%, B 76% (37 abstained), C 98%, D 98%, F 92%.
- 27B Ollama, material_only: A 95%, B 66% (61 abstained), C 98%, D 97%, F 92%.
Reading: the low Chinese material_only scores of Flash Next were the scoring artefact; with Chinese names the Chinese-question results match the English ones. The model-level failure is the same in both languages: without an instruction about half of contradicted or removed facts are answered from memory (Flash Next B 58% own value, C 56% guessed; 27B NVFP4 44.5%, 59%), and with the instruction the 27B models abstain on a third of the contradicted items with a Chinese question (B 18.5 to 30.5%), more than with an English one (13.5 to 14.5%). Caveat: a top search hit can be the wrong entity, and a Chinese alias can match more than the value; the rescore can therefore overcount named values a little, in both the correct and the error columns.
