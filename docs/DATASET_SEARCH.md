# Search for a new clean test set (2026-11-07)

FRESH-5 used up the last untouched original SimpleQA items. Requirements for the next sealed test:
1. never inspected by this project;
2. single-hop factual questions whose answers sit in Wikipedia (the corpus is FineWiki, Aug 2025), so the frozen system can
   reach the 35% coverage floor;
3. one checkable gold answer, with low gold noise;
4. at least about 1,500 items, so that L2 has power (k ≤ 6 at n = 1526);
5. a licence that allows research use;
6. not built from the same source the verifier uses (no circular verification).

| candidate | size | questions | gold | fit | problem |
|---|---|---|---|---|---|
| **PopQA** (Mallen et al. 2022; HF akariasai/PopQA, about 5 MB) | 14k | templated, 16 relations, long-tail entities | Wikidata object + aliases | best fit for 1, 2, 4; single-hop, entity-centric like SimpleQA | templated wording; gold comes from Wikidata, so **Wikidata cannot be the D4 second source on this set** (circular); licence still to be checked on the card |
| EntityQuestions (Sciavolino et al. 2021) | 24k | templated, Wikidata relations | Wikidata | as PopQA | same Wikidata issue; more head entities |
| **Mintaka** (Amazon 2022; CC BY 4.0; HF AmazonScience/mintaka) | 20k (4k test) | human-written, natural | Wikidata entities | natural wording, permissive licence | mostly complex types (count, comparative, multi-hop, ...); only the "generic" type fits the frozen system |
| AntiLeakBench (ACL 2025; github bobxwu/AntiLeakBench) | not stated | built from Wikidata facts that changed in a date window | Wikidata | contamination-resistant by design | templated; licence not stated; released window 2022-23 |
| HalluLens PreciseWikiQA (Meta 2025) | about 5k, generated on demand | LLM-written from GoodWiki sections | LLM-extracted | fresh on demand | questions are written from Wikipedia sections, the same source as our corpus (circular), and the gold is LLM-made: dev use only |
| AA-Omniscience-Public | 600 (v1) / 300 (v1.1) | expert domains (law, health, finance, ...) | reference answer | private full set exists | too small, and not Wikipedia-groundable |
| SimpleQA Verified | 1,000 | human | human | — | already used (FRESH, DEV, S2 dev) |
| NQ-open test | 3,610 | real search queries | Wikipedia spans (2018) | natural, Wikipedia-grounded | about half the questions are ambiguous (AmbigQA); 2018 answers can be stale |
| Search for a 2026 human-written English SimpleQA-style set | — | — | — | — | none found (two broad searches) |

## Recommendation
- **Primary next sealed set: PopQA, with a long-tail stratum** (seeded sample of about 2,000 items, sealed unseen, as was done for
  FRESH-5). It is the only large, single-hop, Wikipedia-groundable set we have not touched. Its Wikidata gold has a useful side effect:
  A_S (source vs gold) becomes measurable as "Wikipedia page vs Wikidata". Constraint: on this set, D4 must use a second source
  other than Wikidata, or D4 is not part of the tested system.
- **Secondary, natural wording: Mintaka test, "generic" questions only** (CC BY 4.0). This checks that the result is not an artefact
  of templated questions.
- The frozen S19 system would be run unchanged first. A new protocol (S21) is written and hashed before anything is unsealed.
- Downloads need the user's permission first: PopQA (HF akariasai/PopQA, about 5 MB) and Mintaka (HF AmazonScience/mintaka,
  a few MB). Each goes into its own new folder and is read as data only. A loader seals the sample without printing any items.

Sources: HalluLens arXiv 2504.17550; AntiLeakBench arXiv 2412.13670 and github bobxwu/AntiLeakBench; SimpleQA Verified arXiv 2509.07968;
AA-Omniscience arXiv 2511.13029 and HF ArtificialAnalysis/AA-Omniscience-Public; PopQA arXiv 2212.10511 and HF akariasai/PopQA;
Mintaka arXiv 2210.01613 and HF AmazonScience/mintaka.
