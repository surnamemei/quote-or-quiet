# S31 result: the two-source pool (2026-11-09; plan in S31_TWOSOURCE_PLAN.md)

Pool: 478 design questions whose candidate has support 2 of 3 (explore 244, held-out 234). Features and pool rows: results/runs/s31/s31_features.py, pool.jsonl.

Explore half, gold-relative wrong rate by feature (selected rows):
- missing source: Wikipedia 224 (26% wrong), web 16 (12%), combined 4 (75%). Almost the whole pool is "the local Wikipedia passage did not give the answer".
- Phi-4 agrees 201 (21%), abstains 24 (58%), differs 19 (42%). Gate passes 69 (17%), refuses 175 (30%).
- question type: YEAR 16 (0%), ANY 110 (14%), NUMBER 20 (25%), NAME 88 (48%). Set: PopQA 78 (53%), Mintaka 36 (31%), SimpleQA 108 (9%), S29 pilot 22 (9%).
- best cell: Phi-4 agrees, the gate passes and the Wikipedia reader abstained: 32 questions, 2 wrong (6.2%). No combination of the allowed features reached 3% with 20 or more questions.

Chosen rule (that best cell), applied once to the held-out half: 23 added, 2 wrong (8.7%, one-sided 97.5% upper bound 28%). Pre-set rule (at least 20 added, at most 3% wrong): **FAIL**. The pool stays closed.

What the wrong answers in the best cell are (explore 6 + held-out 2, read by the author, not adjudicated):
- namesakes: "Who was the screenwriter for Heat?" (1995 film, Michael Mann, against the 1986 film, William Goldman); in S30 also "Dude" and "Some Like It Hot";
- ambiguous questions: "In what country is Norfolk?", "In what country is Marathon?", "What is the religion of Francis?";
- stale or debatable gold: Celtics titles (18 now, gold 17), Ark: Survival Evolved (early access 2015, release 2017), Bush album count;
- one clear wrong answer: Watteau's painting sale (200 livres, gold 60).

Reading: within the pool, the features separate easy from hard (YEAR questions and SimpleQA are mostly right, NAME questions and PopQA mostly wrong), but the remaining errors are dominated by questions that have more than one right answer. Those cannot be removed by a stronger filter; they can only be handled by saying which reading the answer is for. That is the "Qualified" state of Goal A, and the namesake part is detectable without gold: the question's subject maps to more than one page title in the pinned Wikipedia (for example "Heat (1995 film)" and "Heat (1986 film)").
