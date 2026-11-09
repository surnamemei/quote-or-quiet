# S20 Step B pre-registration: synthetic-page test (written 2026-11-07 17:46, before any model sees a synthetic page)

Plan: docs/S20_PLAN.md section 3. Code: results/runs/s20/synth.py. Pages are already built (synth_items.json); no model output exists yet.

## Design (as built)
- **Items:** 220 correct G3 V1-V5 releases from the used sets (DEV, FRESH, S18, FRESH-5). Each released span is a year (118)
  or a full date (102). The question's relation is in one of 13 families. The page is about the question's entity, since the
  page title occurs in the question. One item per page.
- **Conditions per item (7):** the untouched page (k = 0), and k ∈ {1, 2, 4} inserted sentences next to the true sentence of two kinds:
  - **rel**: same entity (page title), a neighbouring relation, a fresh value in the same format;
  - **ent**: another entity (another item's page title, same family), the same relation, a fresh value.

  Inserted values differ from the gold, from each other and from every string on the page. That gives 1540 passages, each a
  window of about ±1500 characters around the true sentence, headed by the page title.
- **Wording:** the phrase lexicon was written for natural wording. 314 of 880 relation-distractor sentences contain a D3 v1
  competitor trigger of the asked relation, so D3 v1 cannot block more than it would by matching wording it was built on;
  this is reported with the result.
- **Readers:** Qwen3-4B (podgen, PLAIN and CAUTIOUS frozen templates, greedy, 40 tokens) and Phi-4 (Ollama, CAUTIOUS, greedy).
- **Release:** the V1-V5 gate (vkg.l3_checks2.release2) on the synthetic page.
- **Outcome per page:** correct (= gold or the true span) / inserted (= an inserted value, an A2 error by construction) /
  other / abstain. The comparison uses vkg.s12_run.agree. No judge is used.
- **System for P2/P3:** 4B cautious release + Phi-4 cautious agreement (the single-source analogue of the H1 system).

## Predictions (priors)
| | prediction | prior |
|---|---|---|
| P1 (C1) | for both 4B cautious and Phi-4 cautious, the inserted-value release rate rises from k = 0 to k = 4 at least twice as much for **rel** as for **ent** distractors (and the rel rise is > 0) | 55% |
| P2 (C2) | when the 4B cautious release is a relation-distractor value, Phi-4 gives the same value in ≥ 50% of cases | 45% |
| P3 (D3) | D3 v1-soft blocks ≥ 80% of the system's relation-distractor releases and keeps ≥ 90% of its correct releases at k = 0 | 35% |
| P5 | D3 v1-soft blocks < 50% of entity-distractor releases (the frame has no entity slot: a predicted blind spot) | 70% |

Also reported, without a threshold: D3 v1-strict and v2-strict on the same releases, 4B plain, and per-family rates.
Reading of the outcomes:
- P1 failing means relation confusion is not the dominant reading error, even when it is made available.
- P2 failing means the two readers' errors on relation distractors are mostly independent, so agreement removes them. That would
  weaken C2's "shared misreading" part.
- P3 failing means D3 as built does not remove A2 errors even by construction.

## Hashes (results/runs/s20)
```
2ffca7cc5a00c61a10d4b2287e0c29833ffb3a619f4fb60355ffaa9850e51f73 *synth.py
66bae622c65c86e84aa221dc2b0feb1fe241faa74f13975b9fcbaa3af41ccf6e *synth_items.json
800c017d8797505ab4f33dbbc49cc0ba1a9e6a76d7d3753c277041e418acd598 *frames.py
dc88d4aab3af6938664d8854c55dde0e208fbb2d4d525aa330b1847e88e8a576 *frames_v1.py
a901b5c8485a3d07a694cf39f4c7aebf11722494e45bbe2bd1febe9338207bba *parse_v2.py
```
