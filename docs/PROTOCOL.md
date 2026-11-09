# Anti-circularity protocol

1. **Gold is never model-produced.** Synthetic gold = generator code; FaithEval gold = dataset labels; real-fact gold = hand-written
   and checked against stable facts. No LLM judge decides pass/fail in any reported headline number.
2. **Dev vs frozen.** Dev seeds may be inspected and used to change systems. A frozen seed is generated, then the code hash
   (`vkg/systems.py`, `vkg/tasks.py`, `vkg/llm.py`) is written to `docs/FREEZE.md` *before* the run, and the run happens once per
   model/config. Any later change to those files invalidates the freeze; a new frozen seed is needed.
3. **No tuning on a sample that is later reported as held-out.** FaithEval sample seed 0 counts as dev once any system change is
   made after viewing it; report seed 1 (disjoint sample) as the held-out figure.
4. **The generator and the checker may be the same model, but then the evaluation must not trust the checker.** VKG's own
   verifier outputs are system behaviour being measured, not evidence. Evidence = independent gold.
5. **Report failures with the same prominence as gains** (e.g. the conflict-detection miss, the grader bug found in v1).
6. **Every figure in a write-up is read from `results/runs/*.md|jsonl`**, with file name cited. No numbers from memory.
7. **Unverified citations** are labelled unverified. See `docs/REUSE_MAP.md`.
