# S65 gate G14: the quote check after three other models (2,001 sealed PopQA questions)

| model | answered | released (coverage) | quotes reviewed | misleading for both | decoys caught | gold-wrong releases | errors after truth check (unless both 'right') | error upper bound, all questions |
|---|---|---|---|---|---|---|---|---|
| llama3.1:8b | 972 | 305 (15.2%) | 300 | 3 (1.0%, upper 2.9%) | 10/10 | 19 | 0 | 0.18% (truth decoys 4/4; gold-right called wrong by both 0/8) |
| gemma3:12b | 1485 | 330 (16.5%) | 300 | 1 (0.3%, upper 1.8%) | 10/10 | 25 | 0 | 0.18% (truth decoys 4/4; gold-right called wrong by both 0/8) |
| mistral-nemo:12b | 1292 | 326 (16.3%) | 300 | 2 (0.7%, upper 2.4%) | 10/10 | 19 | 0 | 0.18% (truth decoys 4/4; gold-right called wrong by both 0/8) |
