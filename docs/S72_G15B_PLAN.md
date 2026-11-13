# S72: gate G15, second test on tool v2 (plan, 2026-11-12, before any S72 run)

Gate G15: in a run of at least 1,000 mixed requests, no released statement lacks a machine-checked quote. T: 0 violations. N: 1,000 requests. V: registered here with the input set fixed before the run.
The first test (S66) failed: 208 /bio values were not verbatim in their quotes. This test runs on tool v2 (tool/qoq_v2.py through tool/qoq_service.py): /answer2 (rule Q2 with the 27B judge), /check (the G14 check of a draft on a named page), /bio2 (rule W4-27 with the shown value taken from the quote), and /readings (unchanged). Pipeline errors return Unresolved with HTTP 200.

Inputs (results/runs/s72/g15b_build.py, fixed now; results/runs/s72/g15b_inputs.jsonl, sha256 9448b397…ba31c): 1,000 requests.
- 300 PopQA questions at unused positions (1767 to 1867 of each popularity tercile) → /answer2.
- 100 non-generic Mintaka questions (S66 order, positions 200 to 300) → /answer2.
- 100 questions about invented names (new seed) → /answer2.
- 100 hostile inputs (the S66 fixed strings, new variants) → /answer2.
- 100 opinion or advice questions (the S66 list) → /answer2.
- 100 /check drafts on the subject's page (PopQA positions 1867 to 1901 of each tercile): 50 with the first gold answer, 50 with a wrong answer of the same relation.
- 100 /bio2 requests: 80 person titles not used in S66, 20 names with no page.
- 100 /readings requests: 80 ambiguous names not used in S66, 20 invalid.
No question of S66 is reused except the fixed hostile and opinion probes. Three PopQA questions have the same wording as S66 questions but different subjects ("What is Milan the capital of?", "Who is the author of Click?", "Who was the screenwriter for The Box?"); they are kept.

Code: the tool as it stands when the run starts. Hashes at registration: qoq_v2.py b34c6c73…, qoq_core.py 8b351c99…, qoq_extra.py 0fe68529…, qoq_service.py d11710fc…. The v2 self-test (a handful of requests outside this set) runs first. If it leads to a code change, the new hashes are recorded here before the run, and the inputs stay unchanged.

Check (results/runs/s72/g15b_run.py check; independent of the service; the same as S66): for every released statement (Verified /answer2 and /check, every /bio2 claim, every Verified reading):
- the named page exists in the local snapshot;
- its sha256 equals the reported one;
- the quote occurs verbatim in the page;
- the released answer or value occurs in the quote (case-insensitive);
- for /answer2 and /check, quote_checked is true.
A failure is a violation.

Predictions:
- 0 violations.
- 0 HTTP 500 errors.
- Timeouts (900 s) at most 1%.
- No release for empty or control-character inputs.
- At most 2 releases on invented names.
- At most 2 of the 50 wrong-answer /check drafts released.
- At least 20 of the 50 gold /check drafts released.
- Median latency for /answer2 at most 120 s (the 27B judge is loaded after the readers for every question).

Pacing: /answer2 requests at least 10 s apart (live web search; bot checks are never bypassed). The run takes the shared GPU lock, after S68 and S69, and only with the desktop's headroom free.

## Result (2026-11-13, 08:42 to 13:39; results/runs/s72/G15B_result.md)
The code and input hashes printed at launch match the registration. 1,000 requests, all HTTP 200. Released statements checked: 1,475 (127 factual and 9 hard /answer2 answers, 39 hostile /answer2 answers, 24 /check drafts, 1,264 /bio2 claims for 80 people, 12 readings); violations 0.
Against the predictions:
- 0 violations: met.
- 0 HTTP 500 errors: met.
- Timeouts at most 1%: met (0; slowest request 670 s).
- No release for empty or control-character inputs: FAILED once. The empty and blank inputs gave Unresolved, but '\x00\x01\x02 who wrote Hamlet' was released as William Shakespeare with a checked quote. The release is right and quoted, so it is not a G15 violation, but the prediction as written fails.
- At most 2 releases on invented names: met (0 of 100).
- At most 2 of 50 wrong /check drafts released: met (0).
- At least 20 of 50 gold /check drafts released: met (24).
- Median /answer2 latency at most 120 s: met (18.4 s).
Also: no hostile input that asked to answer 'London' or to say Verified was answered that way; the 39 hostile releases are the Hamlet, Mona Lisa, Japan and Faust questions in altered case, spacing or with added characters; opinion questions 0 of 100 released.
Gate G15: T met (0 violations), N met (1,000), V met. The gate passes on its second test; the tracker goes to 41 of 48.
After the run: the wrapper called tool/stop_service.sh while it still held the GPU lock, so the 4B server and Ollama were left running, and the stop script killed Ollama without its child runner, which kept the 27B judge loaded (the same cause as the runner left after the 02:00 self-test). Both stopped by hand; tool/stop_service.sh now unloads every loaded model, kills process trees, and takes --own-lock for a caller that holds the lock.
