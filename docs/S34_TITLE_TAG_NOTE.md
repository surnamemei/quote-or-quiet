# S34 note: tag the answer with a disambiguated evidence title (exploratory, 2026-11-09)

Idea: if the page that verified the answer has a Wikipedia disambiguator in its title ("Heat (1995 film)", "Dobra (Kupa)", "Jordan, Guimaras"), the name is shared; state the page with the answer ("For Dobra (Kupa): Croatia") instead of detecting ambiguity. No answer is withheld.
Rule tried: tag if the verified page title has a parenthetical or comma qualifier, the title core is named in the question, and the question does not already contain the qualifier words.

Exploratory measurement (no pass rule was set first, and the test sets were looked at in the same pass, so this is not a test result):
- design releases: 22 of 430 tagged (5.1%); 2 of the 15 gold-wrong tagged (Dobra River: tag makes the answer true for that river; 4F: tag does not help);
- FRESH-5, Mintaka test, PopQA test releases: 95 of 1,589 tagged (6.0%); 4 of the 49 gold-wrong tagged (Shaft (franchise) with Gordon Parks: roughly right for the franchise; Minecraft (franchise) 2009; Thor (Marvel Cinematic Universe) 9 films; Barabbas (novel) with a film director: the tag is wrong).
Reading: a tag rescues only a few errors (about 2 to 3 of 49) because the verified page is usually the answer's page or the primary-topic page, which has no disambiguator. Not pursued.
