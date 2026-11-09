# S21 DEV feasibility: the frozen S19 system on new datasets (2026-11-07, design data)

Run: results/runs/s21/run_dev.sh (frozen S19 pipeline, DuckDuckGo evidence, Phi-4 veto), scored by results/runs/s21/dev_eval.py
(results/runs/s21/dev_eval.md). Third attempt; the first two stalled (embedder crash; judge gate checked the dead pod instead of
the local GPU, fixed with VKG_POD_HOST=local). TEST files stay sealed.

## Results (frozen S19 H1 system)
| set | n | released | coverage (floor 0.35) | wrong | wrong / released | combo_plain baseline: answered / wrong |
|---|---|---|---|---|---|---|
| S19 FRESH-5 (reference, test) | 1526 | 568 | 0.372 | 4 | 0.7% | — |
| PopQA DEV | 300 | 59 | **0.197** | **7** | **11.9%** | 240 / 100 |
| Mintaka generic DEV | 200 | 71 | 0.355 | 2 | 2.8% | 184 / 32 |

PopQA by popularity tercile: coverage 0.23 / 0.15 / 0.21 (high / mid / low); errors 3 / 2 / 2. Low coverage is mainly on film and book
relations (screenwriter, director, producer, author, genre: 17 releases from 195 items). Mintaka: politics 0 of 20 released.

## The PopQA errors (all 7 read)
| question | gold | released | class |
|---|---|---|---|
| In what country is Dobra River? | Romania | Croatia (page Dobra (Kupa)) | ambiguous subject: 5 rivers named Dobra |
| What is Jordan the capital of? | Guimaras | Amman | ambiguous subject (Jordan, Guimaras vs the country) |
| What genre is Legion? | horror literature | Superhero | ambiguous subject (16 pages named Legion) |
| What is the religion of Assumption of Mary? | Anglican / Orthodox ... | Catholic | ill-posed question (Wikidata property on a feast) |
| What is Brussels Capital Region the capital of? | EEC / ... | Belgium | gold incomplete (Belgium is correct) |
| What is Rusty Willoughby's occupation? | songwriter | Musician | both acceptable |
| Who was the producer of O Dragão da Maldade ...? | Glauber Rocha | Zelito Viana | possibly both (co-producers); real error otherwise |

Mintaka errors: "Who developed The Room: Old Sins?" Fireproof Games vs gold Fireproof Studios (same company, renamed: both acceptable);
"Who wrote Salaryman?" (ambiguous title; released from Salaryman Kintaro (film)).

**Reading.** The dominant failure is not a reader mistake but the question itself: templated PopQA questions name the subject by
its label only, and the label is often shared by many entities. S19 passed on SimpleQA, whose questions were written to be
unambiguous. This is assumption A_M failing at the question -> entity step (the "entity slot" of D3), plus gold noise (A_S on the
benchmark side). Under the S19 adjudication rubric about 3 of 7 PopQA errors would be "both acceptable" or "gold wrong"; the
ambiguous-subject cases would count as "cannot tell" or as errors.

## Lexical entity checks do not fix it (results/runs/s21/ent_eval.md)
- E-match (release page title is the question's subject): removes errors but also 30-70% of correct releases (answers are often
  found on another entity's page, e.g. the director's page). Mintaka coverage 0.355 -> 0.095.
- E-unique (no other page with the same title core, unless the question names the qualifier): cheap (coverage loss about 3 points
  on old sets) but blocks only 2 of 7 PopQA errors.
Same pattern as D3 frames (S20): a lexical mapping check buys reliability only at a large coverage cost. Further support for the
sharpened C4 (granularity / reliability trade-off in the semantic mapping).

## What this means for S21
1. A confirmatory L2 test of the unchanged S19 system on PopQA would fail the coverage floor (DEV 0.197, far below 0.35); predicted
   FAIL. On Mintaka the coverage is at the floor and the raw error rate per item is about 1%, so k at n = 2000 would be about 20,
   above the L2 limit (about 12). Predicted FAIL for L2, though L1 might hold.
2. So the S19 L2 PASS is scoped to SimpleQA-style questions (written to be unambiguous, Wikipedia-grounded). This scope must be
   stated in the write-up; it is the honest headline of S21 DEV.
3. Proposed S21 (to be frozen before unsealing, after coordinating the Bonferroni split with Kimi):
   - **transfer test, not a pass attempt**: run the frozen S19 system on both sealed test sets, with pre-registered predictions
     (PopQA coverage < 0.35; Mintaka L2 FAIL, L1-A versus combo_plain baseline MET), error classes adjudicated with the S19 rubric
     plus an added class "ambiguous question";
   - measure A_S directly on PopQA (Wikipedia page versus Wikidata gold);
   - pass all gold aliases to the judge (S19 passed only gold[0]); on DEV no wrong release matched another alias, so this is
     low-risk, but it is the right rule.
4. Research next (Goal B / L3): the entity slot needs a non-lexical check. Candidates: ask the question parser for the subject's
   type and a disambiguating attribute, and require the release page to match; or release with an explicit qualification
   ("Qualified: assuming 'Jordan' means the country") instead of a silent answer. The latter fits Goal A's three output states
   directly and costs no coverage.
