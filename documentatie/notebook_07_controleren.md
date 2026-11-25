# Notebook 07 controleren

## Inhoud

De docentversie bevat 79 cellen met uitgevoerde voorbeeldoutput, vijf tekstvragen, een verplichte eigen hok-/intervalselectie en twee facultatieve verkenningen. De facultatieve opdrachten gaan over kwartielen van diergewichten binnen een hok en een spreidingsdiagram van groei tegenover voederconversie. Ze wijzigen de basisberekening niet.

De hoofdroute leest de analysedatabase uit 06, controleert de inhoud, selecteert en koppelt dieren, bouwt daggewichten, werkt één interval uit en maakt overzichten voor alle tien hokken. Drie hoofdfiguren tonen gewichtsverloop, gemiddelde groei en voederopname, en voederconversie. De notebook bewaart automatisch een vaste beginsituatie en `07_analysecontrole.json`.

De [rekenmethode](rekenmethode_07.md) legt de gekozen regels, tijdsgrenzen en beperkingen vast. De hypothesevorming over voederstrategieën is verkennend. Er worden geen behandelingscodes of hoktoewijzingen getoond. Notebook 08 bouwt hierop voort met aanvullende meetdagen en hypothesen over de voederstrategieën. De studentenversies van 07 en 08 zijn nog niet vrijgegeven.

## Uitgevoerde controles op 25 november 2026

- Kleine onafhankelijke rekenvoorbeelden toetsen gram-naar-kilogram, gemiddelde dagelijkse waarden, exclusieve eindgrens, ontbrekende voederdagen, nulbezoek, niet-positieve groei, ontbreken van extrapolatie en een te grote gewichtsafstand.
- De hokconversie wordt gecontroleerd als verhouding van totalen. Een voorbeeld met ongelijke diergroei onderscheidt dit van het gemiddelde van dierverhoudingen.
- Selectietests toetsen verkeerde eenheden, dubbele identifiers en niet-overeenkomende hoktoewijzingen.
- De bewaarfunctie wordt tweemaal aangeroepen met dezelfde inhoud. Een gewijzigde uitkomst wordt geweigerd zonder de oorspronkelijke beginsituatie te overschrijven.
- Een figuurtest bewaakt dat de gemeenschappelijke assen ook de hoogste waarde in een later hok tonen.
- Het volledige notebook wordt voor zowel de gewichtsrol als de voederopnamerol uitgevoerd met alle 226.677 basisrecords in een tijdelijke SQLite-database in het formaat van notebook 06.
- De kernelproef reconstrueert die testdatabase met de bestaande bron-naar-JSON-omzetter en dezelfde hokmetadata. Dit is geen nieuwe API- of MQTT-netwerkproef. De netwerkroute is bij 06 afzonderlijk getest.
- Beide uitvoeringen leveren 101 gekoppelde dieren op en respectievelijk 72, 98, 98 en 98 bruikbare dierintervallen. De eigen hokopdracht en het automatische controlebestand worden gecontroleerd.
- De SHA-256 van het analysebestand wordt vóór en na de volledige uitvoering vergeleken. De database blijft ongewijzigd.
- Het opnieuw uitvoeren met de andere rol gebruikt dezelfde bewaarde beginsituatie en controleert daarmee ook behoud bij herhaling.
- Een later toegevoegd testrecord buiten de basisperiode verandert de uitkomsten van de vaste basisperiode niet.
- Python-syntaxis, metadata, het drie-cellenpatroon, relatieve links en tijdelijke generatie van de studentversie worden gecontroleerd. Notebook 00 blijft gelijk aan zijn bewaarde checksum. Er wordt geen studentnotebook in de repository geschreven.
- De hoofdfiguren en de gerenderde notebookopmaak worden visueel gecontroleerd, inclusief labels, eenheden, gemeenschappelijke assen en dekkingslabels.

De voorbeeldoutput gebruikt de fictieve deelnemer `proefdocent`. Er worden geen wachtwoorden gevraagd of serververbindingen gemaakt in 07. Je eigen volledige uitvoering van 05 en 06 blijft de voorwaarde om 07 met jouw ontvangen gegevens te doorlopen.

## Herhalen

Gebruik de bestaande Python-omgeving van de practicumrepository met pandas, NumPy, Matplotlib, paho-mqtt, requests, nbformat en nbclient. NumPy is een afhankelijkheid van pandas. De kernelproef heeft een beschikbare Python 3-kernel en Git nodig. Zij werkt in een tijdelijke directory, kopieert de bronbestanden en verandert geen bestaande database.

```bash
python controles/test_analyse_07.py
python controles/controleer_notebook_07.py
python controles/kernelproef_07.py
```

`UITVOER_07` kan een aparte uitvoermap aanwijzen. Zonder instelling bewaart de kernelproef twee uitgevoerde notebooks en voorbeeldinlevering onder `uitvoer07/`. Deze technische proefuitvoer hoort niet in de studentrelease.

## Handmatige beoordeling

Controleer vooral of de uitleg over dagmedianen, interpolatie en dezelfde dierselectie voor teller en noemer voldoende duidelijk is voor de groep. Controleer dat uitsluitend FILTER = '0' wordt behouden en de nadruk op uitsluitingen in het eerste interval. De methode maakt beperkingen zichtbaar, maar vervangt geen biologische validatie van alle bronvlaggen.

Voor de latere studentenversie kan gericht `python hulpmiddelen/maak_studentenversies.py --nummer 7` worden gebruikt. Dit verandert geen branches. De publicatiestap blijft afzonderlijk. In deze ontwikkelronde blijven `main`, `studentenversie` en notebooks 00–06 ongewijzigd.
