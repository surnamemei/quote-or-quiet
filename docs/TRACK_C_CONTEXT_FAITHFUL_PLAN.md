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
Measured, not assumed: the models actually deployed. Locally available now: qwen3.8-27b (Q5_K_M GGUF in Ollama), Qwen3-4B-Instruct-2507, Phi-4, Llama 3.1 8B, Gemma 3 12B, Mistral Nemo 12B. A 'Qwen 3.8 Flash Next' named by the user was not found in the project's model store or under the user's folders (search on 2026-11-12); its location, format and serving setup are needed from the user before it can be included. Architecture claims (dense, MoE, hybrid) only from the models actually loaded and their results.

## People
AI reviewers are not independent human checks. Disagreements and high-risk cases go to people when available (gate G12's sheet exists); until then, the gap is reported, and random samples (for rates) are kept apart from hard-case samples (for finding failures).

## Order
After the running jobs (G4 second test S68, cross-family check S69) and the tool v2 self-test: C1 diagnosis on a small development set (CPU and GPU, a day); C2 evaluation set and baselines 1 to 3; C3 candidate system; C4 sealed test. The related-work check for a paper on this track comes after results are stable.
