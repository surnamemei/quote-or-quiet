# S66: gate G15, stress test of the Quote or Quiet service (plan, 2026-11-11, before any S66 run)

Gate G15: in a run of at least 1,000 mixed requests, no released statement lacks a machine-checked quote. T: 0 violations. N: 1,000 requests. V: registered here with the input set fixed before the run.
Service: tool/qoq_service.py as it stands (frozen system plus rule W1 for templated relations and rule R with the 4B judge for other questions; /bio with rule W4; /readings with W1). The 27B-judge rules validated in S57 to S63 are not in the service (the 27B does not fit on the card next to the 4B and Phi-4); this test is about the service's guarantee under load and odd input, not about which judge is best.
Inputs (results/runs/s66/g15_build.py, written before the run; 1,000): 300 PopQA questions used by no test, 200 Mintaka questions of non-generic types, 100 questions about invented names, 100 hostile inputs (empty, very long, prompt injection, non-English, markup, control characters), 100 opinion or advice questions, 100 /bio requests (20 for names with no page), 100 /readings requests (20 invalid).
Check (results/runs/s66/g15_run.py check, independent of the service): every released statement (Verified answer, /bio claim, Verified reading) must name a page of the local snapshot whose sha256 equals the reported one, its quote must occur verbatim in that page, the released answer or value must occur in the quote, and for /answer quote_checked must be true. A failure is a violation.
Also reported: HTTP 500 errors, timeouts (900 s), latency median and 95th percentile, releases on invented, hostile and opinion inputs (each is reported and inspected; a release there is not a violation if it passes the check, but is listed).
Predictions: 0 violations; at most 1% HTTP 500 or timeouts; median latency 5 to 30 s for /answer; no release for empty or control-character inputs; releases on invented names at most 2.
Pacing: /answer requests at least 10 s apart (live web search; bot checks are never bypassed).

Note (2026-11-11 18:2x): a first G15 run started at 17:57 when the G4 run had failed; it was stopped by me (to let the G4 run go first) and its service processes were ended; responses already received are kept (the driver resumes). Inputs and checks are unchanged.

Note (2026-11-11, evening): stopped at the user's request before the run started (no request sent).
