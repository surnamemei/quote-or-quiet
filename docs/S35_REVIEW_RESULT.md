# S35 blind review of random releases (two model reviewers per row, no gold shown)

Decoys (injected false): called wrong by A 15/15, by B 15/15, by both 15

Sample rows: 180; reviewer verdicts identical on 180

Per set (verdict = 'wrong' if both reviewers say wrong; 'wrong, disputed' if one does; ambiguous = either says 'correct for one reading'):

| set | n | true wrong (both) | wrong by either | ambiguous | gold-relative wrong | gold-wrong while reviewers say correct |
|---|---|---|---|---|---|---|
| fresh5 | 60 | 0/60 = 0.0% [0.0, 6.0] | 0/60 = 0.0% [0.0, 6.0] | 0/60 = 0.0% [0.0, 6.0] | 2/60 = 3.3% [0.4, 11.5] | 2 |
| mintaka_test | 60 | 0/60 = 0.0% [0.0, 6.0] | 0/60 = 0.0% [0.0, 6.0] | 1/60 = 1.7% [0.0, 8.9] | 4/60 = 6.7% [1.8, 16.2] | 4 |
| popqa_test | 60 | 0/60 = 0.0% [0.0, 6.0] | 0/60 = 0.0% [0.0, 6.0] | 3/60 = 5.0% [1.0, 13.9] | 3/60 = 5.0% [1.0, 13.9] | 3 |
| ALL | 180 | 0/180 = 0.0% [0.0, 2.0] | 0/180 = 0.0% [0.0, 2.0] | 4/180 = 2.2% [0.6, 5.6] | 9/180 = 5.0% [2.3, 9.3] | 9 |

Rows where a reviewer says wrong, or gold disagrees, or ambiguous:

- [popqa_test] gold-grade True | A correct for one reading | B correct for one reading | gold ['United Kingdom', '🇬🇧'] | Right for Cambridge, England (UK); wrong for Cambridge, Massachusetts and others.
- [popqa_test] gold-grade False | A correct | B correct | gold ['politician', 'political leader'] | Lawyer (also politician).
- [popqa_test] gold-grade True | A correct for one reading | B correct for one reading | gold ['Nick Hornby', 'Nicholas Peter John Hornby'] | Right for 1997 UK film; 2005 US film written by Lowell Ganz and Babaloo Mandel.
- [mintaka_test] gold-grade False | A correct | B correct | gold ['1990'] | 17 January 1991.
- [mintaka_test] gold-grade False | A correct | B correct | gold ['Oscar Robertson', 'Oscar Robinson'] | Westbrook holds the NBA career regular-season record.
- [popqa_test] gold-grade False | A correct | B correct | gold ['politician', 'political leader'] | GP by trade; also a Luxembourgish DP politician.
- [mintaka_test] gold-grade False | A correct | B correct | gold ['10'] | 14 as of Nov 2026 (no wins at 2025/2026 ceremonies); time-sensitive.
- [mintaka_test] gold-grade False | A correct for one reading | B correct for one reading | gold ['3'] | 9 = MCU films featuring Thor; the Thor-titled film series has only 4.
- [fresh5] gold-grade False | A correct | B correct | gold ['2014'] | 2014 and 2023 (2023 absence fixed by 2022 qualifying).
- [popqa_test] gold-grade False | A correct for one reading | B correct for one reading | gold ['James Toback', 'James Lee Toback'] | Right for the 2016 film; the 1983 'Exposed' was written by James Toback.
- [fresh5] gold-grade False | A correct | B correct | gold ['Gerad Yakubu Andan'] | Name matches.
