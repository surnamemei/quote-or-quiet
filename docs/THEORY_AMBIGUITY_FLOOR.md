# T6: an ambiguity floor for gold-relative silent error (draft, 2026-11-09; numbers filled in from S35)

## Setting
A question q has a set of admissible readings R(q) (things the words can refer to, times they can refer to). For each reading r there is a true answer y(q, r). A benchmark fixes one reading g(q) and one gold answer; the gold can also be wrong for its own reading (stale or mistaken), with probability gamma.
A system releases on a share c of questions; each release is an answer a for some reading r (the reading may be implicit).
Gold-relative error on a release happens if a is wrong for every reading (true error, rate e), or a is right for a reading r with y(q, r) != y(q, g) (reading mismatch), or the gold itself is wrong.

## Statement
Let alpha be the share of releases on questions with two or more readings that have different answers, and m the probability that the system's reading equals the benchmark's reading on those questions. Then the gold-relative error rate among releases is at least

    e_gold >= e + alpha (1 - m) + gamma' ,

with gamma' the share of releases whose gold is wrong for the benchmark's own reading, and the gold-relative silent-error rate is SER_gold = c * e_gold.

## Why m is bounded (the information argument)
If the benchmark's reading is not determined by the words of q, no function of q (and of any evidence that does not encode the benchmark's choice) can match it more often than max_r P(g(q) = r | q). Any system, of any architecture or size, inherits the floor alpha (1 - m*), where m* is that maximum. For benchmarks that pick readings from a knowledge graph without regard to prominence (PopQA asks "In what country is Lima?" with the gold United States), m* is well below 1.

## Consequence for the L2 target
L2 measured against gold requires c * (e + alpha (1 - m) + gamma') < 1% (plus the confidence margin). At the coverage floor c = 35%, this needs alpha (1 - m) + gamma' + e below about 2.9% of releases. If the benchmark's own alpha (1 - m) + gamma' exceeds that, gold-relative L2 is infeasible at that coverage for every system, and the target is falsified for that benchmark rather than missed by the system.
Withholding flagged questions with a detector of true-positive rate t on ambiguous releases lowers the floor to alpha (1 - m)(1 - t) at a coverage cost; S32 and S33 measured t of roughly 0.1 to 0.25 at a cost above the bar, so detection does not remove the floor in practice.

## What stays feasible
Truth-relative error, where an answer is judged for the reading it states (Qualified) or, without a stated reading, for any admissible reading, does not have this floor: its floor is e, the system's own error. That is the target the system can be held to, and S35 estimates it on a random sample.

## Numbers (to be filled from S35: alpha, m, gamma', e with confidence intervals per benchmark)

## Numbers from S35 (2026-11-09)
Random sample of 180 frozen releases (60 per set: FRESH-5, Mintaka test, PopQA test), two blind model reviewers per row (no gold shown), 15 injected-false decoys (15/15 caught by both). Reviewers gave identical verdicts on all 180 sample rows; they are the same model family, so they are not independent in the way two humans would be, and the sample is not a human check.
- True error e (both reviewers say wrong for every reading): 0 of 180; 97.5% upper bound 2.0% of releases (per set 0/60, upper 6.0%).
- Ambiguous (right for one reading): 4 of 180 (2.2%, 95% interval 0.6 to 5.6%); the gold matched the system's reading in 2 of the 4 (m about 0.5), so alpha (1 - m) is about 1.1% of releases.
- Gold-relative wrong: 9 of 180 (5.0%); every one of the 9 was judged correct by both reviewers: 2 reading mismatches (Thor, Exposed) and 7 stale, partial or wrong golds (gamma' about 3.9%).
- Whole-population gold-relative error among releases: FRESH-5 4/568 (0.7%), Mintaka test 28/620 (4.5%), PopQA test 17/401 (4.2%).

## Verdict
1. Truth-relative (the system's own error): no error was found in 180 random releases. Converted to silent-error rate with each set's coverage, the 97.5% upper bound from the pooled sample (2.0% of releases) gives at most 0.74% on FRESH-5 (coverage 0.372), 0.62% on Mintaka (0.310) and 0.38% on PopQA (0.191). Below 1% on all three, under the caveat that the reviewers are models.
2. Gold-relative on Mintaka and PopQA: almost all gold-relative errors are benchmark-caused (about 4% of releases). For a system whose release decision does not see gold quality (and S30-S34 showed four ways of trying to see it, all failing), SER_gold is about c x 4%, which is 1.4% at the 35% coverage floor. So gold-relative L2 at coverage >= 35% is not reachable on these two benchmarks by a gold-blind system; this is a property of the benchmarks, not a shortfall of this pipeline. It is a conditional floor (gold-blind release), not an absolute one: a system that could detect bad golds could avoid them.
3. What is still genuinely open: coverage. Truth-relative L2 holds at the coverage the system reaches, but Mintaka (31%) and PopQA (19%) are below the 35% floor, and S30/S31 showed the coverage limit is the two-source pool, not the gate.
