# S24 closed-evidence score on closed_test2 (n = 1500; harness v2)

| outcome | count |
|---|---|
| lost | 406 |
| qualified_ok | 70 |
| unresolved_ok | 240 |
| verified_correct | 784 |

silent errors 0 of 1500 (0.0%); completion (correct Verified/Derived + Qualified-ok) 854 of 1500 (56.9%)

By expected state, question opening and output state:

| expected | question | state | outcomes |
|---|---|---|---|
| Derived | How old | Derived | verified_correct 225 |
| Derived | How old | Unresolved | lost 14 |
| Derived | How old | Verified | verified_correct 1 |
| Qualified | In which | Qualified | qualified_ok 70 |
| Qualified | In which | Unresolved | lost 80 |
| Unresolved | What is | Unresolved | unresolved_ok 240 |
| Verified | In which | Unresolved | lost 104 |
| Verified | In which | Verified | verified_correct 526 |
| Verified | Who directed | Unresolved | lost 208 |
| Verified | Who directed | Verified | verified_correct 32 |

Silent errors:
