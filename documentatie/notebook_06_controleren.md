# Notebook 06 controleren

## Inhoud en ontwikkelbranch

De volledige docentversie staat in `docent/notebooks/06_gegevens_opvragen_via_een_api.ipynb` op `jrndgrt`. De opmaak en didactiek volgen de herziene notebooks 01–04 en secties 7, 8, 10 en 11 van de practicum specificatie. Notebook 05 is uitsluitend als technische aansluiting gelezen en niet herwerkt. Notebooks 00–05 blijven ongewijzigd. `main` en `studentenversie` worden bij deze ontwikkeling niet bijgewerkt.

De notebook bevat tien opeenvolgende secties: werkplek, API-begrippen, installatie, beveiligde aanvraag, documentatie en recordinspectie, zelf filteren, foutproef, volledige import, herhaling en inlevering. Er zijn vijf tekstvragen en één codeopdracht. Vragen hebben aparte invul- en oplossingscellen. Zeven cellen dragen `oplossing`, inclusief de tijdelijke proefbranchinstelling. Bash-blokken staan afzonderlijk. Een SVG-schema toont de toestel-, server- en kantoorfuncties.

## Aansluiting op 03 en 05

De uitbreiding hergebruikt de bestaande `iot-status`-dienst, Nginx, poort 443, certificaten en API-aanmelding. `server/configuratie/api-uitbreiding.conf` vervangt alleen de Uvicorn-startopdracht via een systemd-aanvulling. De oorspronkelijke statusdienst blijft de herstelroute. Het schema van `verzamelde_metingen.db`, de MQTT-ontvanger en de handmatige start van Mosquitto veranderen niet.

De notebook vereist `01_werkplekcontrole.json`, `server.json`, `ca.crt` en een geslaagde `05_ontvangstcontrole.json`. Aantallen en inhoudsvingerafdrukken uit 05 worden met de API en de analysedatabase vergeleken. Deze controle is bedoeld voor de ongewijzigde beginsituatie. Na de latere gegevensaanvulling in notebook 08 moet de nieuwe bron-/ontvangstcontrole worden gebruikt, niet stilzwijgend de oude controle van 05.

Er is geen nieuwe Python-afhankelijkheid in de lesomgeving nodig. FastAPI en Uvicorn staan in de serveromgeving van 03. Requests en pandas staan in de Codespaces-omgeving. De API-module gebruikt dezelfde geteste pakketversies als de bestaande server.

## Uitgevoerde lokale controles op 25 november 2026

- Contracttests met een echte lokale Uvicorn HTTP-server: authenticatie, GET-only, beveiligde OpenAPI-documentatie, filters, exclusieve einddatum, lege selectie, ongeldige/onjuiste parameters en SQL-injectietekst als gewone parameterwaarde.
- Paginering behoudt exacte lange tekstidentificaties. Een nieuwe meting tijdens de overdracht valt buiten de eerder gekozen grens en komt in een volgende selectie mee.
- Importcontrole: volledig ophalen, herhaald ophalen zonder extra records, weigering van een bronbestand als analysedatabase en terugdraaien bij een foutieve inhoudsvingerafdruk, ook voor een nieuw analysebestand.
- De volledige basisset van 80.028 gewichtsrecords en 146.649 voederrecords wordt met de bestaande omzetter en ontvanger-validator in een tijdelijke verzameldatabase opgebouwd. Dit is een aansluitingstest op de opslag uit 05, geen nieuwe MQTT-netwerkproef.
- De volledige notebook wordt voor beide rollen uitgevoerd met een echte Python-kernel, Uvicorn als gebruiker `iot`, Nginx en HTTPS met een lokaal gegenereerde CA en IP-certificaat. Alle 226.677 records worden per rol tweemaal opgehaald. De tweede import voegt nul records toe. De inhoudsmanifesten en automatische inlevering worden gecontroleerd.
- De gecombineerde lokale proefomgeving is begrensd op één CPU en 512 MiB RAM. Deze grens geldt voor de hele testcontainer, inclusief de testclient.
- De database is ook getest na het sluiten van de schrijver, met een voor `iot` niet-schrijfbare database-directory. De uitsluitend-lezende API kon de gegevens lezen.
- De systemd-unit met aanvulling is met `systemd-analyze verify` gecontroleerd. Dit is syntaxis- en configuratiecontrole, geen echte systemd-bootproef.
- Alle codecellen zijn syntactisch gecontroleerd, de zes Bash-blokken door `bash -n`, relatieve links op bestaan en notebookmetadata met `nbformat`.
- Een tijdelijke studentversie is gegenereerd en gecontroleerd: 82 cellen, geen oplossingscellen, geen uitvoer en geen docentoverride. Geen studentnotebook in de repository is hierbij gewijzigd.
- Notebook 00 is tegen zijn bewaarde SHA-256 gecontroleerd. De notebook is als HTML gerenderd en de tekst, tabel, schema en kaders zijn visueel gecontroleerd.

De bewaarde uitvoer van het docentnotebook gebruikt de fictieve deelnemer `proefdocent`, de rol gewichten en localhost. De echte wachtwoordinvoer is in de kernelproef automatisch ingevuld met een tijdelijk gegenereerd testwachtwoord. Het wachtwoord is uit de opgeslagen broncode verwijderd vóór de uitgevoerde notebook wordt bewaard. Interactieve SSH en handmatige installatie worden door de testopstelling vervangen.

## Nog controleren op je echte oefenserver

1. Doorloop de installatiecellen met je bestaande `beheer`-account en controleer het kopiëren vanuit Codespaces.
2. Controleer het `getpass`-invoerbalkje, het bestaande API-wachtwoord en de eigen CA in de echte Codespaces-interface.
3. Test de werkelijke systemd-dienst, herstart van de Droplet, behouden database en herstelroute. Mosquitto blijft na een Droplet-herstart handmatig te starten.
4. Voer de volledige import uit met je eigen ontvangen gegevens en controlebestand uit notebook 05. Controleer de belasting naast de MQTT-ontvanger en de campusbediening.
5. Controleer de leesbaarheid van schema en kaders in jouw editor en vul de oefenopdracht in zoals een student.

Er is voor deze ontwikkeling geen echte Droplet gewijzigd en geen cloudresource aangemaakt. Een geslaagde lokale uitvoering vervangt deze echte-serverproef niet.

## Tests herhalen

Gebruik een nieuwe wegwerpcontainer op basis van `controles/server_03.Dockerfile` en kopieer de repository naar een lokaal Linux-bestandssysteem in de container. De testomgeving heeft aanvullend pandas nodig om de notebook uit te voeren. De uitgebreide ketenproef richt gebruikers, Nginx en lokale testcertificaten in en hoort niet op een bestaande server.

```bash
/opt/iot/venv/bin/python controles/test_api_06.py
/opt/iot/venv/bin/python controles/controleer_notebook_06.py
/opt/iot/venv/bin/python controles/keten_06.py
```

De ketenproef schrijft de twee uitgevoerde notebooks en `ketenresultaat.json` naar `uitvoer06/` binnen de wegwerpcontainer. De benodigde handmatige stappen zijn hierboven afgebakend. Beëindig de testcontainer na de controle.

## Latere studentpublicatie

De generator ondersteunt nu een gerichte selectie. Na inhoudelijke goedkeuring kan uitsluitend notebook 06 worden gegenereerd zonder de studentkopieën van 01–05 opnieuw te schrijven:

```bash
python hulpmiddelen/maak_studentenversies.py --nummer 6
```

Dit genereert alleen bestanden op de huidige branch. Het publiceert niets. `maak_studentenbranch.py` blijft een afzonderlijke, bewuste stap voor de latere release. In deze ontwikkelronde wordt geen studentrelease gemaakt.
