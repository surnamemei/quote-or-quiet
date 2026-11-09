# S30: verification gate that also accepts pinned web pages (plan, written 2026-11-09 before any scoring)

Motivation: the frozen gate (V1-V5) accepts a span only from the pinned Wikipedia snapshot (August 2025). Wikipedia is not always right and not always current, and an answer the readers agree on, that Phi-4 confirms, can still be refused because the snapshot does not contain it verbatim.

Variant W(m): unchanged support rule (>= 3 of the six reader outputs) and unchanged Phi-4 agreement. If the Wikipedia gate refuses, run the same deterministic checks (V2 verbatim, V3 type with T2, V4 period on the URL in place of the title, V2' whole number, V5 unit) on the text of the question's own kept web pages (the pages the web reader saw, contaminated pages and blocked domains already removed), with the page text pinned by sha256 in the certificate. Release if the span passes in pages from at least m distinct domains (registrable host, "www." removed). m = 2 is the main variant; m = 1 is reported.

Data (design sets only; nothing sealed): SimpleQA DEV 300 + FRESH 200, Mintaka DEV 200, PopQA DEV 300 (S19 outputs), and the S29 pilot 144 (free-search-mcp pool). The test sets already reported (FRESH-5, Mintaka test, PopQA test) are not used.

Pass rule, fixed now: pooled over the design sets, W(2) adds at least 20 releases and the gold-relative wrong rate among the added releases is at most 3% (the bar used for S23). Otherwise the variant is rejected. The added errors are listed for reading; no adjudication changes the verdict.
