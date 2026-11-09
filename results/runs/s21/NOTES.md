2026-11-07 18:19 vkg/websearch.py search spacing 10 s -> 5 s at the user's request (S19 is closed; its hash list no longer binds). Bot checks are still never bypassed; prefetch stops after 5 consecutive failures. Prefetch restarted from the cache.
2026-11-07 19:06 vkg/s17_run.py items(): S21 set names added (load results/runs/s21/<name>.json).
2026-11-08 18:50 vkg/pod.py JUDGE_URL reads VKG_OLLAMA_URL (default unchanged 11435): after a reboot Windows reserved 11393-11492, so the project Ollama now runs on 11535 for S22 DEV runs. No behaviour change otherwise.
