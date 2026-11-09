# Short-answer rewrite on DEV (cached labels)

| variant | set | frozen gate: released / wrong | format gate |
|---|---|---|---|
| s19 | dev | 138 (0.460) / 1 wrong, 0 unl | 148 (0.493) / 2 wrong, 0 unl |
| s19short | dev | 139 (0.463) / 1 wrong, 0 unl | 149 (0.497) / 3 wrong, 0 unl |
| pin | mintaka_dev | 118 (0.590) / 11 wrong, 0 unl | 135 (0.675) / 11 wrong, 0 unl |
| pin | popqa_dev | 126 (0.420) / 36 wrong, 0 unl | 141 (0.470) / 39 wrong, 0 unl |
| pinshort | mintaka_dev | 129 (0.645) / 11 wrong, 0 unl | 136 (0.680) / 11 wrong, 0 unl |
| pinshort | popqa_dev | 124 (0.413) / 35 wrong, 0 unl | 137 (0.457) / 36 wrong, 0 unl |

## dev: s19short vs s19 (format gate)
new releases 1, lost 0
- NEW ('When (day, month, year), where, and by whom was the central sports clu', '1 February 1895', '1 February 1895, Stockholm, by Louis Zettersten and Pehr Ehnemark', False)

## mintaka_dev: pinshort vs pin (format gate)
new releases 1, lost 0

## popqa_dev: pinshort vs pin (format gate)
new releases 4, lost 8
- NEW ('What genre is The Car?', 'art rock, orchestral rock, lounge pop', 'thriller', False)
- NEW ('Who was the producer of The Fall?', 'Gub Neal and Julian Stevens', 'Tarsem Singh', False)
- LOST ('What is Brussels Capital Region the capital of?', 'Belgium', 'Burgundian Netherlands', False)
- LOST ('Who was the producer of O Dragão da Maldade Contra o Santo Guerreiro?', 'Zelito Viana', 'Glauber Rocha', False)
- LOST ('Who is the author of Aida?', 'Giuseppe Verdi', 'Linda Woolverton', False)
- LOST ('What genre is Egg?', 'Egg punk', 'progressive rock', False)
- LOST ('What genre is Nine?', 'pop-punk and pop rock', 'traditional music', False)
- LOST ('Who was the screenwriter for Final Destination?', 'Jeffrey Reddick', 'Jeffrey Reddick', True)
- LOST ('Who is the author of Tam Lin?', 'Pamela Dean', 'Pamela Dean', True)
- LOST ('In what country is Wright?', 'United States', 'United States of America', True)