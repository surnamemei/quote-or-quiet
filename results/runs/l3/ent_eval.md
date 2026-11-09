# Goal B step 1 on DEV: stated entity vs rule-based layer

| set | releases | no entity parsed | 4B answer agrees with release |
|---|---|---|---|
| popqa_dev | 59 | 0 | 55 |
| mintaka_dev | 71 | 0 | 65 |
| dev | 138 | 0 | 129 |
| fresh | 83 | 0 | 79 |

## Q1 PopQA DEV, intended subject known

- releases with intended sense: 59
- 4B stated entity matches intended: 18
- rule-based: Qualified 17, of which sense = intended 10; Verified with release page core = intended core 27

## Q3 Unresolved releases on DEV (entity resolves to a sense page holding the answer?)

| set | question | release | graded | stated entity | resolved titles | holding the answer |
|---|---|---|---|---|---|---|
| popqa_dev | What is the capital of Mendoza? | Mendoza | True | Capital Department, Mendoza | Capital Department, Mendoza | Capital Department, Mendoza |
| mintaka_dev | Who is the main character of the first Yakuza game? | Kazuma Kiryu | True | Kazuma Kiryu | Kazuma Kiryu | Kazuma Kiryu |
| mintaka_dev | What clan does the witch Bayonetta belong to in Bayonetta? | Umbra Witch | True | Umbra Witch Clan |  |  |
| dev | Who was the person who spoke out against naming a new Imperi | Léon Gambetta | True | Léon Gambetta | Léon Gambetta | Léon Gambetta |
| dev | What signature piece of the MOBA did Scott Wilson discover o | Lucy in the Field with Fl | True | Lucy in the Field with Flowers |  |  |
| dev | In which general elections (year) was Makhdum Khusro Bakhtya | 2013 | True | Makhdum Khusro Bakhtiar |  |  |
| dev | What is the title of the second YouTube video ever uploaded? | My Snowboarding Skillz | True | My Snowboarding Skillz | My Snowboarding Skillz | My Snowboarding Skillz |
| dev | Who was the first person to be an American diplomatic minist | Eugene Schuyler | True | Eugene Schuyler | Eugene Schuyler | Eugene Schuyler |