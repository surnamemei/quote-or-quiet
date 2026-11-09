# S19 result: joint sealed test on FRESH-5 (2026-11-07)

Protocol: docs/S19_PROTOCOL.md (FROZEN 10:04). One run on FRESH-5, all 1,526 items, no item skipped.
The 89 frozen files were checked before the run, after the run (hashes_check_after.txt: 89 OK, 0 not OK) and again after
`final` (0 not OK).

## Verdict
- **H1 (L2, this session): PASS.** Coverage 568 / 1526 = 37.2% (floor 35%). Graded-wrong releases k = 4, raw SER 0.26%.
  With the false-credit correction, the one-sided 97.5% Clopper-Pearson upper bound is **0.76%**, below the 1% limit.
  Primary (adjudicated) and secondary (gold-relative) are the same, k = 4, because no adjudication was done (deviation 3 below).
  Files: S19_raw.md, S19_final.md.
- **H2 (L1-A, Kimi session): MET.** The tiered system vs wiki_plain: coverage 70.9% vs 61.5%, SER 3.0% vs 12.1%. All three
  criteria pass: (a) SER difference upper bound −1.9 points; (b) coverage difference lower bound +16.0 points; (c) passes.
  File: E:\Models\halluc_runs\TIERED_S19_FRESH5.md (scorer tiered.py hash matches the freeze).
  **Secondary L1-B comparisons are not met:** vs combo_plain and vs MSany, criteria (b) and (c) fail. vs 4B cautious combo,
  (a) fails too (upper bound +0.26 points), and (b) and (c) fail. The tiered system buys a lower error rate with less coverage,
  so it does not halve errors at equal coverage against the stronger single-pass readers.
- Cross-check: Kimi's "tier 1 only" row is the H1 system, scored independently: 568 releases, 4 errors. It matches.

## Predictions (priors fixed before unsealing)
| | prediction | prior | outcome |
|---|---|---|---|
| P1 | H1 met (adjudicated k ≤ 6, coverage ≥ 35%) | ~60% | met (k = 4, no error removed) |
| P2 | secondary met (gold-relative k ≤ 6) | ~35% | met (k = 4) |
| P3 | coverage ≥ 35% | ~85% | met (37.2%) |
| P4 | adjudication removes ≥ 1 system error | ~80% | **not tested** (no adjudication) |
| P5 | ≤ 1 in 10 decoy_system_correct rows judged "answer wrong" | ~80% | **not tested** |

The gold-relative error rate (0.26%) came out below the design estimate (0.33-1.0% on DEV/FRESH, 0.45% on S18).
P2 had a prior of only about 35%, so k = 4 is at the lucky end of what the design data predicted.

## Deviations and incidents (all of them)
1. **DuckDuckGo error page (rule set during the run).** Attempt 1 stopped about 13:51 when DuckDuckGo answered one query with
   its own "Oops... server error" page; the frozen websearch raised, as designed, and the run was postponed. Before any FRESH-5
   model output existed, I fixed this rule (about 14:05-14:10; the user had delegated decisions): a query that gets the Oops page
   on first failure and again on a direct probe at least 45 min later is recorded as having no web results (cache "[]", exactly
   what websearch writes for a "No results" page). Bot checks and other failures still postpone. It fired once, at 14:36
   (cache key 459dcd5f70e120ef). That item kept its wiki and combo evidence and stays in n. No frozen file changed
   (results/runs/s19/resume.sh, INCIDENTS.md).
2. **Restarts.** Attempts 2-4 failed in the embedder: CUDA out of memory three times while system RAM was full (my own
   analysis job, 36 GB, plus a Kimi-session job, about 38 GB), then a ConnectionAborted error. Each restart resumed from the caches
   with the same frozen run_test.sh. The final attempt (15:06-17:07) ran without errors. No item was skipped or regenerated
   differently: generation is greedy and batch sizes are bounded by tokens.
3. **No blind adjudication.** The user delegated this step ("你看着办"). I did not adjudicate myself, because I built the system
   and had seen the raw result. I filled every row as "cannot tell", which the rubric counts as keeping the error. So the primary
   endpoint equals the gold-relative one, the most conservative reading. P4 and P5 are untested. The blank sheet is kept as
   S19_adjudication_sheet_blank.csv.
4. **Glimpse of two test questions.** While debugging the search failure, error messages showed me the opening words of two
   FRESH-5 questions ("Rana Ayyub … awarded the Internatio…" and "Q-Ship 'Salvia' (alias Q-15) struck by a torpedo…").
   No gold, answers or outputs were seen, and no frozen component changed after the freeze, so this could not affect the system.
5. The judge (grader 6.1) labelled all outputs during generation, as the protocol says. Both scorers then ran with the judge disabled.

## The 4 errors (post hoc reading after unsealing; decides nothing)
| question (short) | gold | released | page sentence | class |
|---|---|---|---|---|
| Sosoliso 1145 first officer, full name | Gerad Yakubu Andan | Gerald Andan | "The first officer was Gerald Andan, …" | incomplete name (asked for the full name); source wording |
| Lennon's Rolls-Royce shown at PNE, year | 2014 | 2015 | "In 2015, it was shown at the Pacific National Exhibition …" | source vs gold (A_S / gold) |
| Jock Zonfrillo death date | April 30, 2023 | 1 May 2023 | "(4 August 1976 – 1 May 2023)" | source vs gold (A_S / gold) |
| Pakistan, World Cup absences "as of 2022" | 2014 | 2014 and 2023 | "… the only absence coming in 2014 and 2023" | temporal qualifier ignored (A2 / qualifier) |

Each released span is stated verbatim on a hash-pinned page, so all four are failures of the assumptions, not of the
deductive checks. Two are source-versus-gold disagreements, one is an incomplete answer to "full name", and one ignores the
"as of 2022" cut-off. No error is a pure reader hallucination.

## D3 out of sample (exploratory, not pre-registered)
The D3 frame-match code (results/runs/s20/frames.py, frames_v1.py, last changed 15:14) predates the FRESH-5 outputs (17:07).
Hashes are recorded in results/runs/s20/d3_v1_hashes_before_fresh5.txt. Table: results/runs/s20/d3_fresh5.md.
| FRESH-5, H1 system + D3 v1 | coverage | wrong |
|---|---|---|
| none (H1) | 37.2% | 4 |
| D3-soft | 29.9% | 3 (blocks the "as of 2022" qualifier error) |
| D3-strict (T* form) | 11.7% | 1 (Zonfrillo: an A_S case) |
This repeats the S18 pattern out of sample: under D3-strict, the only error left is a source/gold one, as T* predicts, and
D3 costs too much coverage for L2 (below the 35% floor). It was not pre-registered, so it is a consistency check only.

## What this means and what it does not
- **L2 is reached for this system** on original SimpleQA questions: with gold-relative grading, with no adjudication and at
  37.2% coverage, the one-sided 97.5% upper bound on SER is below 1%. The other 62.8% of questions are abstentions
  (Unresolved), not answers.
- **L1 is only partly reached.** H2 halves errors against the pre-registered baseline (wiki_plain), but not at equal budget and
  not against the stronger single-pass readers.
- **Not L3.** Every release has a verbatim, typed, period-checked span in a hash-pinned page, but the 4 errors show that the
  assumptions (source truth, semantic match, completeness) fail at about 0.26% here. The L3 plan is docs/THEORY_CONJECTURES.md
  section 6 (D3 frame match, D4 conflict → Qualified) and docs/S20_PLAN.md.
- **FRESH-5 was the last untouched SimpleQA pool.** Any further confirmatory test needs a new clean question set.
