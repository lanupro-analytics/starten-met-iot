# Behandelingssleutel en verkenning voor de docent

De sleutel is door de docent aangeleverd. HP is HRE, LP is LRE. HRE18 en LRE18 bevatten elk drie hokken, HRE10 en LRE10 elk twee. Deze map hoort uitsluitend bij de docentbranch. De studentenbranchgenerator sluit de volledige map `docent/` uit. Publiceer de docentbranch niet voor studenten die de toewijzing nog moeten afleiden.

## Uitkomsten van drie verkenningen

1. De bestaande methode uit 07, met dagelijkse gewichtsmedianen en interpolatie op de grenzen van dag 1, 10, 18 en 27. De drie hoogste groeisnelheden tussen dag 10 en 18 horen bij hokken 1, 8 en 4. De drie laagste bij 3, 6 en 7. Alle zes zijn correct als HRE18 respectievelijk LRE18. De grens tussen de onderste drie en de overige hokken bedraagt slechts circa 0,020 kg groei per dag. Aan de bovenkant is dit circa 0,019 kg. Zie `poging1_interpolatie.csv`.
2. Als gevoeligheidscontrole is per dier een rechte lijn door alle dagmedianen in dezelfde fase geschat. Minstens 70% van de dagen moest een gewicht hebben, minimaal drie dagmedianen, en elke dag moest voederopname geregistreerd zijn. Alleen positieve groeisnelheden zijn meegenomen. Ook hier zijn dezelfde zes hokken de uitersten. Het verschil tussen het laagste HRE18-hok en het beste overige hok is nu slechts 0,006 kg per dag. Zie `poging2_helling.csv`. Dit is geen onafhankelijke validatie en geen robuust bewijs voor individuele behandelingstoewijzing.
3. Vierdaagse vensters vóór en na beide wisseldagen, met dezelfde trendlijnmethode als in poging 2. Rond dag 18 verbeteren groei en conversie bij hokken 6 en 7, maar niet bij hok 3. Rond dag 10 is geen consequent patroon dat de vier vroeg schakelende hokken betrouwbaar onderscheidt. Zie `poging3_wissel.csv`. Er zijn geen verdere vensters gezocht om de sleutel passend te maken.

## Keuze voor de les

De hoofdroute gebruikt poging 1. Die sluit rechtstreeks aan op 07 en heeft geen extra model nodig. De code leest geen behandeling. De fase is gekozen vanwege het bekende voederontwerp. De methode is wel achteraf op deze dataset beoordeeld met kennis van de sleutel en is dus geen blind gevalideerde classificator.

De docentuitwerking maakt vervolgens een voorlopige verdeling van de vier resterende hokken op conversie vóór dag 10: de laagste twee HRE10, de andere twee LRE10. Dit geeft acht van de tien correcte labels, maar verwisselt hokken 9 en 10. Hun zekerheid blijft expliciet laag. De uitwerking wordt niet met de sleutel gecorrigeerd: dat zou de mogelijkheden van de beschrijvende methode verkeerd voorstellen. `controle_hypothesen.csv` toont de vergelijking met de waarheid. Een student moet alle tien hokken toewijzen, de juiste groepsgroottes gebruiken en twijfel onderbouwen. Beoordeel ook de argumenten, niet uitsluitend het aantal juiste labels.

Opname en conversie nuanceren de groeirangorde. Hok 3 combineert trage groei met lage opname en heeft geen uitzonderlijk slechte conversie. Hokken 6 en 7 eten veel meer en hebben een hogere conversie. Een eenvoudige rangschikking op alleen conversie zou de zes juiste labels niet opleveren. Verschillen in aantallen bruikbare dieren, gezondheid en beginmassa kunnen meespelen. Er is geen causale of economische behandelingseffectschatting uitgevoerd.

## Uitvoering en reikwijdte

Op 25 november 2026 is het gewijzigde analysegedeelte van 08 vanaf de eerder via MQTT en HTTPS/API verkregen volledige analysedatabase opnieuw uitgevoerd, inclusief beginsituatiecontrole, grafieken, hypothesen, export en databasesnapshot. De transport- en Excel-importcode is niet veranderd. Die keten is in de eerdere oplevering voor beide rollen uitgevoerd. Deze hercontrole start bij de opgeslagen API-database en herhaalt geen cloudinstallatie of netwerkoverdracht.

De oorspronkelijke bestanden uit 07 zijn onveranderd. De eindgrafiek toont nu kg per dier per dag. Interne tabellen blijven hun expliciet benoemde gramkolommen gebruiken. De fasetabel bevat daarnaast kg-kolommen. Lysine is alleen een facultatieve suggestie met verwijzing naar slide 29 van de instructiepresentatie.

## Vrijgave naar studenten

De sleutel en dit evaluatieverslag staan uitsluitend onder `docent/`. Oplossingscellen en alle opgeslagen uitvoer worden bij studentgeneratie verwijderd. De branches `main` en `studentenversie` zijn niet aangepast.

Let op de al bestaande bronkolom `TREAT` in de oorspronkelijke databases. Het weglaten van deze docentmap alleen maakt historische bronbestanden niet blind. De analysecode selecteert `TREAT` niet, maar studenten kunnen bronbestanden zelf inspecteren. Een volledig geblindeerde vrijgave vereist afzonderlijk neutraliseren van die kolom in lesbestanden en bijwerken van bijbehorende controlesommen. Dat is in deze wijziging niet stilzwijgend gedaan.
