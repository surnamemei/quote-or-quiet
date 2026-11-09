# S31: can the two-source pool be split into right and wrong? (plan, 2026-11-09, written before looking at any feature)

Pool: design-set questions (the same 1,144 as S30) whose max-support candidate has support 2 of 3 sources (478 questions, candidate right 72% by gold).
Split, fixed now: explore half = questions whose sha256(id) ends in an even hex digit; held-out half = odd. Features are looked at, and a rule is chosen, on the explore half only.
Allowed features: deterministic functions of the cached outputs (which source is missing and whether it abstained or gave another answer, how many of the six reader outputs agree, Phi-4 agreement, Wikipedia gate result, question type, set). No gold, no new model calls.
Pass rule, fixed now: the chosen rule, applied once to the held-out half, adds at least 20 releases with gold-relative wrong at most 3% (one-sided). If it fails, the pool stays closed and the finding is reported. One rule only; no second try on the held-out half.
