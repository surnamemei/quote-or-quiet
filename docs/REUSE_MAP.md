> Note (2026-11-05): for the verification status of any reference, docs/LITERATURE_CHECK.md is authoritative. This map is out of date in places: Abstain-R1 is confirmed only as 'accepted at ACL 2026'; 2405.05904, 2601.04525, 2608.22228, TIAR and AWA-RL have since been verified from primary pages; 2509.04664, 2404.05405, 2603.21172, 2606.02628, 2510.17733 and 2601.20126 were not re-checked in LITERATURE_CHECK.

# What already exists, and how VKG reuses it

Status: **verified** = primary page or search result of the primary page seen 2026-11-05. Papers' claims were read from
search snippets, not full texts; open the primary source before quoting numbers.

| need | existing work | status | use in VKG |
|---|---|---|---|
| Incentive theory | Kalai et al., *Evaluating LLMs for Accuracy Incentivizes Hallucinations*, Nature 2026 | verified exists | motivates scoring with abstention (our SER/yield), "open-rubric" evals |
| Unanswerable / inconsistent context | FaithEval (Salesforce, ICLR 2025): 2,492 unanswerable, 1,500 inconsistent, 1,000 counterfactual | verified, downloaded | real-data twin of `closed_unans` / `closed_conf` |
| Broad abstention | AbstentionBench (Meta, NeurIPS 2025): 20 datasets, 35k+ unanswerable; reasoning models lose abstention recall | verified, not yet downloaded | Phase 1 breadth; uses LLM judge, so treat as secondary |
| Open-world short facts | SimpleQA Verified (Google, 2025): 1,000 Qs; no tools; public since 2024 | verified; contamination risk | open-world check, labelled contaminated-possible |
| Sampling-based detection | Semantic entropy (Farquhar et al., Nature 2024) | verified | stronger replacement for my string-match consistency gate |
| Risk guarantees | Conformal factuality (Mohri & Hashimoto 2024); Cherian & Gibbs 2024; ITCR (ICML 2026, arXiv 2606.08831) | verified | L2 statistical guarantees; ITCR needs exchangeable calibration/test data |
| Multi-turn claim checking | VISTA (ACL 2026, code: ashleylew/VISTA) | verified | Phase 3+ dialogue, claim store |
| Evidence-chain systems | Science One / ScientistOne (Google Research, Jul 2026) | verified blog; vendor claims unverified | design reference only |
| Abstention training | R-Tuning (EMNLP Findings 2024); *Rewarding Intellectual Humility* (arXiv 2601.20126) | verified exists | Goal B: abstain-reward fine-tuning on local models |
| Claim-level graph checking | "FreeGuard": Wang and Zhao, "Claim level graph reasoning for training free LLM hallucination mitigation", Discover Computing 29:713, 7 Oct 2026, DOI 10.1007/s10791-026-10667-z | **EXISTS** (Crossref record confirmed by me; the method name FreeGuard and the abstract are from a subagent reading the Springer page, see docs/LITERATURE_CHECK.md) | earlier "not found" note was wrong (my searches had missed it); treat as a named baseline for claim-level checking |
| Long-form atomic facts | FActScore, VeriScore | cited by target.txt; not re-verified here | Phase 4 long-form |

## Consequences for the plan
- Do not rebuild detectors that exist; benchmark them as baselines (semantic entropy, conformal filtering).
- Novelty claims must be made against these, not against raw prompting.
- Reported gains on FaithEval/AbstentionBench are comparable to others' numbers only with their exact prompts/graders.

## Update 2026-11-05: abstention training already exists (checked before building anything)
Sources read: arXiv abstract pages (fetched) and search snippets; full texts not read, numbers are the authors' claims, not reproduced here.
| Work | What it does | Models | Code/weights | Use here |
|---|---|---|---|---|
| Chen, Asai, Zettlemoyer, Hajishirzi, Brahman, arXiv 2510.17733 (Oct 2025), Binary Retrieval-Augmented Reward | online RL, reward 1 only if output is fully correct (checked against retrieval); model learns to abstain; claims 39.3% fewer hallucinations on long-form, 44.4% fewer wrong answers on PopQA | Qwen3 reasoning models (4B, 8B per search snippet) | none found on the page | the recipe closest to Goal B; do not re-derive |
| Jha et al., arXiv 2601.20126 (Jan 2026), ternary-reward RLVR | reward -1 wrong / r_abs abstain / +1 correct; moderate r_abs helps; open-ended QA needs SFT warm start | Granite-3.3-2B, Qwen3-4B | code: github.com/Mystic-Slice/rl-abstention (from abstract page); no weights | reusable training code |
| Abstain-R1, arXiv 2604.17073 (ACL 2026 Findings) | verifiable-RL abstention plus clarification after refusal | 3B | weights: huggingface.co/leoleung04/Abstain-R1 (from search); no code found | small-model reference |
| TIAR 2605.25850, AWA-RL 2607.10738, I-CALM (prompt-only) | further abstention-RL variants / prompt framing | various | not checked | cite as related |
Consequence: an abstention-RL run on a 27B model would repeat published methods. Remaining gaps that are specific to this project and not covered by these papers as far as I could see: (1) controlled prompt-vs-verifier-vs-training comparison on one model with independent gold (done for prompt vs verifier, see SUMMARY), (2) separating true-but-unsupported from false answers (FaithEval manual check), (3) model-size/architecture (dense vs MoE) and precision confounds, which these papers do not isolate. Training results from 2B-8B models do not transfer to Qwen3.8-27B without a test.

## Update 2026-11-05 (theory pass, see docs/ROADMAP.md)
Page-verified (abstract read): arXiv 2509.04664 (Kalai et al., why LMs hallucinate); 2404.05405 (Allen-Zhu and Li, knowledge capacity); 2603.21172 (entropy alone insufficient for selective prediction); 2606.02628 (probes in 4-bit LLMs; single author, AUROC up to 1.0 on paired-label sets, treat as unreliable until reproduced); 2510.17733; 2601.20126.
Search-snippet only (not verified): 2405.05904 and 2511.02626 (fine-tuning on unknown facts), 2406.15927 (semantic entropy probes), 2601.04525 (GRACE), 2608.22228 (GRAB-RAG), 2604.17073 (Abstain-R1), 2509.01455 (UniCR), 2603.24704 (SCoRE), the ICLR 2025 generation-verification gap paper, preprints.org 202601.0892.
No published Wikipedia-retrieval baseline for SimpleQA Verified with small open models was found; SimpleQA Verified is designed to test parametric knowledge.

## Corrections 2026-11-05 from docs/LITERATURE_CHECK.md (subagent; two points re-checked by me)
- UniCR (arXiv 2509.01455) is **withdrawn** by arXiv admin (authors could not be verified; re-checked by me on the arXiv page). Do not use it as support for shift-robust guarantees.
- SCoRE (2603.24704) states exchangeability; its shift extension is only asserted in the abstract. The abstracts of ITCR, Mohri-Hashimoto and Cherian-Gibbs do not mention exchangeability, so the sentence "needs exchangeable data" is unconfirmed for them.
- The finding that misleading retrieved evidence is the main failure belongs to GRAB-RAG (2608.22228, single author, 3.8-8B models), not to GRACE (2601.04525).
- Six further 2026 papers were verified from primary pages (2609.01687, 2609.37469, 2605.03534, 2606.29054 on conformal risk control under shift with open-weight models, 2606.22728, 2604.23783). No 2026 SimpleQA-style retrieval-abstention paper with open-weight models was found in four searches.
