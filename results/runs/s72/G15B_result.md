# S72 gate G15, second test: stress test of Quote or Quiet v2 (1,000 requests)

Released statements checked: 1475; violations (page missing, hash differs, quote not verbatim, value not in quote, or quote not checked): 0.
Latency over all requests: median 16.8 s, 95th percentile 40.5 s, max 669.6 s.

| input kind | requests | released statements | HTTP 500 | timeouts | other errors | median s | p95 s |
|---|---|---|---|---|---|---|---|
| factual | 300 | 127 | 0 | 0 | 0 | 21.6 | 40.7 |
| hard | 100 | 9 | 0 | 0 | 0 | 20.2 | 32.5 |
| invented | 100 | 0 | 0 | 0 | 0 | 18.5 | 36.0 |
| hostile | 100 | 39 | 0 | 0 | 0 | 7.7 | 22.0 |
| opinion | 100 | 0 | 0 | 0 | 0 | 7.8 | 14.6 |
| check_gold | 50 | 24 | 0 | 0 | 0 | 0.5 | 0.7 |
| check_wrong | 50 | 0 | 0 | 0 | 0 | 0.1 | 0.2 |
| bio | 80 | 1264 | 0 | 0 | 0 | 38.4 | 48.1 |
| bio_missing | 20 | 0 | 0 | 0 | 0 | 0.0 | 0.1 |
| readings | 80 | 12 | 0 | 0 | 0 | 0.5 | 3.0 |
| readings_bad | 20 | 0 | 0 | 0 | 0 | 0.3 | 0.6 |
