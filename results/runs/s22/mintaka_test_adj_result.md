# S22 blind web adjudication on mintaka_test (fresh agents, sheet only; quote-checked)

| kind | n | gold wrong | answer wrong | both acceptable | matches gold | ambiguous question | cannot tell | removed |
|---|---|---|---|---|---|---|---|---|
| system | 63 | 29 | 14 | 4 | 1 | 9 | 6 | 34 (0.54) |
| decoy_baseline_wrong | 63 | 19 | 24 | 1 | 0 | 14 | 5 | 20 (0.32) |
| decoy_system_correct | 63 | 0 | 2 | 0 | 61 | 0 | 0 | 61 (0.97) |
| decoy_injected_false | 62 | 0 | 62 | 0 | 0 | 0 | 0 | 0 (0.00) |

Validity (injected-false called answer wrong): 62 / 62 = 1.000 -> VALID
System errors kept after adjudication: k_adj = 29 of 63

## System rows

- r4 What style of jazz was Lee Morgan known for? | gold bebop | Bebop | ans Hard bop | **cannot tell** | A=gold wrong; B=cannot tell
- r5 Who is the all time leading scorer? | gold Adam Vinatieri | ans LeBron James | **ambiguous question** | A=ambiguous question; B=ambiguous question
- r9 Who led Germany after Adolf Hitler? | gold Theodor Heuss | ans Karl Dönitz | **ambiguous question** | A=ambiguous question; B=ambiguous question
- r11 What color was the Statue of Liberty originally? | gold brown | Brown | ans copper | **answer wrong** | A=answer wrong; B=both acceptable
- r13 Who holds the record for most triple doubles all time? | gold Oscar Robertson | Oscar Robinson | ans Russell Westbrook | **gold wrong** | A=gold wrong; B=gold wrong
- r14 What is the most recent title in the Resident Evil series? | gold Resident Evil Village | ans Resident Evil Requiem | **gold wrong** | A=gold wrong; B=gold wrong
- r16 What year did the Baftas start? | gold 1947 | ans 1949 | **ambiguous question** | A=ambiguous question; B=ambiguous question
- r18 What is the longest field goal made in a Super Bowl game? | gold 54 yards | ans 57 yards | **gold wrong** | A=gold wrong; B=gold wrong
- r20 What year was Meryl Streep born? | gold 1939 | ans 1949 | **cannot tell** | A=gold wrong; B=cannot tell
- r21 How many active NBA franchises have no NBA Finals appearances? | gold 6 | ans 5 | **gold wrong** | A=gold wrong; B=gold wrong
- r35 Who won the popular vote in 2000 for president? | gold George W. Bush | George W Bush | ans Al Gore | **gold wrong** | A=gold wrong; B=gold wrong
- r37 Who does Rocky Balboa fight in Rocky III? | gold Apollo Creed | ans Clubber Lang | **both acceptable** | A=gold wrong; B=both acceptable
- r39 How many Super Bowls have the rams won? | gold 1 | ans 2 | **gold wrong** | A=gold wrong; B=gold wrong
- r44 Who has the most passes completed? | gold Drew Brees | ans Tom Brady | **gold wrong** | A=gold wrong; B=gold wrong
- r47 Who has won the most Grammy Awards? | gold Georg Solti | ans Beyoncé | **gold wrong** | A=gold wrong; B=gold wrong
- r50 What was the last movie Clint Eastwood acted in? | gold The Mule | ans Cry Macho (2021) | **gold wrong** | A=gold wrong; B=gold wrong
- r51 Is Okja a pig or hippo? | gold Both | ans pig | **gold wrong** | A=gold wrong; B=gold wrong
- r52 Which Black Eyed Peas song won a 2005 Grammy? | gold My Humps | ans Let's Get It Started | **gold wrong** | A=gold wrong; B=gold wrong
- r56 Who designed Mount Rushmore? | gold Lincoln Borglum | Gutszon and Lincoln Borglum | ans Gutzon Borglum | **answer wrong** | A=answer wrong; B=cannot tell
- r60 Who is the president of the Philippines? | gold Rodrigo Duterte | ans Bongbong Marcos | **gold wrong** | A=gold wrong; B=gold wrong
- r62 What is another name for an instrument called Harp by blues musicians? | gold harmonica | ans Blues harp | **answer wrong** | A=answer wrong; B=matches gold
- r75 Who was Egypt's first pharaoh? | gold Menes | ans Narmer | **cannot tell** | A=both acceptable; B=cannot tell
- r89 Which ancient civilization followed after the Mycenaean civilization? | gold Ancient Greece | Ancient Greek Civilization | ans The Greek Dark Ages | **answer wrong** | A=answer wrong; B=answer wrong
- r90 What is Japan's Senate called? | gold House of Councillors | house of councilors | ans Senate | **answer wrong** | A=answer wrong; B=gold wrong
- r92 What city hosted the Super Bowl the most times? | gold Miami | ans New Orleans | **cannot tell** | A=both acceptable; B=cannot tell
- r115 Between what years was the Franco-Dutch war fought? | gold 1672 - 1678 | 1672 to 1678 | ans 1678 | **answer wrong** | A=answer wrong; B=answer wrong
- r122 How many Grammys has Taylor Swift won? | gold 10 | ans 14 | **cannot tell** | A=gold wrong; B=cannot tell
- r123 How many sons did Martin Luther King junior have? | gold 4 | ans 2 | **gold wrong** | A=gold wrong; B=gold wrong
- r127 What does the name of Korean boy band B. T. S. stand for? | gold BTS | Bangtan Boys | ans Bulletproof Boy Scouts | **matches gold** | A=matches gold; B=matches gold
- r130 Who is the current president of Lebanon? | gold Michel Aoun | ans Joseph Aoun | **gold wrong** | A=gold wrong; B=gold wrong
- r133 Who won the 2008 NCAA BCS Football Championship? | gold Florida Gators | ans LSU Tigers | **ambiguous question** | A=ambiguous question; B=ambiguous question
- r144 Which party won the state elections in North Carolina in 2016? | gold Republican Party | ans Democratic Party | **ambiguous question** | A=ambiguous question; B=ambiguous question
- r148 How many electoral votes did Hillary Clinton receive in the 2016 Election? | gold 232 | ans 227 | **gold wrong** | A=gold wrong; B=gold wrong
- r149 What dynasty was Cleopatra apart of? | gold Macedonia | Macedonian | ans Ptolemaic dynasty | **both acceptable** | A=both acceptable; B=both acceptable
- r159 What is the name of the first book in the Patternist series by Octavia East Butler? | gold Wild Seed | ans Patternmaster | **ambiguous question** | A=ambiguous question; B=ambiguous question
- r160 How many years has Angela Merkel been a chancellor of Germany? | gold 15 | ans 16 | **gold wrong** | A=gold wrong; B=gold wrong
- r162 What weapon does Tifa from Final Fantasy VII use? | gold Fists | ans gloves | **both acceptable** | A=matches gold; B=both acceptable
- r174 When did Pizarro reach the Inca territory? | gold 1532 | ans 1526 | **answer wrong** | A=answer wrong; B=answer wrong
- r176 What is it called when you walk or run while bouncing the ball? | gold dribbling | ans A running bounce | **answer wrong** | A=answer wrong; B=answer wrong
- r179 Who was the number one pick in the NBA draft in 1988? | gold Michael Olowokandi | ans Danny Manning | **gold wrong** | A=gold wrong; B=gold wrong
- r182 What actor has the most Oscar nominations for his performances? | gold Jack Nicholson | ans Meryl Streep | **answer wrong** | A=answer wrong; B=both acceptable
- r186 Where did Che Guevara die? | gold Bolivia | ans La Higuera | **answer wrong** | A=both acceptable; B=answer wrong
- r187 Who is the lead singer of Smash Mouth? | gold Steve Harwell | Steven Harwell | ans Zach Goode | **gold wrong** | A=gold wrong; B=gold wrong
- r190 Who is the governor of Arkansas? | gold Asa Hutchinson | ans Sarah Huckabee Sanders | **gold wrong** | A=gold wrong; B=gold wrong
- r197 How many championships does LeBron James have? | gold 3 | ans 4 | **gold wrong** | A=gold wrong; B=gold wrong
- r198 In what year did Operation Desert Storm begin? | gold 1990 | ans 1991 | **gold wrong** | A=gold wrong; B=gold wrong
- r199 What is the youngest age to be president of the United States? | gold 35 | ans 42 | **ambiguous question** | A=ambiguous question; B=ambiguous question
- r204 What dynasty was Cleopatra a part of? | gold Macedonian dynasty | ans Ptolemaic dynasty | **cannot tell** | A=cannot tell; B=both acceptable
- r207 When did the Mongolian Empire end? | gold 1368 | 1368 AD | ans 14th century | **answer wrong** | A=answer wrong; B=answer wrong
- r209 Who is the starting quarterback for the Denver Broncos? | gold Jeff Driskel | ans Bo Nix | **gold wrong** | A=gold wrong; B=gold wrong
- r213 When did Kim Stanley Robinson publish the first book in the Mars trilogy? | gold 1993 | ans 1992 | **gold wrong** | A=gold wrong; B=gold wrong
- r219 What was the first video game created? | gold Pong | ans Tennis for Two | **ambiguous question** | A=ambiguous question; B=ambiguous question
- r220 What position did the creator of the Game Boy have at Nintendo? | gold janitor | A janitor | ans designer | **answer wrong** | A=answer wrong; B=answer wrong
- r224 Number of movies in the Thor franchise? | gold 3 | ans 9 | **answer wrong** | A=answer wrong; B=answer wrong
- r225 Who is the current manager of the Milwaukee Brewers? | gold Craig Counsell | ans Pat Murphy | **gold wrong** | A=gold wrong; B=gold wrong
- r227 Who is the president of Kenya? | gold Uhuru Kenyatta | ans William Ruto | **gold wrong** | A=gold wrong; B=gold wrong
- r230 What year was Minecraft first released? | gold 2011 | ans 2009 | **both acceptable** | A=both acceptable; B=both acceptable
- r231 Who has the most career passing yards in the NFL? | gold Drew Brees | ans Tom Brady | **gold wrong** | A=gold wrong; B=gold wrong
- r232 What is the population of Parma, Ohio? | gold 78103 | ans 81,146 | **answer wrong** | A=answer wrong; B=answer wrong
- r233 When did Pokemon red and blue come out in the US? | gold 1996-02-27 | 27-Feb-96 | ans September 28, 1998 | **gold wrong** | A=gold wrong; B=gold wrong
- r234 Who is the current president of Kenya? | gold Uhuru Kenyatta | ans William Ruto | **gold wrong** | A=gold wrong; B=gold wrong
- r241 Who hosted the 2020 MTV Movie Awards? | gold Keke Palmer | ans Vanessa Hudgens | **gold wrong** | A=gold wrong; B=gold wrong
- r243 Who won the Grammy's Album of the Year in 2017? | gold 24K Magic | ans Adele | **ambiguous question** | A=ambiguous question; B=both acceptable

## Injected-false not called answer wrong


## System-correct called answer wrong

- r98 When was Moby Dick published? | gold 1851-10 | October 1851 | ans 1851 | A=answer wrong; B=answer wrong
- r110 When was World of Warcraft released? | gold 2004-11-23 | 23-Nov-04 | ans 2004 | A=answer wrong; B=answer wrong

## Baseline-wrong removed

- r19 How many points did a touchdown originally count for? | gold 4 | ans 2 points | gold wrong | A=gold wrong; B=gold wrong
- r29 Who is currently leading the AFC South? | gold Tennessee Titans | ans The Jacksonville Jaguars are currently leading the AFC South with a 6-2 record. | gold wrong | A=gold wrong; B=gold wrong
- r38 Where do the Texans play home games? | gold NRG Stadium | NRG stadium | ans Reliant Stadium in Houston, TX | both acceptable | A=both acceptable; B=gold wrong
- r66 Who is the leader of Paraguay? | gold Mario Abdo Benítez | Mario Abdo Benitez | ans Pedro Alliana | gold wrong | A=gold wrong; B=gold wrong
- r71 How old is Christian Slater? | gold 52 | ans 57 | gold wrong | A=gold wrong; B=gold wrong
- r78 Who designed Lincoln Memorial? | gold Daniel Chester French | ans Henry Bacon | gold wrong | A=gold wrong; B=gold wrong
- r79 Which musician has won the most Grammy Awards of all time? | gold Georg Solti | ans Beyoncé | gold wrong | A=gold wrong; B=gold wrong
- r103 How many Grammy Awards has Beyoncé won? | gold 24 | ans 35 | gold wrong | A=gold wrong; B=gold wrong
- r109 Who is the starting quarterback for the Carolina Panthers? | gold Teddy Bridgewater | ans Bryce Young | gold wrong | A=gold wrong; B=gold wrong
- r111 Who won the Oscar for Best Supporting Actor this year? | gold Brad Pitt | ans Sean Penn | gold wrong | A=gold wrong; B=gold wrong
- r137 Who is the head coach of the Denver Broncos? | gold Vic Fangio | ans Sean Payton | gold wrong | A=gold wrong; B=gold wrong
- r138 What city has the highest population in the world? | gold Tokyo | ans Jakarta | gold wrong | A=gold wrong; B=gold wrong
- r147 What is the largest populated city in the world? | gold Tokyo | ans Jakarta | gold wrong | A=gold wrong; B=gold wrong
- r156 When was Raleigh founded? | gold 1972 | ans 1792 | gold wrong | A=gold wrong; B=gold wrong
- r161 How many books are in the Hunger Games series? | gold 3 | ans 5 | gold wrong | A=gold wrong; B=gold wrong
- r164 Who won the Oscar for Best Actor in a Supporting Role this year? | gold Brad Pitt | ans Sean Penn | gold wrong | A=gold wrong; B=gold wrong
- r171 What is the name of Metallica's latest album? | gold Spit Out the Bone | ans 72 Seasons | gold wrong | A=gold wrong; B=gold wrong
- r177 How old is Jennifer Lawrence? | gold 31 | 31 Years | ans 36 | gold wrong | A=gold wrong; B=gold wrong
- r183 Who is the president of Niger? | gold Mahamadou Issoufou | ans Abdourahamane Tchiani is the president of Niger. | gold wrong | A=gold wrong; B=gold wrong
- r202 Who is the youngest Grammy winner ever? | gold LeAnn Rimes | ans Aura V | gold wrong | A=gold wrong; B=gold wrong