# Model matrix and comparison rules

Facts below come from public Hugging Face model cards / config.json (fetched 2026-11-05). Knowledge cutoff is
**not stated** on either card, so recency must be measured, not assumed.

| model | FFN type | total / active params | attention | notes |
|---|---|---|---|---|
| Qwen3.8-27B | Dense (card: "dense model") | 27B LM (28B with vision) / all | hybrid: 48 linear + 16 full (every 4th layer) | 64 layers, hidden 5120, BF16 original |
| Qwen3.8-Flash-Next | MoE: 512 experts, 10 routed + 1 shared | 125B LM (+51B n-gram embeddings, +4B MTP; 180B file) / 6B | hybrid Gated DeltaNet + Qwen Sparse Attention, 48 layers | release Aug 2026, license qwen-community-1.0 |

"Dense" here means dense feed-forward only; attention is already hybrid. Flash-Next is *not* an "A3B"-class model.

## Rules that follow
1. **Dense-vs-MoE is confounded** in this pair: total parameters (27B vs 125B+), active parameters (27B vs 6B),
   quantization, attention variant and runtime all differ. Report as descriptive. No sentence of the form
   "MoE causes X" without a routing intervention (top-k change, expert ablation, router swap).
2. **Clean attributions** come only from within-model variables: same weights at BF16 / Q8_0 / Q5_K_M / NVFP4,
   same prompts, same runtime. Runtime (Ollama vs Infernix) is itself a variable; compare on one model first.
3. **Size** is reported as total *and* active parameters, plus memory footprint.
4. **Timeliness** (three separate issues):
   - *Contamination*: public benchmarks (SQuAD-derived FaithEval, SimpleQA since 2024) may be in training data.
     Procedurally generated items (this repo's synthetic families) cannot be. Keep both; compare.
   - *Staleness (F6)*: with no stated cutoff, probe it: facts known to change in 2025-2026 vs stable facts.
   - *Literature currency*: every cited paper is checked against its primary page before use (see REUSE_MAP.md).
5. Every run records model, quant, runtime, date, sampling parameters (see `run.py` header).
