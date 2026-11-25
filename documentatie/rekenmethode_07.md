# Rekenmethode: vijf dichtstbijzijnde gewichten

## Bronnen en selectie

De analysedatabase uit 06 bevat gewichten in kg en voederopname per bezoek in gram. Beide bronnen worden gekoppeld op dier en hok. Alleen stabiel overeenkomende hokkoppelingen worden gebruikt. De populatie wordt vóór de numerieke kwaliteitsselectie vastgelegd, zodat we de oorspronkelijke aantallen blijven tonen.

Alleen `FILTER = '0'` telt mee. `flagged` en `errored` worden uitgesloten. Ook ongeldige tijdstippen, waarden en herkenningsfouten vallen buiten de analyse. Voor gewichten blijven oorspronkelijke toestelmetingen, handmatige wegingen en startwegingen behouden. Geïmputeerde gewichten en uitstroomregistraties worden uitgesloten. De bronrecords blijven ongewijzigd.

De oorspronkelijke vier weken bevatten 80.028 gewichtsrecords en 146.649 voederrecords. Alleen de FILTER-selectie behoudt respectievelijk 71.115 en 74.690 rijen. Na alle overige controles blijven 70.001 gewichtsrecords en 74.690 voederrecords over. De populatie telt 101 dieren in tien hokken.

## Eerst de periodegrenzen, dan de grensgewichten

Voor iedere grens wordt per dier de absolute tijdafstand van iedere behouden individuele gewichtsmeting tot het gewenste tijdstip berekend. De vijf dichtstbijzijnde meetrecords worden geselecteerd en hun rekenkundig gemiddelde vormt het geschatte grensgewicht. Bij gelijke afstand komt de eerdere meting eerst. Het gaat om vijf individuele meetrecords, niet om vijf dagmedianen.

Er is geen maximale afstand en geen eis dat het doelpunt tussen de metingen ligt. `afstand_begin_uren` en `afstand_eind_uren` bevatten de grootste absolute afstand binnen de vijf geselecteerde metingen. `aantal_begin_metingen` en `aantal_eind_metingen` tonen het aantal beschikbare geselecteerde metingen. Bij minder dan vijf blijft het grensgewicht onbekend. De afstand is kwaliteitsinformatie, geen uitsluitingscriterium.

Dezelfde oude metingen kunnen bij een dier zonder latere waarnemingen voor meerdere grenzen worden geselecteerd. Zo'n uitkomst bewijst geen actueel lichaamsgewicht of sterfte. Grote tijdafstanden en ontbrekende registraties moeten bij de interpretatie zichtbaar blijven.

## Groei, opname en conversie

Groei per dier is eindgewicht min begingewicht. Voederopname is de som van alle behouden bezoekwaarden waarvan de starttijd op of na de begingrens en vóór de eindgrens ligt, gedeeld door 1.000. Een bezoek over een grens wordt volledig aan zijn startinterval toegewezen en apart geteld.

Een behouden bezoek op iedere dag is niet verplicht. Het aantal blokken van 24 uur met minstens één behouden bezoek wordt gerapporteerd in `voederdagen`. Ontbrekende dagen sluiten een dier niet uit. De som is de geregistreerde opname en kan de werkelijke opname onderschatten. Een volledig lege voederperiode blijft onbekend. Een geregistreerd nulbezoek is wel een waarneming.

Conversie vereist twee berekenbare grensgewichten, minstens één voederrecord en positieve geschatte groei. De dierentabel behoudt ook uitgesloten dieren met hun reden. De hokberekening gebruikt voor groei en opname dezelfde bruikbare dieren. Conversie is som(voeder_kg) / som(groei_kg), niet het gemiddelde van dierconversies. Dagelijkse groei en opname zijn de totalen gedeeld door het aantal bruikbare dieren en de intervalduur. Interne gramkolommen zijn expliciet benoemd. De eindgrafieken van 08 tonen kg per dier per dag.

## Perioden en procestijd

De oorspronkelijke kalenderintervallen van 07 blijven 25 augustus, 1 september, 8 september, 15 september en 20 september, telkens 00:00. De oorspronkelijke bronperiode blijft begrensd tot 21 september exclusief, ook bij herberekening na latere toevoegingen. Met de vijfmetingenmethode zijn respectievelijk 98, 99, 99 en 99 dieren bruikbaar.

Procestijd is de verstreken tijd sinds het gezamenlijke eerste meetpunt op 24 augustus 2023 om 12:00, uitgedrukt in dagen inclusief uren en minuten. De fasevergelijking van 08 gebruikt dag 1, 10, 18 en 27. Alle tijdfiguren markeren dag 10 en 18. Een intervalpunt staat in het midden van de periode, met een horizontaal lijntje voor de duur. De spreidingsfiguren hebben geen tijdas.

Alleen de beschrijvende dagelijkse gewichtsgrafiek gebruikt één mediaan per dier per kalenderdag en vervolgens een gemiddelde per hok. Dit voorkomt dat dieren met veel bezoeken zwaarder doorwegen in die grafiek. Die dagmedianen worden niet gebruikt voor grensgewichten of groei.

## Beginsituatie en herhaling

De methodeversie is `vijf_dichtste_filter0_07_v3`. Archiveer een eerdere beginsituatie en voer 07 opnieuw uit voordat je met 08 verdergaat. De bewaarfunctie weigert een afwijkende bestaande beginsituatie te overschrijven.

De map `gegevens/inlevering/beginsituatie_07/` bewaart populatie, dagelijkse samenvattingen, dierintervallen en hokresultaten plus metadata, rekenregels en inhoudsvingerafdrukken. CSV-getallen gebruiken twaalf significante cijfers. De herberekening in 08 vergelijkt met een tolerantie van 1e-10. Dier- en hokcodes worden als tekst gelezen. Extra meetdagen wijzigen de vaste bronselectie van de oude intervallen niet.
