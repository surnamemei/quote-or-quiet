# S24 closed-evidence test result (2026-11-09; sealed set closed_test, 1,500 items, single run; synthetic corpus)

Frozen harness (hashes verified after the run: results/runs/s24/hashes_freeze.txt), docs/CLOSED_EVIDENCE_SPEC.md. Raw: results/runs/s24/closed_test_score.md.

| expected state | n | correct answer | lost (abstained) | wrong definite answer |
|---|---|---|---|---|
| Verified: single or qualified lookup | 630 | 528 | 102 | 0 |
| Verified: tenure ("who directed X in year Y") | 240 | 12 | 228 | 0 |
| Derived: age at a stated date | 240 | 217 | 23 | 0 |
| Qualified: namesake, entity list | 150 | 56 | 94 | 0 |
| Unresolved: fact not in any document | 240 | 240 correct abstentions | 0 | 0 |
| all | 1,500 | 813 (54.2%) | 447 | **0** |

L2 rule (k <= 6 of 1,500 silent errors, coverage >= 35%): **met**. k = 0, corrected 97.5% upper bound 0.246%; coverage of definite answers
(Verified, Derived, Qualified) 813 of 1,500 = 54.2%.

Predictions written before the test (docs/CLOSED_EVIDENCE_SPEC.md): all six held. L2 met (p 0.65); no wrong Verified/Derived answer (0.55); completion 54.2%,
inside 50 to 62% (0.7); compute_age 217 of 240 = 90.4% >= 85% (0.75); tenure 12 of 240 = 5% <= 20% (0.8); namesake Qualified-ok 56 of 150 = 37.3%,
inside 10 to 40% (0.6).

Reading. On a corpus with exact gold and no benchmark noise, the gate, the entity slot, the per-entity Qualified list and the derivation
certificates produced no wrong definite answer in 1,500 items, including 240 questions with no answer in the corpus and 150 namesake
questions. All remaining loss is lost coverage: the 4B reader fails the interval reasoning of tenure questions (95% abstained), and the
cautious readers and the veto often answer "unknown" for one of two namesake entities (63% of namesake items lost) or for a plain lookup (16%).
Limits: synthetic, regular text with invented names, no web source; the system configuration differs from the frozen S19 system (two reader
prompts instead of three sources); the DEV iterations that shaped the harness were on closed_dev only.
