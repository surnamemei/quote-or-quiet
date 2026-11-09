# S33 result: Phi-4 reading check (2026-11-09; plan in S33_READING_CHECK_PLAN.md)

Design sets only; no rule reached the bar, so nothing was frozen and the test sets were not run.

| version | candidates | AMBIGUOUS (withheld) | of withheld gold-wrong | correct releases withheld | unparsed |
|---|---|---|---|---|---|
| prompt 1 | 115 | 83 | 5 (6.0%) | 78 (17.2%) | 18 |
| prompt 2 (NONE option, stricter AMBIGUOUS) | 115 | 33 | 2 (6.1%) | 31 (6.8%) | 33 |

Bar (from S32): at least 20% of withheld gold-wrong and at most 5% of correct withheld. Both versions are far from it: the share of wrong answers among withheld (6%) is about the same as among all flagged candidates, so the check does not separate. Phi-4 calls clearly specified questions ambiguous ("the American Major League Baseball catcher" with pages "Major League Baseball" and its video game), and often answers in prose instead of a number (unparsed).

One observation for later, not tested: for "What is Jordan the capital of?" Phi-4 picked the page "Jordan, Guimaras", which is the gold reading, while the verified answer (Amman) is about the country. A mismatch between the page the model picks and the page the answer was verified in may be a better signal than AMBIGUOUS; with one example it is only a lead.

Run beside the sealed run on a separate Ollama instance (port 11536, Phi-4, context 4,096) with a VRAM watchdog; peak use was about 18 GB of 32 GB, the watchdog never fired, and the instance was shut down afterwards.

Reading of S30-S33 together: the frozen system's remaining errors on the design and test sets are mostly questions with more than one right answer. Four approaches to find them without gold (web pages as evidence, deterministic features, a title index, a model reading check) each failed their pre-set bar. These errors are close to the floor that a single-answer benchmark can measure; separating them needs either human adjudication or a question set built to have one answer, which is what the S29 sealed set is.
