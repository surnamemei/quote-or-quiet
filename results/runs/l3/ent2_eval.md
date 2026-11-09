# Closed-choice entity (ent_gen2) on DEV

- items asked (multi-sense mention): popqa_dev 20, mintaka_dev 31, dev 18, fresh 6
- pick = none/invalid: popqa_dev 0, mintaka_dev 3, dev 5, fresh 2
- pick agrees with rule sense: popqa_dev 14, mintaka_dev 20, dev 11, fresh 3

PopQA DEV with intended sense, asked: 20: pick=intended 12, rule=intended 10, pick right where rule wrong 3, rule right where pick wrong 1
Verified releases where the pick disagrees with the rule's page: 4 (graded wrong 0, graded correct 4)

graded-wrong releases that were asked:
- popqa_dev | In what country is Dobra River? | Qualified | rule=Dobra (Kupa) | pick=Dobra (Kupa) | intended=Dobra River (Lotru)
- popqa_dev | What is Jordan the capital of? | Qualified | rule=Jordan | pick=Jordan | intended=Jordan, Guimaras
- popqa_dev | What genre is Legion? | Qualified | rule=Legion (TV series) | pick=Legion (TV series) | intended=Legion (Blatty novel)