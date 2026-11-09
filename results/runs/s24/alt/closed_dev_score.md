# S24 closed-evidence score on closed_dev (n = 200; harness v2)

| outcome | count |
|---|---|
| lost | 56 |
| qualified_ok | 8 |
| unresolved_ok | 32 |
| verified_correct | 104 |

silent errors 0 of 200 (0.0%); completion (correct Verified/Derived + Qualified-ok) 112 of 200 (56.0%)

By expected state, question opening and output state:

| expected | question | state | outcomes |
|---|---|---|---|
| Derived | How old | Derived | verified_correct 32 |
| Qualified | In which | Qualified | qualified_ok 8 |
| Qualified | In which | Unresolved | lost 12 |
| Unresolved | What is | Unresolved | unresolved_ok 32 |
| Verified | In which | Unresolved | lost 12 |
| Verified | In which | Verified | verified_correct 72 |
| Verified | Who directed | Unresolved | lost 32 |

Silent errors:
