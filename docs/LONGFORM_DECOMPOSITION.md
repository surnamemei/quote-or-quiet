# How to split a long answer into checkable claims (research note, 2026-11-09; nothing run)

Companion to LONGFORM_DESIGN.md. The decomposition step decides what the gate can check, so its errors become the system's errors.

## 1. What the literature says about the unit of checking
- **Too atomic loses context.** Gunjal and Durrett ("Molecular Facts", Findings of EMNLP 2024): a fully atomic fact can be "verified" against evidence about a different entity. They ask for two properties: decontextuality (the claim stands alone and names its entity uniquely) and minimality (it adds no more than needed). Their two-step method first finds ambiguity in the subject, then disambiguates; it helps most in ambiguous biographies.
- **Bad splitting corrupts the score.** Core (Jiang et al., 2024): decomposition-based precision such as FActScore can be inflated by obvious or repeated sub-claims; they filter for uniqueness and informativeness before scoring.
- **Extraction quality can be measured.** Claimify (Metropolitansky and Larson, ACL 2025): extraction is judged by entailment (is each claim implied by the source sentence), element-level coverage (are the sentence's verifiable elements captured) and decontextualization; Claimify extracts only when the reading is confident. A search summary reports 99.0% claim entailment for Claimify, tied with VeriScore and above DnD (89.1%); I have read only the abstract, so these numbers are unverified here.
- **Decomposition can be trained for verification.** "Distill and Align Decomposition" (Findings of EACL 2026) trains an 8B decomposer on verification accuracy and decomposition quality jointly (about 8 sub-claims per claim on average).

## 2. The unit for Quote or Quiet: a slot claim
The gate can check one thing exactly: that a typed value is a verbatim span of a pinned page. So the unit is a **slot claim**:

    (subject page, relation as a short question, value, qualifiers)
    ("Marie Curie", "Where was Marie Curie born?", "Warsaw", -)
    ("Marie Curie", "When was Marie Curie awarded the Nobel Prize in Chemistry?", "1911", -)

- The **subject page** does the decontextualization that molecular facts ask for, in the strongest form: the subject is a pinned page title, so "Heat" becomes "Heat (1995 film)" and the reader of the final text sees which one. It reuses the S30-S33 lesson: the page title is what makes a reading visible.
- The **relation question** is what lets each claim go through the frozen short-form system unchanged (support, typed span, second reader).
- The **value** is typed (YEAR, DATE, NAME, NUMBER, PLACE) by the question, so the existing type check (V3) applies.
- **Qualifiers** (a time, a role) are part of the question ("Who was Prime Minister of X in 2001?"), never a free-floating phrase.

What is not a slot claim (evaluations, causes, summaries, "widely regarded as") is labelled unchecked.

## 3. The decomposition pipeline
1. **Select.** Split the draft into sentences; keep sentences that state at least one verifiable fact (Claimify's selection step).
2. **Name the subject.** For each sentence, resolve pronouns and short names to a page among the evidence pages (the answer's own retrieval results); if two pages fit, the claim is unchecked (no guessing).
3. **Extract slots.** One model call per sentence returns a list of slot claims in a fixed JSON form. For biographies a closed set of relation templates covers most facts (birth date and place, death date and place, nationality, occupation, education, spouse, positions with dates, works with years, awards with years); other relations use a free question.
4. **Check the extraction, not the facts.** Before any verification, three checks, deterministic where possible:
   - entailment: each slot claim, rendered as a sentence, must be implied by its source sentence (an NLI judgement by a second model, plus the deterministic test that the value string occurs in the source sentence);
   - coverage: every number, date and capitalised name in the source sentence must appear in some slot claim; anything left over makes the leftover part unchecked;
   - informativeness: drop duplicates and trivial claims (Core) before counting retention.
5. **Verify.** Each slot question goes through the frozen short-form system with the value as its only candidate.

## 4. Re-render the output from verified slots
The original sentences are not kept as they are. The final text is written from the verified slots only:
- either by templates ("Marie Curie was born in Warsaw [quote, source]"),
- or by a model that rewrites the verified slots into prose, followed by a deterministic check that every number, date and name in the prose is the value of a verified slot, and an entailment check that the prose says nothing the slots do not.
This closes the gap that claim-filtering methods leave open: when a sentence keeps its original wording after its checkable parts pass, unchecked content (an adjective, a cause, a second fact) can stay inside it. Re-rendering means every factual statement in the output is a verified slot. The cost is style, measured and reported.

## 5. Pilot to measure the decomposition (design set, before any test)
- 50 biographies of people with Wikipedia pages (FActScore-style prompts), drafted by the 4B with evidence; decomposed by Phi-4 (a different family from the drafter).
- Blind review of a random 300 slot claims by two reviewers: is the slot claim implied by its source sentence; is the subject page the right entity; is the relation question faithful.
- A random 100 source sentences: element coverage (share of verifiable elements captured).
- Targets before freezing: entailment at least 97%, correct subject page at least 97%, coverage at least 80%, share of claims covered by the closed relation set reported.
- If the targets are missed, the decomposition is changed and re-measured on the same design set; the sealed test comes only after they are met.

## 6. What this would add to the field
- A unit of checking that is decontextualized by construction (a pinned page title), typed, and checkable by the same deductive gate as short answers.
- Output re-rendered from verified units, so a "kept" sentence cannot carry unchecked content.
- The same two-level measurement as short form: the system's own error against the facts, separated from the reference's errors.

## Sources
- Gunjal and Durrett, Molecular Facts: Desiderata for Decontextualization in LLM Fact Verification, arXiv:2406.20079 (Findings of EMNLP 2024).
- Jiang et al., Core: Robust Factual Precision with Informative Sub-Claim Identification, arXiv:2407.03572.
- Metropolitansky and Larson, Towards Effective Extraction and Evaluation of Factual Claims (Claimify), arXiv:2502.10855 (ACL 2025).
- Distill and Align Decomposition for Enhanced Claim Verification, arXiv:2602.21857 (Findings of EACL 2026).
