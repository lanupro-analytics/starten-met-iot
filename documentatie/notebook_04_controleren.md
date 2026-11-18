# Notebook 04 controleren

De volledige notebook staat in `docent/notebooks/04_metingen_publiceren_met_mqtt.ipynb`. De studentenversie is nog niet gegenereerd. De docentversie gebruikt dezelfde uitleg en uitvoercellen, met aparte antwoorden en uitwerkingen die de tag `oplossing` dragen. Notebook 00 en de bestaande notebooks 01–03 worden door deze toevoeging niet gewijzigd.

## Proefroute op de eigen server

1. Hervat dezelfde branch en Codespace als bij 01–03. De rol, werkdatabase, server.json en ca.crt moeten aanwezig zijn.
2. Start de broker handmatig via SSH. Gebruik het MQTT-wachtwoord van eigenaar in de verborgen notebookinvoer.
3. Voer het oefenbericht uit, pas de waarde aan en controleer de werkelijk ontvangen inhoud.
4. Zoek één geselecteerd bronrecord terug in DB Browser. Vergelijk identificatie, dier, hok en meetwaarde.
5. Bekijk de ontvangst van dat record via MQTT. Probeer het abonnement met `+`.
6. Publiceer de twintig records, herhaal de gewone publicatie en voer bewuste herpublicatie uit. Verwacht op een eerste uitvoering 20, 0 en 20 bevestigingen. Bij hervatten zijn de eerste twee tellingen 0 en 0.
7. Controleer `gegevens/inlevering/04_publicatiecontrole.json`. Bewaar antwoorden, commit en push. Bewaar werkbestanden afzonderlijk en stop de Codespace.

De voorbeeldoutput gebruikt de fictieve deelnemer `proef` en een lokale testbroker op 127.0.0.1. Gebruik in de les de eigen bestanden uit notebook 03, niet dat voorbeeldadres. De handmatige stappen moeten door een deelnemer worden gevolgd. De geautomatiseerde proef voert geen muisbediening in DB Browser of Codespaces uit.

## Uitgevoerde controles op 18 november 2026

De proef is uitgevoerd in een tijdelijke Debian 13-container met een echte Mosquitto-broker, TLS en de topicrechten uit notebook 03. De werkdatabanken en sleutels waren tijdelijke testkopieën. Geen DigitalOcean-server is gewijzigd.

- Alle 80.028 gewichtsrecords en 146.649 voederrecords zijn omgezet naar strikte JSON, met behoud van oorspronkelijke identificaties en velden.
- Voor beide rollen is een selectie van twintig records via MQTT gepubliceerd, door een afzonderlijke client ontvangen en inhoudelijk vergeleken.
- De volledige notebookcode is voor beide rollen uitgevoerd in een echte Jupyter-kernel. Beide uitvoeringen zijn herhaald met behoud van de verzendadministratie.
- Een selectie uitgebreid van twintig naar eenentwintig records verstuurde precies één bijkomend record.
- Gewone herhaling verstuurde nul records. Bewuste herpublicatie verstuurde twintig records. De werkdatabanken bleven byte voor byte gelijk.
- Verkeerde rol, gewijzigde inhoud, ongeldige JSON-getallen, te grote payloads en publicatietopics met wildcards werden geweigerd.
- Verkeerd wachtwoord, onbekende CA, verkeerd serveradres en onvoldoende publicatierechten werden gecontroleerd.
- Een gesimuleerde verzendfout leverde geen onterechte registratie als bevestigd op.
- Testwachtwoorden staan niet in bewaarde notebookuitvoer.

De volledige beginsets zijn bij deze test wel omgezet, maar niet geheel over MQTT verstuurd. Overdrachtduur en volledigheid van de volledige gepaarde keten worden bij notebook 05 getest. Een campusproef met Codespaces en een eigen DigitalOcean-server blijft nodig.

De HTML-weergave is visueel gecontroleerd op brede en smalle vensters (1400 en 800 pixels), zonder horizontale pagina-overloop.

## Technische proef herhalen

Gebruik een wegwerpcontainer met de image uit `controles/server_03.Dockerfile`. De controletest weigert uitvoering buiten Docker en werkt uitsluitend met tijdelijke bestanden en een broker op localhost. Kopieer de repository naar het Linux-bestandssysteem in de container om trage SQLite-lezingen via een Windows-bindmount te vermijden. Voer met de virtuele Python-omgeving uit:

```bash
/opt/iot/venv/bin/python controles/controleer_notebook_04.py
```

Met omgevingsvariabele `UITVOER_04` kan een map voor uitgevoerde testnotebooks worden aangewezen. Anders verdwijnen die uitvoerbestanden samen met de tijdelijke testmap. De test vervangt alleen de interactieve wachtwoordinvoer door een tijdelijk testgeheim. De daadwerkelijke MQTT-verbindingen en alle publicatiecellen worden uitgevoerd.

Het [MQTT-gegevenscontract](mqtt_gegevenscontract.md) legt de berichtstructuur, identiteit en herstelroute voor de aansluiting op notebook 05 vast.
