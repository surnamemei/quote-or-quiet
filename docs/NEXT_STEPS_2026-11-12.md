# Next steps (2026-11-12, bar 36 of 48)

Order of work. GPU jobs run one at a time under the shared lock; reviewer rounds start when a sheet is ready.

1. G4 (S58, running): candidates, 27B judge (rule Q2), grading, adjudication sheet; then two blind reviewers adjudicate every gold-wrong release (gold shown, removing verdicts need a quote found in the page), 12 decoys and 24 gold-matching releases mixed in; unblind; record pass or fail as registered (coverage at least 35% and at most 5 adjudicated errors of 1,200).
2. G15 (S66, queued after G4): the 1,000-request stress test of the service (about 4 to 5 hours with 10 s between web questions); independent check of every released statement; record.
3. G16 (replication by someone else; CPU now): a replication guide in the release repository (docs/REPLICATION.md) listing, for each gate, the command that recomputes its table from the released aggregates and scripts, what needs the local models and Wikipedia snapshot, and what a replicator should send back. The gate is met only when another person reruns it.
4. G12 (people check the reviewers; CPU now): refresh the human audit sheet so that it covers the kinds of verdict the gates now rest on (quote states the answer; attribution on contested topics; long-form claims), 180 rows, Chinese and English instructions, no answer key in the folder; the gate needs two people.
5. Tool v2 (after G15; design first): the service still uses the 4B judge for rule R. Put the validated 27B rules in: R27 for open questions (G3, G11), Q2 for natural-question coverage (G4, if it passes), W4-27 for /bio (G8), A3 for a new /views endpoint (G9, G10), the G14 check for drafts of any model (/check). Memory: the 27B (about 20 GB) cannot sit beside the 4B server and Phi-4 with the desktop's share, so v2 loads models in turn (readers, then the judge) or drops Phi-4 where a rule does not use it. After v2: rerun G15 on v2 (registered as a second stress test).
6. Paper and release after each result: tracker, sections, abstract, release push.

## Phase 2 (G12 stays open for now; G16 needs an outside person)
7. Cross-family reviewer check (not counted for G12): Gemma 3 12B or Mistral Nemo re-reviews a sample of every gate's sheets with the same instructions; agreement with the Claude reviewers is reported per gate.
8. Judge robustness: G3, G11 and G14 rerun once, registered, with another judge family in place of the 27B Qwen (e.g. Gemma 3 12B).
9. Paper pass to version 0.5: structure around the gates and the tracker, every number checked against its result file, an anti-defensive style pass.
10. Release cleanup: README with the tracker table, tool v2 documentation and limits, a fresh-clone check against docs/REPLICATION.md.
11. New scope (user permission given 2026-11-12, "feel free to do that"; download of the Chinese Wikipedia snapshot): the quote check on Chinese questions, as a new gate.

## Added 2026-11-12 after the G4 result (S58 failed: 7 adjudicated errors, upper 1.20%)
4b. G4 second test, registered before any output: rule Q2 unchanged; adjudication fixed in advance on the two causes found: (a) 'answer right' (equivalent to the gold) is a clearing verdict when both adjudicators give it, as are 'gold wrong' and 'equally acceptable'; (b) the quote check also matches against the rendered page text (MediaWiki action=parse text), so that dates written with templates are found. Questions: a fresh natural-question set, since Mintaka's generic questions are used up: candidates are the NQ-open or WebQuestions test sets (public; download needed, under the user's download permission), sealed with a script that prints counts only. Runs after G15 and before tool v2.
