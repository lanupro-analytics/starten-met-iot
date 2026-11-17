# Gegevens en opslag

`origineel/asserva.db` bevat 80.028 gewichtsmetingen. `origineel/schauer.db` bevat 146.649 voederbezoeken. Beide bestanden bevatten de eerste vier weken: 24 augustus tot en met 20 september 2023. Ze zijn vrijgegeven voor opname in deze openbare onderwijsrepository. Bewaar deze startbestanden ongewijzigd.

In het [gegevenswoordenboek](gegevenswoordenboek.md) staan de velden, eenheden en beperkingen. Lichaamsgewicht is uitgedrukt in kg; voederopname per bezoek in gram. De meettijden zijn vermoedelijk Belgische lokale tijden en zijn niet naar UTC omgerekend. De bronselectie bevat geen aanvullende kwaliteitsfiltering. De resterende vijftien kalenderdagen zijn gereserveerd voor een latere oefening en zijn hier nog niet toegevoegd.

`oefeningen/oefenhokken.xlsx` en `.csv` bevatten dezelfde vier fictieve contextregels voor notebook 02. Ze zijn geen meetgegevens of beschrijving van de echte proefhuisvesting.

`werk/` bevat werkbestanden van de Codespace. Git slaat de inhoud over. Bewaar de lokale kopie van je databank; verwijdering van de Codespace verwijdert ook bestanden die niet elders zijn bewaard. Upload in notebook 02 naar `werk/invoer/`; na controle wordt de werkdatabank in `werk/` bewaard. Een afwijkend bestaand werkbestand wordt niet overschreven.

`inlevering/` bevat kleine, bewust geselecteerde resultaten. Notebook 01 maakt een werkplekcontrole; notebook 02 maakt een databankcontrole. Controleer de inhoud voordat je commit en push gebruikt.

De startdatabanken zijn reproduceerbaar met `hulpmiddelen/maak_startdatabanken.py`. Het bestand `origineel/maakcontrole.json` legt de broncontrolesommen, selectie en aantallen vast. De volledige onderzoeksbestanden zijn niet opgenomen.
