# S24 closed-evidence score on closed_dev (n = 200; harness v2)

| outcome | count |
|---|---|
| lost | 79 |
| qualified_ok | 6 |
| unresolved_ok | 32 |
| verified_correct | 83 |

silent errors 0 of 200 (0.0%); completion (correct Verified/Derived + Qualified-ok) 89 of 200 (44.5%)

By expected state, question opening and output state:

| expected | question | state | outcomes |
|---|---|---|---|
| Derived | How old | Unresolved | lost 32 |
| Qualified | In which | Qualified | qualified_ok 6 |
| Qualified | In which | Unresolved | lost 14 |
| Unresolved | What is | Unresolved | unresolved_ok 32 |
| Verified | In which | Unresolved | lost 5 |
| Verified | In which | Verified | verified_correct 79 |
| Verified | Who directed | Unresolved | lost 28 |
| Verified | Who directed | Verified | verified_correct 4 |

Silent errors:
