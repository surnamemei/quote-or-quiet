# Claim-source verification log (2026-11-09)
Method: every sentence of paper/manuscript.md that attributes a statement to a cited source was checked by one reader (me) under the skeptic rule: no supporting phrase found in the source, no confirmation.
Sources were the arXiv abstract pages unless noted; two were read in full text (BalanceRAG, Judge Retrieve or Abstain); PopQA body via ar5iv. Note: one reader did both roles; this is weaker than the two-role protocol.

| # | claim in the manuscript | source | outcome | note |
|---|---|---|---|---|
| 1 | selective prediction trades coverage for risk with a confidence threshold | Geifman and El-Yaniv 2017 | PARTIAL, reworded | abstract says coverage is traded to meet a user-set risk by rejecting instances; "confidence threshold" not in the abstract |
| 2 | conformal risk control controls expected risk | Angelopoulos et al. 2024 | CONFIRMED | "control the expected value of any monotone loss function" |
| 3 | Learn-then-Test gives high-probability guarantees | Angelopoulos et al. 2021 | REJECTED as worded, reworded | abstract says "explicit, finite-sample statistical guarantees" only |
| 4 | attribution framework | Rashkin et al. 2023 | CONFIRMED | AIS evaluation framework |
| 5 | citation evaluation | Gao et al. 2023 | CONFIRMED | metrics for fluency, correctness, citation quality |
| 6 | Self-RAG reduces unsupported claims | Asai et al. 2024 | PARTIAL, reworded | abstract says it improves "factuality and citation accuracy"; no "unsupported claims" |
| 7 | detection from sampling disagreement | Manakul et al. 2023 | CONFIRMED | sampled responses likely to diverge and contradict |
| 8 | semantic-entropy detection of confabulations from samples | Farquhar et al. 2024 | BLOCKED today | Nature and PMC pages returned redirects or a browser check; supported by the primary page read on 2026-11-05 (docs/LITERATURE_CHECK.md) |
| 9 | SimpleQA questions have a single stable answer | Wei et al. 2024 | CONFIRMED | abstract: single, indisputable answer; Sec. 2.1: reference answers should not change over time |
| 10 | SimpleQA Verified relabelled the original | Haas et al. 2025 | PARTIAL, reworded | abstract: filtered 4,326 to 1,000, noisy labels, topical bias, redundancy |
| 11 | Mintaka crowd-written, Wikidata | Sen et al. 2022 | CONFIRMED, reworded | "naturally elicited from crowd workers", "annotated with Wikidata entities" |
| 12 | PopQA from Wikidata triples, templates, popularity | Mallen et al. 2023 | CONFIRMED in body only | abstract has none of it; body: triples of 16 relationship types from Wikidata, templates written per relation, Wikipedia monthly page views as popularity proxy |
| 13 | Qwen3-4B-Instruct-2507 is the updated non-thinking release | model card | CONFIRMED | "updated version of the Qwen3-4B non-thinking mode" |
| 14 | Phi-4 as a reader | Abdin et al. 2024 | no specific claim | |
| 15 | Clopper-Pearson bound | Clopper and Pearson 1934 | no specific claim | existence checked |
| 16 | BalanceRAG: thresholds, risk 10 to 16%, random splits, semantic-similarity gold, same-distribution assumption | Jia et al. 2026 | CONFIRMED in full text | targets 0.10 to 0.16; 100 random 50/50 splits; similarity threshold 0.7; limitation paragraph |
| 17 | Judge, Retrieve, or Abstain: FDR, Clopper-Pearson, 5 to 30%, random splits | Badshah et al. 2026 | CONFIRMED in full text | 2,000 instances per dataset, 100 splits, drift check after three months |
| 18 | conformal factuality for RAG: vacuous outputs, fragile under shift and distractors | Chen et al. 2026 | CONFIRMED (abstract) | |
| 19 | extractive spans | Recski et al. 2026 | CONFIRMED (abstract) | |
| 20 | proof-carrying numbers | Solatorio 2025 | CONFIRMED (abstract) | no experiments reported |
| 21 | agreement weak when errors correlated | Denisov-Blanch et al. 2026 | CONFIRMED (abstract) | |
| 22 | PAT-Questions gold regenerated from knowledge-graph queries | Meem et al. 2024 | CONFIRMED (abstract page) | |
| 23 | AmbigDocs entities sharing a name | Lee et al. 2024 | CONFIRMED (abstract page) | |

Counts: 23 pairings checked; 16 confirmed (3 of them in body or full text); 4 partial or rejected as worded and reworded (rows 1, 3, 6, 10); 1 blocked (row 8, supported by an earlier primary read); 2 with no specific claim.
Warnings carried forward: do not write "high-probability guarantee" for Learn-then-Test from its abstract; do not say Self-RAG "reduces unsupported claims"; PopQA's construction is in the body, not the abstract; BalanceRAG and Judge, Retrieve, or Abstain have no public code.
