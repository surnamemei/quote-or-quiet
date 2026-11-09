# S25: stronger veto (Qwen3.8-27B) on the added releases (plan written before running, 2026-11-09)

Gap addressed: raising coverage with pinned or independently retrieved pages adds releases at 6% to 21% error (S22, S23), too high for L2.
Hypothesis: the veto is the weak link; Phi-4 (14B) agrees with wrong candidates that a stronger local model would reject.
Test (design data only, DEV sets, no new generation of candidates): for every pre-veto release of the S19 (format gate), pin and indep variants on
mintaka_dev, popqa_dev and dev, ask Qwen3.8-27B (cautious prompt, on the combined passage of that variant). Policies: Phi-4 only (current), 27B only, both must agree.
Decision rule (fixed now): policy "both" or "27B only" counts as an improvement if, pooled over the DEV sets and over the variants pin and indep,
the wrong releases among those added beyond the frozen S19 system fall by at least half while at least 75% of the correct added releases survive.
If so, the next step is the same policy on FRESH-5 (design data) for the pin and indep variants; if not, the veto line stops.
Resources: the 27B runs only on candidates that already pass support and gate (a few hundred prompts), GPU lock protocol, idle priority.
