# Docentcontrole met FILTER = '0'

De sleutel is uitsluitend voor de docent. Deze hele map wordt uitgesloten bij het maken van de studentenbranch. HRE18 en LRE18 hebben elk drie hokken, HRE10 en LRE10 elk twee.

Alle drie de beschrijvende verkenningen zijn opnieuw berekend met uitsluitend FILTER = '0'. De hoofdroute gebruikt de methode uit notebook 07, met grenzen op dag 1, 10, 18 en 27. De drie hoogste groeisnelheden tussen dag 10 en 18 horen bij hokken 1, 4 en 8. De drie laagste bij 3, 6 en 7. Dat zijn alle zes correcte HRE18- en LRE18-labels.

De overige vier hokken worden voorlopig verdeeld op conversie vóór dag 10. Met deze filtering levert dezelfde regel ook daarvoor de juiste labels op: alle tien voorbeeldhypothesen komen overeen met de sleutel. Zie controle_hypothesen.csv. De regel is niet aangepast om de labels te laten kloppen. De filtering volgt de kwaliteitscodes van de bronverwerking.

Dit succes is geen onafhankelijke validatie. Bij de alternatieve trendlijn door dagmedianen (poging 2) wisselen hok 1 en hok 9 aan de bovengrens van plaats. De zes uitersten zijn dus niet volledig robuust voor de methode. De vierdaagse vensters (poging 3) geven geen eenduidig patroon dat alle voerwissels identificeert. De zekerheid bij de vroege groepen blijft laag. Er zijn geen nieuwe vensters gezocht om de sleutel passend te maken.

Notebook 07 is na filtering volledig uitgevoerd voor beide rollen. Notebook 08 is vanaf de eerder via de API verkregen volledige database opnieuw geanalyseerd. De nieuwe beginsituatie, grafieken, tabellen, advies en snapshot zijn gecontroleerd. Bronbestanden en transport blijven ongewijzigd. De methodenaam is dagmediaan_lineair_filter0_07_v2. Oude beginsituaties worden geweigerd en moeten eerst afzonderlijk gearchiveerd worden.

De oorspronkelijke bronkolom TREAT bevat nog codes A–D. De analyse selecteert deze niet. Voor een volledig blinde studentenpublicatie moeten die bestaande codes apart worden geneutraliseerd, inclusief actualisering van broncontrolesommen. Dit is geen onderdeel van de filterwijziging.
