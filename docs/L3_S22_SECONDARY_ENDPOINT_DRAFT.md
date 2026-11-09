> **WITHDRAWN 2026-11-09.** S22 was not run (docs/S22_DEV_FINDINGS.md). The Qualified layer is reported only as a post hoc,
> clearly labelled analysis on the frozen S19 releases (FRESH-5, S21 PopQA/Mintaka tests); nothing below is pre-registered.

# L3 Qualified layer as a secondary endpoint of S22 (DRAFT, not frozen; to be agreed with the S22 session)

Purpose: turn the entity-slot check from "designed on DEV, inspected post hoc on unsealed tests" into a pre-registered,
confirmatory secondary endpoint. It is post-processing of S22 releases: no GPU, no change to the S22 primary endpoint.

## Frozen decision module (hashes, 2026-11-08)
- results/runs/l3/qualified.py        sha256 463e23b48db678ea…  (v4, strict)
- results/runs/l3/qualified_dev.py    sha256 f20b99afcaab81dc…
- results/runs/l3/accounting.py       sha256 c6114c3cbb2562d8…
- results/runs/l3/titles.db           sha256 550c75ade97334eb…  (local FineWiki title index, 6,614,655 rows)
No edits to these after the S22 test sets are unsealed. Variant: strict only (mid and lenient are not reported as results).

## Procedure
1. For every S22 release on each test set, run qualified.decide(question, answer, release_page) -> Verified / Qualified(E) / Unresolved.
2. Grade Verified and Qualified answers against gold with the S22 alias-aware grader (same labels as the primary endpoint).
3. Counts per set: releases, Verified, Qualified, Unresolved; graded-wrong in each; graded-correct lost to Unresolved.

## Accounting (conservative, fixed in advance)
- Completion = graded-correct Verified + graded-correct Qualified.
- Silent error = Verified graded wrong + Qualified graded wrong. No conditional-truth discount: no judge was validated
  (docs/L3_QUALIFIED_DESIGN.md sections 9 and 10).
- Where S22's blind web adjudication removes an error ("gold wrong" / "both acceptable"), the same removal applies here.
- Qualified correct against gold with a wrong stated sense is reported separately as a qualifier error; it is not a silent error.

## Endpoints
- Secondary S1: the same bound as the S22 primary endpoint (Clopper-Pearson one-sided 97.5% after the f_up = 0.0082 correction,
  E = ceil(k/(1-0.0082))), computed at the run's actual coverage (floor 0.35), on Verified + Qualified.
- Secondary S2: the same bound on Verified alone, reported always; it is the headline if more than half of releases are Qualified
  (anti-gaming clause).
- Secondary S3: entity errors. Count of S22 releases that adjudication labels "ambiguous question" / wrong-sense and that remain
  Verified. Expected 0 given DEV (no entity error in Verified) and the PopQA unsealed tests (all 8 S21 entity errors left Verified).
- Cost, reported not tested: completion lost to Unresolved versus the unfiltered S22 release (DEV strict: 0-3.6% of correct answers).

## Stated limits (part of the registration)
- Mention extraction is the main hole: if no mention is found the output defaults to Verified.
- Remaining assumptions as in L3 section 3: source true, span answers the relation, time, closed-world senses.
- The Qualified accounting is conservative, so S1 can be worse than the primary endpoint; that is accepted.

## Inputs (confirmed by the S22 session)
- results/runs/s22/{set}_releases.jsonl: id, question, gold (list), answer, source (s19|pin), release_doc (page text via
  vkg.localwiki.page_text), wiki_titles, grade (True/False/"?", alias-aware).
- Adjudication: results/runs/s22/mintaka_test_adj_checked.csv + mintaka_test_adj_key.json, kind == "system" rows only.
- Dry run on the closed S21 set mintaka_test_releases.jsonl (design data, 1005 releases); S3 note: 2 system rows were marked
  'ambiguous question' by adjudication.

## Request to the S22 session (answered: agreed 2026-11-08)
Confirm the endpoint wording, and that the release files (results/runs/s22/*) carry question, answer, release page text and
graded labels in a form the module can read. No file under results/runs/s22/ is touched by the L3 side.

## Dry run (closed S21 Mintaka set, S22 release file; design data, decides nothing)
Script results/runs/l3/l3_secondary.py, output results/runs/l3/secondary_mintaka_test.md. 1005 releases: Verified 616 (6 errors
after adjudication), Qualified 296 (1 error), Unresolved 93 (87 graded correct, i.e. 8.7% of releases lost). Qualified share
about 0.30, below the 0.5 anti-gaming trigger. S1: k=7, E=8, bound 1.72%; S2: k=6, E=7, bound 2.33% (both above 1%, the
sample is a design set with many ambiguous-entity questions). Known weakness seen: the Qualified sense can be a wrong-type
sense that still holds the answer ("Mount Rushmore (band)" for the location question), a qualifier error with a true answer.
Cost of Unresolved is the largest open item.
