# S30 result: gate that also accepts pinned web pages (2026-11-09; plan in S30_WEBGATE_PLAN.md)

Design sets, cached outputs (SimpleQA DEV 300 + FRESH 200, Mintaka DEV 200, PopQA DEV 300, S29 pilot 144; 1,144 questions). Script results/runs/s30/s30_webgate.py, table results/runs/s30/s30_webgate.md.

| rule | released | coverage | gold-relative wrong |
|---|---|---|---|
| frozen (Wikipedia gate) | 430 | 0.376 | 15 |
| W(1): also one web domain | 462 | 0.404 | 18 |
| W(2): also two web domains | 454 | 0.397 | 17 |

W(2) adds 24 releases with 2 graded wrong (8.3%). Pre-set rule (at least 20 added, at most 3% wrong): **FAIL**. The variant is rejected and the frozen gate stays.

The two W(2) errors are both namesake titles in PopQA ("Dude": the answer is the composer of the 2025 Tamil film, the gold is the composer of the 1972 musical; "Some Like It Hot": Billy Wilder's 1959 film against a 1939 film). The one extra W(1) error is a real wrong answer (Dominica 2001: Roosevelt Skerrit, who took office in 2004; the gold Pierre Charles is right). With n = 24 the 3% bar could only be met with 0 errors, and the namesake problem is exactly what a second web domain does not solve: both domains describe the more famous entity.

Where the design questions stop (same 1,144 questions, frozen pipeline; "correct" = candidate matches gold):

| stop | n | candidate correct |
|---|---|---|
| released | 430 | 415 (96.5%) |
| only 2 of 3 sources agree | 478 | 346 (72%) |
| no answer | 86 | - |
| only 1 source agrees | 69 | 20 |
| Wikipedia gate refuses | 56 | 53 (95%) |
| Phi-4 disagrees | 25 | 22 |

Reading: the gate is not the main limit on coverage. Even a perfect recovery of every gate refusal would add 4.9 points of coverage; the largest pool is the questions with only two agreeing sources (42% of all questions), where the candidate is wrong 28% of the time, so that pool cannot be released without a much stronger signal. Earlier attempts on this pool (pin plus format gate, independent title retrieval, larger veto, corroboration, trained checker) added errors at 5 to 16%. The next step on coverage would have to separate the right from the wrong answers inside the two-source pool, not loosen the gate.
