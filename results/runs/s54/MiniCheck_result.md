# S54: MiniCheck-Flan-T5-Large on our reviewer labels

| Set | Checker | AUROC for 'states' | accepted | measure among accepted |
|---|---|---|---|---|
| heldout (n=939) | MiniCheck, threshold 0.5 | 0.963 | 749 (79.8%) | not 'states': 31 (4.1%, upper 5.8%) |
| heldout (n=939) | small trained judge, 0.5 | 0.988 | 744 (79.2%) | not 'states': 19 (2.6%, upper 4.0%) |
| heldout (n=939) | MiniCheck at the small judge's acceptance (744) |  | 744 (79.2%) | not 'states': 31 (4.2%, upper 5.9%) |
| mintaka (n=361) | MiniCheck, threshold 0.5 | 0.890 | 190 (52.6%) | misleading: 25 (13.2%, upper 18.8%) |
| mintaka (n=361) | MiniCheck at the small judge's acceptance (154) |  | 154 (42.7%) | misleading: 7 (4.5%, upper 9.1%) |
