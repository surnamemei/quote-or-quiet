# S24: closed-evidence benchmark with exact gold (spec, 2026-11-09)

Purpose (docs/GENERALITY_PLAN.md, step 2a). Existing benchmarks have noisy gold (Mintaka: 19 of 28 graded errors were gold problems), so
gold-relative SER mixes system and benchmark. Here the evidence is a corpus of invented people and organisations; gold is computed from
the generator's own facts. Parametric memory cannot help, namesakes and unanswerable questions are built in, and no adjudication is
needed. Limits: synthetic text is easier and more regular than Wikipedia, so this tests the verification machinery (span gate, entity
slot, derivation certificates, abstention), not natural-language difficulty.

## Item types and expected output state
| type | share | example | expected state | a definite answer when expected is not Verified or Derived |
|---|---|---|---|---|
| lookup_unique | 28% | birth city of a unique name | Verified | n/a |
| lookup_qualified | 14% | "the linguist X" with a namesake economist | Verified | n/a |
| lookup_ambiguous | 10% | "X" with two namesakes | Qualified (names the entity) | silent error |
| compute_age | 16% | age when they joined an organisation | Derived (certificate) or Verified | n/a (gold = year difference or one less) |
| unanswerable | 16% | doctoral supervisor, never stated | Unresolved | silent error |
| tenure | 16% | director of an organisation in a given year | Verified | n/a |

## Outcomes per item (all exact)
correct Verified/Derived; wrong Verified/Derived (silent error); Qualified with the right entity; definite answer on an ambiguous or
unanswerable item (silent error); Unresolved on an answerable item (lost coverage). The output-level L2 quantity is wrong definite
answers over all items.

## Protocol
1. Generator: results/runs/s24/gen_closed.py; its SHA-256 and those of items and docs are written next to each set.
2. DEV set: closed_dev, seed 101, 200 items, 248 documents (generated, inspected on four samples). Harness bugs are fixed on DEV only.
3. System variant for this corpus (declared now): evidence = the question's top documents from a BM25 index over docs.jsonl (no web);
   Qwen3-4B plain and cautious readers on that evidence give the candidates; release needs agreement of the readers (the support
   rule with two sources of passage instead of three), the verbatim span gate V1 to V5 against the retrieved document, the entity
   slot, derivation certificates for computed answers, and the Phi-4 veto. This is a different configuration from the frozen S19
   system (no web source), so it is reported as the cross-corpus axis, not as the frozen system.
4. Test set: after the DEV harness works and its rules are written, hash the harness, generate closed_test with a new seed (202) and
   1,500 items, and run once. Pre-declared prediction: answers judged wrong at most 0.91% of released answers (docs/GENERALITY_STEP1.md P1);
   no answer to ambiguous or unanswerable items beyond the output-level allowance (k <= 6 of 1,500 items).
5. Everything on the test set is reported, pass or fail.

## DEV harness development (2026-11-09; design data; closed_dev, 200 items)
Four DEV iterations, kept as results/runs/s24/closed_dev_score_v1.md, _v2, _v4 (v3 not saved separately):
| version | change | silent errors | completion (correct Verified/Derived + Qualified-ok) |
|---|---|---|---|
| v1 | span gate + entity slot, no Qualified list, no certificates | 0 | 83 (41.5%) |
| v2 | per-entity Qualified list for namesakes, Phi-4 derivation specs + certificates | 0 | 89 (44.5%) |
| v3 | derivation prompt asks for short quotes (a planned per-entity question rewrite was not applied: the edit failed silently, so per-entity readers see the original question) | 0 | 91 (45.5%) |
| v4 | generator: joining event has a full date, gold = exact age (the earlier year-only items had an ambiguous true age); derivation prompt: the date alone is a valid quote | 0 | 112 (56.0%) |
v4 by item type (n = 200): lookup_unique and lookup_qualified 75 of 84 correct Verified, 9 lost; compute_age 32 of 32 Derived and correct;
unanswerable 32 of 32 correctly Unresolved; namesake 5 of 20 Qualified-ok, 15 lost (single-document cautious readers often answer "unknown");
tenure 0 of 32 (the 4B reasons "year inside an interval" wrongly; the gate refuses those answers, so none is released).
Silent errors 0 of 200 (97.5% upper bound 1.83% at this n).

## Freeze and predictions for closed_test (written before the test set is generated)
Frozen: closed_run.py (gen and score), gen_closed.py, l3cert/cert.py, vkg/l3_checks2.py, vkg/l3_verify.py, vkg/lite.py; hashes in
results/runs/s24/hashes_freeze.txt. Test set: seed 202, 1,500 items, generated once, not inspected; the system runs once.
Output-level L2 rule: silent errors k <= 6 of 1,500 (corrected 97.5% upper bound 0.959%) and coverage (definite answers: Verified, Derived,
Qualified) >= 35%.
Predictions (prior probability): k <= 6 and L2 met (0.65); no wrong Verified or Derived answer on an expected-Verified or Derived item
(0.55); completion between 50% and 62% (0.7); compute_age at least 85% correct Derived (0.75); tenure at most 20% correct (0.8);
namesake Qualified-ok between 10% and 40% (0.6).

Correction (2026-11-09): the frozen harness has no per-entity question rewriting; the namesake lists are built from the original question on each document alone.

## Configuration B: reader-role swap (2026-11-09)
Question: do the system rules transfer when other models play the roles? B = Phi-4 as the plain and cautious readers (instead of the 4B), Qwen3.8-27B
as the veto (instead of Phi-4); retrieval, gate, entity slot, certificates (specifications still from Phi-4) and scoring are imported unchanged
from closed_run.py (closed_run_alt.py). DEV check (closed_dev, 200 items, not used to change anything): 0 silent errors, completion 112 (56.0%);
tenure 0 of 32, compute 32 of 32, namesake Qualified-ok 8 of 20, lookup 72 of 84 correct Verified.
Frozen files: closed_run.py and its dependencies as in hashes_freeze.txt, plus closed_run_alt.py and run_closed_alt.sh (hashes appended there).
Test set closed_test2: seed 303, 1,500 items, generated once, not inspected; run once.
Predictions for configuration B, written before the set is generated (prior probability): output-level L2 met, k <= 6 of 1,500 and coverage >= 35% (0.7);
no wrong Verified or Derived answer (0.55); completion between 45% and 65% (0.7); completion within 8 points of configuration A's 54.2% (0.65);
compute_age at least 85% correct Derived (0.8); tenure at most 20% correct (0.85); namesake Qualified-ok between 10% and 45% (0.7).
