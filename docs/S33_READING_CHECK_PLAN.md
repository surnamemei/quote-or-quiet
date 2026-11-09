# S33: model-based reading check for same-name subjects (plan, 2026-11-09, before any model call)

S32 showed that a title index can find subjects with several same-name pages, but cannot tell whether the question is really ambiguous. S33 asks a model.

Candidates: releases whose subject has at least one other page of at least 3,000 characters (S32 variant A flag; subject and page list from the frozen S32 functions).
Check: Phi-4 (a different model family from the 4B readers), temperature 0, one call per candidate. The prompt shows the question and up to 8 pages of the subject (longest first, the page the answer was verified in always included), each as title plus the first 200 characters of its pinned text, and asks: which page the question is about, or AMBIGUOUS if a careful reader could not tell which one is meant. Output parsed as a page number or AMBIGUOUS. The proposed answer is not shown (the check is about the question, not the answer).
Rule R: withhold (Unresolved) if the model says AMBIGUOUS. (A page choice is logged; using it to qualify the answer is a later step.)
Design: the design sets of S30-S32 (frozen releases plus the S31 cell). Test, once, after freezing: the frozen releases on FRESH-5, Mintaka test and PopQA test, with the S32 pass rule: at least 5 withheld, at least 20% of withheld gold-wrong, at most 5% of gold-correct releases withheld.
Resources: a separate Ollama instance (port 11536, one model, context 4,096, parallel 1) beside the sealed run; started only with at least 20 GB VRAM free; a watchdog stops it if free VRAM falls below 6 GB, so the sealed run always has priority.

Design iteration 2 (after the first design run: 83 of 115 called AMBIGUOUS, 17% of correct releases withheld, 6% of withheld wrong): the S32 subject is often a part of a longer name, so none of the listed pages is the real subject, and the prompt pushed towards AMBIGUOUS. Added a NONE reply (the question is about something not listed; the answer is kept) and the instruction to reply AMBIGUOUS only when two or more pages fit equally well; generation limit 6 tokens.
