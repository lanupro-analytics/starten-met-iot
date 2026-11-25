# Behandelingen: informatie voor de docent

`behandelingssleutel.csv` bevat de door de docent aangeleverde werkelijke toewijzing. HRE18 en LRE18 hebben elk drie hokken, HRE10 en LRE10 elk twee. De volledige map `docent/` wordt bij het maken van de studentenbranch weggelaten.

## Interpretatie van de voorbeeldoplossing

Notebook 08 berekent de hypothesen uitsluitend uit meetgegevens met `FILTER = '0'`, zonder deze sleutel te lezen. De hoofdroute vergelijkt groei tussen dag 10 en 18. De drie hoogste waarden horen bij hokken 1, 4 en 8, de drie laagste bij 3, 6 en 7. Dit zijn de correcte HRE18- en LRE18-groepen. De overige vier hokken worden voorlopig verdeeld op conversie vóór dag 10. Met de huidige gegevens en filtering komen alle tien voorbeeldhypothesen overeen met de sleutel.

Deze overeenkomst is geen onafhankelijke validatie. Een aanvullende controle met trendlijnen door de dagmedianen verwisselde hok 1 en hok 9 aan de bovengrens. Kortere vensters rond de schakeldagen leverden geen eenduidige herkenning van alle voerwissels. De voorlopige labels en onzekerheden in de notebook moeten daarom samen worden beoordeeld. De vroege groepen behouden een lage zekerheid.

De actuele berekeningen, figuren en export van de hypothesen worden door notebook 08 gemaakt. De eerdere losse verkenningsscripts en exports zijn daarvoor niet nodig. Hun historische versies blijven beschikbaar in Git.

## Uitvoering en vrijgave

De [rekenmethode](../../documentatie/rekenmethode_07.md) beschrijft de filtering en berekening. De controlehandleidingen voor [07](../../documentatie/notebook_07_controleren.md) en [08](../../documentatie/notebook_08_controleren.md) beschrijven uitvoering, controles en herhaling. Oude beginsituaties zonder de verplichte filtering mogen niet met de huidige methode worden gecombineerd.

De oorspronkelijke bronkolom `TREAT` bevat nog codes A–D. De analyse selecteert deze niet. Voor een volledig blinde studentenpublicatie moeten die bestaande codes apart worden geneutraliseerd, inclusief actualisering van broncontrolesommen. Alleen het weglaten van de docentmap maakt de bronbestanden niet blind.
