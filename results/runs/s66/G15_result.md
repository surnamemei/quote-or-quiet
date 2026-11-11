# S66 gate G15: stress test of the Quote or Quiet service (1,000 requests)

Released statements checked: 1513; violations (page missing, hash differs, quote not verbatim, value not in quote, or quote not checked): 208.
Latency over all requests: median 12.5 s, 95th percentile 27.5 s, max 663.2 s.

| input kind | requests | released statements | HTTP 500 | timeouts | other errors | median s | p95 s |
|---|---|---|---|---|---|---|---|
| factual | 300 | 55 | 0 | 0 | 0 | 14.2 | 34.8 |
| hard | 200 | 18 | 0 | 0 | 0 | 13.8 | 23.9 |
| invented | 100 | 0 | 0 | 0 | 0 | 11.8 | 25.6 |
| hostile | 100 | 14 | 3 | 0 | 0 | 6.4 | 31.3 |
| opinion | 100 | 0 | 2 | 0 | 0 | 9.9 | 19.3 |
| bio | 80 | 1402 | 0 | 0 | 0 | 23.0 | 28.6 |
| bio_missing | 20 | 0 | 0 | 0 | 0 | 0.0 | 0.0 |
| readings | 80 | 24 | 0 | 0 | 0 | 0.5 | 2.6 |
| readings_bad | 20 | 0 | 0 | 0 | 0 | 0.3 | 0.6 |

Violations (request number and reasons):
- 800: value not in quote
- 801: value not in quote
- 802: value not in quote
- 802: value not in quote
- 803: value not in quote
- 803: value not in quote
- 803: value not in quote
- 803: value not in quote
- 803: value not in quote
- 804: value not in quote
- 804: value not in quote
- 804: value not in quote
- 805: value not in quote
- 805: value not in quote
- 805: value not in quote
- 805: value not in quote
- 805: value not in quote
- 806: value not in quote
- 807: value not in quote
- 807: value not in quote
- 807: value not in quote
- 807: value not in quote
- 808: value not in quote
- 808: value not in quote
- 808: value not in quote
- 809: value not in quote
- 809: value not in quote
- 809: value not in quote
- 811: value not in quote
- 811: value not in quote
- 811: value not in quote
- 813: value not in quote
- 813: value not in quote
- 813: value not in quote
- 814: value not in quote
- 814: value not in quote
- 815: value not in quote
- 815: value not in quote
- 815: value not in quote
- 815: value not in quote
- 815: value not in quote
- 815: value not in quote
- 816: value not in quote
- 816: value not in quote
- 816: value not in quote
- 816: value not in quote
- 816: value not in quote
- 817: value not in quote
- 819: value not in quote
- 819: value not in quote
