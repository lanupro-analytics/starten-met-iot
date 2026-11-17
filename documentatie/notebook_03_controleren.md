# Notebook 03 controleren

## Huidige uitvoering

Open `docent/notebooks/03_eigen_server_inrichten.ipynb`. De volledige versie staat op `codex/practicum-03-server`, voortbouwend op de bestanden van notebook 02. De tekst in het notebook gebruikt al de toekomstige studentenlocatie `notebooks/`; de studentenversie is nog niet gegenereerd.

Iedere deelnemer maakt één eigen Droplet binnen team **lanupro-tech**, project **starten-met-iot**. GitHub is een mogelijke aanmeldmethode voor DigitalOcean, maar vervangt de teamuitnodiging niet. De server van de docent is uitsluitend een eventuele oefenomgeving voor verificatie en wordt niet in het notebook als studentserver ingesteld.

De notebook heeft 63 cellen, zes vragen met afzonderlijke invul- en oplossingscellen en 24 terminalblokken. De tijdelijke branch-omzeiling volgt het patroon van notebooks 01 en 02 en heeft de tag `oplossing`. Voor een proef op een eigen deelnemersbranch doorloop je eerst notebook 01 op die branch. Gebruik je de tijdelijke omzeiling op een ontwikkelbranch, dan moeten de opgeslagen instellingen overeenkomen met `student/proefdocent`.

## Technische keuzes

- Debian 13 met Mosquitto 2.0 uit de Debian-pakketbron.
- Wachtwoordaanmelding via SSH; afzonderlijke gebruiker `beheer` met sudo. Directe root-aanmelding via SSH wordt pas uitgeschakeld nadat de tweede gebruikersaanmelding is getest.
- Geen domeinnaam nodig: per server een eigen CA en een certificaat met het publieke IPv4-adres. De CA wordt via een gecontroleerde SSH-verbinding naar de clients overgebracht. Certificaat- en adrescontrole blijven ingeschakeld.
- Mosquitto op 8883 met afzonderlijke eigenaar- en lezersaccounts en topicrechten.
- Nginx op 443; een kleine FastAPI-statusdienst op uitsluitend `127.0.0.1:8000`, onder servicegebruiker `iot`.
- De statusdienst controleert een afzonderlijk API-wachtwoord met een gezouten scrypt-controlewaarde. Het controlepad is `/gezondheid`; het is nog geen meetgegevens-API.
- UFW laat TCP 22, 8883 en 443 toe. Een eventuele Cloud Firewall moet daarmee overeenkomen. De leshandleiding wijzigt geen gedeelde teamfirewall.
- Python-pakketten staan met geteste versies in `server/requirements.txt`. De systeem-Python wordt niet met pip aangepast.

De eerste inrichting gebeurt in verklaarde stappen. Er is geen automatisch cloud-aanmaakscript. Ontvangst en opslag van echte metingen en de lees-API worden in de volgende notebooks toegevoegd. De statusdienst bevestigt alleen de bereikbaarheid en beveiligde aanmelding; hij kan later door de gegevensdienst worden vervangen nadat die is getest.

## Uitgevoerde lokale controles — 17 november 2026

De installatieonderdelen zijn getest met Debian 13 in een tijdelijke Dockercontainer, begrensd op één CPU en 1 GiB geheugen. Mosquitto, Nginx en Uvicorn draaiden als echte processen. De webdienst draaide onder de niet-bevoorrechte gebruiker `iot`; Mosquitto gebruikte zijn eigen serviceaccount. Het is geen DigitalOcean-Droplet en geen bewijs dat de volledige latere meetgegevensketen binnen deze servergrootte past.

Gecontroleerd:

- certificaataanmaak, IPv4-validatie en weigeren van onbedoelde vervanging;
- MQTT-aanmelding, bevestiging van het abonnement en een werkelijk ontvangen controlebericht via TLS;
- HTTPS met wachtwoord en CA-controle;
- afwijzen van een onjuist MQTT- of API-wachtwoord, onbekende CA, verkeerd certificaatadres en publicaties buiten de toegekende rechten;
- ontvangst via een afzonderlijk lezersaccount, naast de geweigerde publicatie met datzelfde account;
- behoud van bereikbaarheid na een herstart van het Mosquitto-proces;
- Nginx-configuratie en systemd-unit op geldigheid;
- volledige uitvoering van de notebookcodecellen met een echte Jupyter-kernel en tijdelijke testinvoer;
- geldige notebookstructuur, oplossingscellen, lokale afbeeldingverwijzingen en syntaxis van alle terminalblokken;
- visuele controle van de HTML-weergave: beide afbeeldingen laden, de kleurenkaders zijn leesbaar en de pagina loopt niet buiten de vensterbreedte.

De opgeslagen voorbeelduitvoer gebruikt `student/proef` en `127.0.0.1` in een afgesloten lokale test. De testwachtwoorden en de tijdelijke invoercel worden niet opgeslagen in het notebook. Studenten voeren de cellen opnieuw uit met hun eigen servergegevens. De test maakt geen cloudresources aan en wijzigt geen teamrechten.

## Nog uit te voeren op DigitalOcean en Codespaces

De echte Droplet is nog niet geïnspecteerd of gewijzigd. Browsertoegang voor die inspectie kon niet worden uitgevoerd doordat de automatische goedkeuringscontrole een gebruikslimiet meldde. Dit is een beperking van de verificatie, geen geslaagde serverproef.

Doorloop vóór vrijgave aan studenten:

1. Controleer teamrechten, project, actuele Debian-image, planbeschikbaarheid en kosten. Een project is geen garantie dat een teamlid uitsluitend de eigen Droplet kan wijzigen.
2. Gebruik een daarvoor bestemde lege oefenserver. Inspecteer een bestaande server eerst; installeer niet over onbekende diensten heen.
3. Voer de installatieblokken in de opgegeven volgorde uit. Controleer de eerste hostvingerafdruk, verborgen wachtwoordinvoer en tweede SSH-aanmelding vóór het wijzigen van root-toegang.
4. Test de verbinding vanuit een echte Codespace op het campusnetwerk. Controleer ook de verborgen invoervelden in de Codespaces-notebookinterface.
5. Controleer UFW, eventuele Cloud Firewall en de werkelijke externe poorten. Alleen syntaxiscontrole bewijst niet dat firewallregels juist werken.
6. Test een echte `systemctl`-serviceherstart en een volledige Dropletherstart. De lokale proef herstartte het brokerproces; de Dockercontainer draaide niet als volledige systemd-VM.
7. Controleer de kosten- en afsluitroute, het hervatten van dezelfde Codespace en de bewaarde controlebestanden.

Pas de aangewezen servergrootte pas definitief toe nadat ook de latere complete gegevensketen is belast. De lokale proef is aanvullend geslaagd met één CPU, 512 MiB geheugen en zonder extra swap (`--memory=512m --memory-swap=512m`). Het lesformulier kiest nu het goedkoopste gepubliceerde Basic/Regular-plan: 512 MiB, 1 vCPU, 10 GiB SSD, $4 per maand op 17 november 2026. Dit bewijst nog niet dat de gehele latere lesketen op een echte 512-MiB-Droplet past. Controleer ook de installatiebelasting en alle achtergrondprocessen van de echte VM vóór de les.

## Controles herhalen

Vanuit de hoofdmap van de repository, met Docker beschikbaar:

```bash
docker build -f controles/server_03.Dockerfile -t iot-practicum-server03 .
docker run --rm --memory=1g --cpus=1 --mount "type=bind,src=$PWD,dst=/proef" iot-practicum-server03 /opt/iot/venv/bin/python controles/controleer_server_03.py
docker run --rm --mount "type=bind,src=$PWD,dst=/proef,readonly" iot-practicum-server03 /opt/iot/venv/bin/python controles/controleer_notebook_03.py
```

Dit zijn Bash-opdrachten voor een ontwikkelomgeving met Docker; Docker is geen vereiste voor studenten. De serverproef weigert buiten een nieuwe Dockercontainer te draaien. Hij maakt tijdelijke accounts en certificaten binnen die container. De uitgevoerde notebook wordt opgeslagen onder `gegevens/werk/controle03/`, buiten Git. De studentbestanden worden niet automatisch overschreven. Er wordt niets naar DigitalOcean verstuurd.

## Herstel en geldigheid

Het oefencertificaat is 90 dagen geldig. Plan bij langer gebruik een gecontroleerde vernieuwing. Als de CA wordt vervangen, moeten alle betrokken clients het nieuwe openbare CA-certificaat via een vertrouwde route krijgen. Bewaar en vervang privésleutels niet via Git.

Een vergeten API-wachtwoord vereist een nieuwe controlewaarde onder begeleiding; de installatie overschrijft de bestaande waarde niet. Mosquitto-wachtwoorden kunnen met `mosquitto_passwd` per account worden gewijzigd. Houd altijd een werkende beheersessie of herstelconsole beschikbaar bij toegangsaanpassingen.

## Uitgebreide aanmaakroute

Sectie 4 bevat acht afzonderlijke stappen met uitleg per keuze en zes extra officiële schermafbeeldingen. Studenten kiezen Password, zetten alle optionele extra diensten uit, laten Startup scripts uitgeschakeld en voegen hun voornaam toe als tag. De prijs wordt gecontroleerd tegen de [officiële prijslijst](https://www.digitalocean.com/pricing/droplets); een screenshot met een Premium-plan is alleen een bedieningsvoorbeeld. De codecellen zijn bij deze uitbreiding inhoudelijk ongewijzigd.
