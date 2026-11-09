# S22 adjudication pilot on the S21 Mintaka sheet (blind web check by a fresh agent; descriptive)

| kind | n | gold wrong | answer wrong | both acceptable | ambiguous question | cannot tell | removed share |
|---|---|---|---|---|---|---|---|
| system | 28 | 17 | 3 | 7 | 1 | 0 | 0.86 |
| decoy_baseline_wrong | 28 | 6 | 15 | 6 | 1 | 0 | 0.43 |
| decoy_system_correct | 28 | 0 | 0 | 28 | 0 | 0 | 1.00 |

System errors kept after adjudication: 4 of 28 (would-be adjudicated k; S21 coverage 0.310 fails regardless).
Missing verdict rows: []

System rows:

- Who has the most career passing yards in the NFL? | gold Drew Brees | ans Tom Brady | **gold wrong** | https://www.espn.com/nfl/story/_/id/32334871/tom-brady-overtakes-drew-brees-claim-nfl-career-passing-yards-record
- What dynasty was Cleopatra apart of? | gold Macedonia | Macedonian | ans Ptolemaic dynasty | **both acceptable** | https://en.wikipedia.org/wiki/Ptolemaic_dynasty
- What dynasty was Cleopatra a part of? | gold Macedonian dynasty | ans Ptolemaic dynasty | **both acceptable** | https://en.wikipedia.org/wiki/Ptolemaic_dynasty
- Which Black Eyed Peas song won a 2005 Grammy? | gold My Humps | ans Let's Get It Started | **gold wrong** | https://www.grammy.com/awards/categories/rap-duo-group-performance/2005/
- How many active NBA franchises have no NBA Finals appearances? | gold 6 | ans 5 | **gold wrong** | https://www.si.com/nba/which-nba-teams-have-never-won-a-championship-running-through-the-full-list-of-have-nots
- When did Pizarro reach the Inca territory? | gold 1532 | ans 1526 | **ambiguous question** | https://en.wikipedia.org/wiki/Spanish_conquest_of_the_Inca_Empire
- How many Grammys has Taylor Swift won? | gold 10 | ans 14 | **gold wrong** | https://en.wikipedia.org/wiki/List_of_awards_and_nominations_received_by_Taylor_Swift
- Who is the president of the Philippines? | gold Rodrigo Duterte | ans Bongbong Marcos | **gold wrong** | https://en.wikipedia.org/wiki/Bongbong_Marcos
- Who holds the record for most triple doubles all time? | gold Oscar Robertson | Oscar Robinson | ans Russell Westbrook | **gold wrong** | https://en.wikipedia.org/wiki/Russell_Westbrook
- In what year did Operation Desert Storm begin? | gold 1990 | ans 1991 | **gold wrong** | https://en.wikipedia.org/wiki/Gulf_War
- Who does Rocky Balboa fight in Rocky III? | gold Apollo Creed | ans Clubber Lang | **gold wrong** | https://en.wikipedia.org/wiki/Rocky_III
- Number of movies in the Thor franchise? | gold 3 | ans 9 | **answer wrong** | https://en.wikipedia.org/wiki/Thor_(film_series)
- Who won the Grammy's Album of the Year in 2017? | gold 24K Magic | ans Adele | **both acceptable** | https://en.wikipedia.org/wiki/59th_Annual_Grammy_Awards
- How many Super Bowls have the rams won? | gold 1 | ans 2 | **gold wrong** | https://en.wikipedia.org/wiki/Super_Bowl_LVI
- What is the longest field goal made in a Super Bowl game? | gold 54 yards | ans 57 yards | **gold wrong** | https://en.wikipedia.org/wiki/Super_Bowl_LVIII
- Who was the number one pick in the NBA draft in 1988? | gold Michael Olowokandi | ans Danny Manning | **gold wrong** | https://en.wikipedia.org/wiki/1988_NBA_draft
- Who is the president of Kenya? | gold Uhuru Kenyatta | ans William Ruto | **gold wrong** | https://en.wikipedia.org/wiki/William_Ruto
- Who is the current president of Kenya? | gold Uhuru Kenyatta | ans William Ruto | **gold wrong** | https://en.wikipedia.org/wiki/William_Ruto
- Who is the governor of Arkansas? | gold Asa Hutchinson | ans Sarah Huckabee Sanders | **gold wrong** | https://en.wikipedia.org/wiki/Sarah_Huckabee_Sanders
- What is another name for an instrument called Harp by blues musicians? | gold harmonica | ans blues harp | **answer wrong** | https://en.wikipedia.org/wiki/Harmonica
- What style of jazz was Lee Morgan known for? | gold bebop | Bebop | ans hard bop | **both acceptable** | https://www.britannica.com/biography/Lee-Morgan
- What is the name of the first book in the Patternist series by Octavia East Butler? | gold Wild Seed | ans Patternmaster | **both acceptable** | https://en.wikipedia.org/wiki/Patternist_series
- Who is the current manager of the Milwaukee Brewers? | gold Craig Counsell | ans Pat Murphy | **gold wrong** | https://en.wikipedia.org/wiki/Pat_Murphy_(baseball)
- Who was Egypt's first pharaoh? | gold Menes | ans Narmer | **both acceptable** | https://en.wikipedia.org/wiki/Menes
- What is the most recent title in the Resident Evil series? | gold Resident Evil Village | ans Resident Evil Requiem | **answer wrong** | https://www.businesswire.com/news/home/20250609946595/en/Capcoms-Resident-Evil-Requiem-the-Latest-Title-in-the-Series-Set-to-Release-on-February-27-2026
- Who is the current president of Lebanon? | gold Michel Aoun | ans Joseph Aoun | **gold wrong** | https://en.wikipedia.org/wiki/Joseph_Aoun
- How many championships does LeBron James have? | gold 3 | ans 4 | **gold wrong** | https://en.wikipedia.org/wiki/LeBron_James
- What year was Minecraft first released? | gold 2011 | ans 2009 | **both acceptable** | https://en.wikipedia.org/wiki/Minecraft

Baseline-wrong decoys judged acceptable:

- Who has the most passes completed? | gold Drew Brees | ans Tom Brady | gold wrong | Stale gold: Brady passed Brees in Dec 2021 and holds the record.
- What was the name of the first atomic bomb? | gold Little Boy | ans The Gadget | both acceptable | Gadget was first detonated; Little Boy first used in war; both readings defensible.
- Who won the 1947 Oscar for Best Actress? | gold Loretta Young | ans Olivia de Havilland | both acceptable | 1947 ceremony = de Havilland; 1947 film year (20th awards) = Loretta Young.
- Who is the leader of Ecuador? | gold Lenín Moreno | Lenin Moreno | ans Daniel Noboa | gold wrong | Stale gold.
- Who won the Oscar for Best Actor in 2011? | gold Jean Dujardin | ans Colin Firth | both acceptable | 2011 ceremony = Firth; 2011 film year = Dujardin.
- What was the first baseball team created? | gold Cincinnati Red Stockings | ans The Knickerbocker Base Ball Club of New York, founded in 1845. | both acceptable | Knickerbockers first organized; Red Stockings first professional.
- Who won the 2008 NCAA BCS Football Championship? | gold Florida Gators | ans LSU | both acceptable | Jan 2008 game = LSU; 2008 season = Florida.
- What is the largest city in the world by population? | gold Tokyo | ans Jakarta | both acceptable | UN 2025 methodology ranks Jakarta; earlier UN ranking had Tokyo. Hard row.
- How many albums has Carrie Underwood released? | gold 7 | Seven studio albums | ans 10 | gold wrong | Stale gold (7); 9 studio + 1 compilation = 10 albums. Hard row.
- How old is Michael Caine? | gold 87 | ans 92 | gold wrong | Age 92 in Aug 2025; stale gold.
- What is the population of Raleigh, North Carolina? | gold 469298 | ans 506,306 | gold wrong | Answer is current Census estimate (Jul 2025); gold is an old figure.
- Who is the head coach for the Philadelphia Eagles? | gold Doug Pederson | ans Nick Sirianni | gold wrong | Stale gold.

System-correct decoys judged answer wrong:
