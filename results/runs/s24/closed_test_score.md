# S24 closed-evidence score on closed_test (n = 1500; harness v2)

| outcome | count |
|---|---|
| lost | 447 |
| qualified_ok | 56 |
| unresolved_ok | 240 |
| verified_correct | 757 |

silent errors 0 of 1500 (0.0%); completion (correct Verified/Derived + Qualified-ok) 813 of 1500 (54.2%)

By expected state, question opening and output state:

| expected | question | state | outcomes |
|---|---|---|---|
| Derived | How old | Derived | verified_correct 217 |
| Derived | How old | Unresolved | lost 23 |
| Qualified | In which | Qualified | qualified_ok 56 |
| Qualified | In which | Unresolved | lost 94 |
| Unresolved | What is | Unresolved | unresolved_ok 240 |
| Verified | In which | Unresolved | lost 102 |
| Verified | In which | Verified | verified_correct 528 |
| Verified | Who directed | Unresolved | lost 228 |
| Verified | Who directed | Verified | verified_correct 12 |

Silent errors:
