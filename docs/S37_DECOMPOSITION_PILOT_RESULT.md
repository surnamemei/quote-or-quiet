# S37 result: decomposition pilot, version 1 (2026-11-09; design set only; targets in LONGFORM_DECOMPOSITION.md section 5)

Setup: 50 design people (title index, S29 subjects excluded), closed-book biographies by Phi-4 (FActScore prompt), one Phi-4 call per biography returning slot claims as JSON (prompt v1), deterministic checks. Drafts 1-19 ran on the CPU-only instance and the rest on a GPU instance; greedy decoding, so the two can differ in rounding; this pilot measures extraction only.
Output: 50 of 50 parsed; 530 sentences, 682 slot claims, 328 statements marked unchecked.
Review: 300 random slot claims + 30 decoys, two model reviewers per row (sentence and claim only, no web); 100 random sentences for coverage, two reviewers.

| criterion | result (both reviewers) | target |
|---|---|---|
| claim implied by its sentence | 267/300 = 89.0% (95% lower bound 84.9%) | 97%: not met |
| subject is the right entity | 188/300 = 62.7%; 272/300 = 90.7% when sentences that use only a pronoun for the biography's person count as right | 97%: not met |
| question faithful to the sentence | 268/300 = 89.3% | (reported) |
| element coverage (stricter reviewer) | 137/215 = 63.7% | 80%: not met |
| decoys caught by both | value swap 10/10, relation change 10/10, subject swap 7/10 | |

All three targets are missed. Version 1 is not good enough for a test.

## A flaw in the review sheet
The sheet did not show the biography's person, so a sentence that says only "he" or "she" could not be checked for the subject: two reviewers marked such rows "unclear", two marked them right. This explains most of the gap between 62.7% and 90.7%, and the 3 subject-swap decoys that were not caught (each in a pronoun sentence). The next sheet shows the person.

## What fails (from the data and the reviewers' notes)
1. **Sentence numbers drift.** 63 of 682 claims (9%) have a value that is not in the sentence they are attached to: 28 of these values are in another sentence of the same biography, mostly the previous one (the model's sentence index is one too high), and 35 occur nowhere in the biography (the model rewrote or completed the value, e.g. "London School of Economics" for "London").
2. **Wrong subject.** The subject is set to the work or organisation the fact mentions (the Parker series, a football club, a university, "2021") instead of the person, or the reverse.
3. **Added qualifiers.** Questions add names, places or works that the sentence does not contain ("at Harvard", "VfB Stuttgart", "University of New Hampshire").
4. **Missed facts.** Occupations stated in passing ("her prints", "penned hits"), nationalities, and facts in sentences cut by the splitter at headings are not extracted.

## Version 2 (to be built and re-measured on the same design set)
- One extraction call per sentence, with the biography's person given: no sentence numbers to drift.
- Deterministic filters before review: the value must occur verbatim in the sentence; the subject must be the person or a name that occurs in the sentence; every content word of the question must come from the sentence, the subject, or a short list of relation words (no added qualifiers).
- A second extraction pass for any sentence whose numbers or capitalised names are left uncovered.
- A sentence splitter that removes markdown headings and keeps clauses together.
- Review sheet shows the biography's person.

## Versions 2 and 3 (same 50 design biographies)
| criterion | v1 | v2 (one call per sentence + filters) | v3 (v2 + three filters, fresh unreviewed sample) | target |
|---|---|---|---|---|
| implied | 89.0% | 90.7% | 93.0% | 97% |
| subject right | 62.7% (sheet flaw) | 93.3% | 94.3% | 97% |
| question faithful | 89.3% | 95.7% | 94.0% | - |
| element coverage | 63.7% | 85.5% | 76.4% | 80% |
| decoys caught by both | 27/30 | 30/30 | 29/30 | |
Version 3's filters were found on the version 2 review; on the reviewed rows they predicted 94.4% implied and 97.0% subject, and on a fresh sample they gave 93.0% and 94.3% while coverage fell below target. The extraction plateaus at about 93-95% with Phi-4 and deterministic filters; the remaining errors are relation errors (a reputation read as an occupation, a film's year read as the year of recognition, "his tenure was controversial during the war" turned into "the war was controversial"). Version 2 is the better trade-off (coverage met, 91-96% on the others).

## What the extraction targets protect (reading, 2026-11-09)
The 97% targets were set as if an extraction error became an output error. In the design (LONGFORM_DECOMPOSITION.md section 4) it does not: every slot is verified against the pinned evidence, not against the draft sentence, and the output is re-rendered from verified slots only. An unfaithful slot (wrong relation, wrong subject) is checked as stated; if it passes, the re-rendered statement is true, only not what the draft said; if it fails, the content is dropped. Extraction quality therefore sets how much of the draft survives (retention and fidelity), while the truth of the output rests on the verification step, whose release error on short questions was 0 of 180 sampled.
The exception is an extraction error that the verification cannot see: a slot whose question is wrong in a way that the gate and the second reader still accept as true for the wrong reason. Measuring that needs the end-to-end test: verify the version 2 slots, re-render, and have reviewers check every kept statement against the facts (false-kept-claim rate), plus fidelity to the draft as a secondary measure.
Next step: end-to-end run on the 50 design biographies with version 2 slots (needs the GPU for the short-form verification), then a sealed test.
