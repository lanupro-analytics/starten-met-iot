# Rekenmethode voor notebook 07

## Doel en bron

Deze methode combineert individuele gewichten met individuele voederopnames tot een verkennend overzicht per hok. Zij is een expliciete lesmethode, geen herimplementatie van de statistische analyse uit de bronpublicatie en geen gevalideerde regeling van een voederinstallatie. Zij gebruikt uitsluitend de via 06 opgeslagen basisdata.

De aangeleverde publicatie is Zhu et al. (2026), *Impact of a protein feeding strategy on performance and lysine utilization efficiency in weaned piglets*, Animal Nutrition 27, 62–73. De abstract en methodes beschrijven 101 biggen, vier strategieën met 188 of 162 g ruw eiwit/kg gedurende 10 of 18 dagen, gevolgd door 179 g/kg. Sectie 2.6 beschrijft de oorspronkelijke kwaliteitsverwerking. De lesmethode herhaalt die filters en modellen niet. Er wordt geen behandeling aan een hok gekoppeld of uit het veld TREAT getoond.

De algemene definitie van voederconversie is kg opgenomen voeder per kg gewichtstoename. Zie ook [Ontario: Providing feed and water to pigs](https://www.ontario.ca/page/providing-feed-and-water-pigs). In deze oefening gaat het om geregistreerde opname en geschatte groei, niet om een volledige bedrijfsboekhouding inclusief voerverlies, gezondheid of kostprijs.

## Broncontrole en afzonderlijke selectie

De analyse leest `analyse_06.db` met SQLite `mode=ro`. De application_id moet 600106 zijn. SHA-256 wordt opnieuw over de opgeslagen JSON berekend en vergeleken met de recordcontrolewaarden. Daarna wordt het inhoudsmanifest vergeleken met de laatste API-import en de notebookcontrole uit 06.

De geladen velden omvatten dier, hok, datum, meetwaarde, eenheid, bezoekstart/-einde, ERROR, FILTER en DATAORIGIN. Behandelingscodes worden niet geladen. De ruwe bronrecords worden niet gewijzigd. Dubbele `(bron,record_id)` en verkeerde bron/meettype/eenheid worden als fout gemeld.

Selectiestappen:

1. Bronkalenderdatum vanaf 24 augustus tot 21 september 2023 exclusief.
2. ERROR gelijk aan `no error`, FILTER niet `errored`, dier en hok aanwezig.
3. Dier komt in beide bronnen voor en heeft in beide dezelfde unieke hokcode.
4. Geldige begin- en eindtijd, eindtijd niet vóór begintijd, datum gelijk aan de kalenderdatum van bezoekstart, eindige meetwaarde. Gewicht strikt positief, voer nul of positief.
5. Voor gewicht alleen DATAORIGIN `0`, `allocation` of `manualweighing`. `imputed` en `exit` worden uitgesloten.

Uitsluitend `FILTER = '0'` (tekst) is toegestaan. `flagged` en `errored` zijn eerder gemarkeerde uitschieters of fouten. Hun meetwaarden dragen niet bij aan analyses of figuren. De populatie wordt vóór deze numerieke kwaliteitsselectie vastgelegd, zodat uitgesloten metingen de noemer niet onzichtbaar verkleinen. Ontbrekende voederdagen worden niet als nulopname ingevuld.

## Tijd en gewichten

Voor ieder dier en iedere kalenderdag wordt de mediaan van de geselecteerde gewichten berekend. De mediane waarnemingstijd geeft dit daggewicht een representatieve tijdpositie. Dit paar is een samenvatting, niet noodzakelijk één werkelijk gemeten record.

Voor een grens t worden de dichtstbijzijnde dagmedianen vóór en na t gebruikt. Het grensgewicht is:

`gewicht(t) = gewicht_links + fractie × (gewicht_rechts − gewicht_links)`

`fractie = (t − tijd_links) / (tijd_rechts − tijd_links)`

Er is geen extrapolatie. De ondersteunende dagmedianen mogen maximaal 48 uur uit elkaar liggen. Een exact aanwezige dagmediaan mag direct worden gebruikt. De grens van 48 uur is een onderwijskeuze, geen bewezen optimale grens. De dagelijkse samenvatting kan abrupte veranderingen afvlakken.

De standaardgrenzen zijn 25 augustus, 1 september, 8 september, 15 september en 20 september, steeds 00:00. Zo is de gedeeltelijke eerste kalenderdag geen volledige voederdag in de hoofdvergelijking en kunnen metingen van 20 september het laatste grensgewicht ondersteunen. Er wordt geen gewicht van na de basisperiode gebruikt. De intervallen duren 7, 7, 7 en 5 dagen.

## Voeder, dekking en koppeling

Voer wordt op bezoekstart toegewezen, vanaf inclusief en tot exclusief. VFI wordt opgeteld en door 1000 gedeeld. Er wordt geen cumulatieve teller afgetrokken. Een bezoek dat een grens passeert wordt volledig aan zijn startinterval toegekend. Zulke grensbezoeken worden geteld. Binnen de geïnspecteerde basisselectie zijn er geen bezoeken over middernacht.

Ieder dier moet in iedere kalenderdag van het interval minstens één geldig voederrecord hebben. Een geregistreerd nulbezoek geldt als waarneming. Een ontbrekende dag wordt niet als nul ingevuld. Dit is een minimale dekkingscontrole en bewijst geen volledige registratie binnen elke dag.

De populatie wordt vóór de numerieke kwaliteitsselectie vastgelegd op basis van stabiele, foutvrij herkende koppelingen. Zij bevat 101 dieren in 10 hokken, met 11 dieren in hok 1 en 10 in de andere hokken. Per interval vallen dieren uit wanneer begin-/eindgewicht ontbreekt, een voederdag ontbreekt of de geschatte groei niet positief is. Alle redenen blijven in `dierintervallen.csv` zichtbaar.

De hokberekening gebruikt voor beide tellers exact dezelfde bruikbare dieren. Voederconversie is som(voeder_kg) / som(groei_kg), niet het gemiddelde van individuele verhoudingen. Groei en opname in g per dier per dag zijn de respectieve totalen × 1000 / (aantal bruikbare dieren × dagen). Bij nul bruikbare dieren blijven de uitkomsten ontbrekend.

Het uitsluiten van niet-positieve groei kan de groepsverhouding gunstiger doen lijken. Daarom staan aantallen en dekkingspercentages bij de uitkomsten. De groepsresultaten zijn geen schatting voor de ontbrekende dieren. Ook kan de groep tussen intervallen veranderen.

## Controlewaarden uit de basisdata

- Oorspronkelijk: 80.028 gewichtsrecords en 146.649 voederrecords.
- Expliciete herkenningsfouten: 7 gewicht, 80 voer.
- FILTER = '0': 71.115 gewichtsrecords en 74.690 voederrecords. Na de overige controles blijven 70.001 gewichtsrecords en 74.690 voederrecords over.
- Bruikbare dieren per interval: 72, 98, 98, 98.
- Dier 89728010, hok 3, eerste interval: groei 1.268328 kg, opname 1.459 kg, conversie 1.150333.
- Hok 1, eerste interval: conversie 0.968261.
- Hok 9, laatste interval: conversie 1.263938.


Afgeronde tekstwaarden dienen voor uitleg. De opgeslagen tabellen bevatten meer precisie en vormen het vergelijkingspunt voor 08. De kwartielverkenning en het spreidingsdiagram zijn facultatief en wijzigen deze basis niet.

## Beginsituatie en latere vergelijking

`gegevens/inlevering/beginsituatie_07/` bevat populatie.csv, daggewichten.csv, dierintervallen.csv, hokresultaten.csv en beginsituatie.json. De JSON bewaart methodeversie, regels, bronmanifest en SHA-256 van de CSV-inhoud in UTF-8 met LF-regeleinden. De map wordt eerst volledig in een tijdelijke buurmap geschreven en daarna geplaatst. Herhalen met dezelfde inhoud behoudt de map. Verschillende inhoud veroorzaakt een melding zonder overschrijven.

De drie hoofdfiguren en `07_analysecontrole.json` worden daarnaast automatisch gemaakt. Bronwaarden en database blijven ongewijzigd. Een toekomstige analyse van aanvullende data krijgt een aparte resultaatset. Voor vergelijking over dezelfde vaste basisperiode moeten de populatie, bronselectie, grenzen en kwaliteitsregels gelijk blijven. De methode gebruikt geen later meetpunt buiten de vastgelegde basisselectie.

Bij het later inlezen van de CSV-bestanden blijven `dier_id` en `hok` expliciet tekst (`dtype=str` voor deze kolommen). Tijden worden met microseconden geëxporteerd, zodat ook een mediane waarnemingstijd tussen twee seconden behouden blijft. Numerieke tabellen gebruiken twaalf significante cijfers. Vergelijk herberekende floats met een verklaarde tolerantie, niet als exacte binaire waarden.

De filterversie heet `dagmediaan_lineair_filter0_07_v2`. Archiveer een oudere beginsituatie en voer 07 opnieuw uit voordat je met 08 verdergaat. De oude beginsituatie wordt niet overschreven.

## Procestijd op de figuren

Procestijd is `(tijdstip - eerste meetpunt) / 24 uur`. Het gezamenlijke eerste meetpunt van beide oorspronkelijke bronnen ligt op 24 augustus 2023 om 12:00. Uren, minuten en seconden blijven als een fractie van een dag behouden. De notebooks bepalen het nulpunt uit de brongegevens vóór filtering. Latere aanvullingen verplaatsen dit nulpunt niet.

Alle tijdfiguren hebben een as in dagen en verticale stippellijnen op dag 10 en 18. Een dagelijkse hokwaarde staat op de mediane tijd van de gebruikte dierdaggewichten. Ontbrekende dagen blijven gaten in de lijn. Intervalwaarden staan op het midden van het interval, met een horizontaal lijntje dat de duur aangeeft. De oorspronkelijke kalendergrenzen van de basisanalyse blijven behouden. De spreidingsgrafiek van groei tegenover conversie heeft geen tijdas.

De fasevergelijking in 08 gebruikt grenzen op procestijd 1, 10, 18 en 27, telkens om 12:00. De voederdekking wordt dan gecontroleerd in blokken van 24 uur vanaf de intervalstart. Voor middernachtgrenzen is dit gelijk aan de bestaande kalenderdagcontrole. Dag 10 en 18 zijn de afgesproken wisselmomenten in procestijd, geen uit meetgegevens bewezen feitelijke wisseluren.
