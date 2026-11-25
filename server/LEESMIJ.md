# Serverbestanden voor notebooks 03, 05 en 06

Deze bestanden horen bij de stap-voor-stapinstructies in `03_eigen_server_inrichten.ipynb`. Kopieer ze naar een eigen nieuwe Debian 13-oefenserver en volg het notebook. Er is geen automatisch installatiescript dat alle stappen zonder controle uitvoert.

| Bestand | Functie |
|---|---|
| `certificaat_maken.py` | Eigen oefen-CA en servercertificaat met IPv4-adres; behoudt bestaande certificaten |
| `toegang_api.py` | Verborgen wachtwoordinvoer en opslag van een gezouten controlewaarde |
| `statusdienst.py` | Beveiligd controleantwoord op `/gezondheid` |
| `requirements.txt` | Geteste Python-pakketten voor de virtuele omgeving |
| `configuratie/mosquitto.conf` | MQTT met TLS en account- en topicrechten |
| `configuratie/nginx.conf` | HTTPS en doorgeven naar de interne Python-dienst |
| `diensten/iot-status.service` | Starten en bewaken van de Python-dienst onder gebruiker `iot` |

MQTT-eigenaar en MQTT-lezer krijgen afzonderlijke wachtwoorden. De API en SSH gebruiken ieder een ander wachtwoord. Privésleutels, wachtwoordbestanden en controlewaarden worden tijdens de installatie op de server gemaakt; ze staan niet in deze map of in Git.

Een MQTT-broker slaat berichten niet vanzelf in een SQLite-database op. Notebook 05 voegt de ontvanger en verzameldatabase toe. Notebook 06 breidt de bestaande webdienst uit met de meetgegevens-API.

Zie `documentatie/notebook_03_controleren.md` voor de uitgevoerde lokale controles en de nog noodzakelijke DigitalOcean- en Codespaces-proef.

## Ontvangst en opslag vanaf notebook 05

Volg de stappen in `05_metingen_ontvangen_en_opslaan.ipynb`. Kopieer de vier ontvangscripts, `diensten/iot-ontvanger.service` en `configuratie/ontvangst-capaciteit.conf`. De laatste configuratie begrenst de wachtrijen voor volledige beginsets en wordt actief na een bewuste brokerherstart.

`ontvangst_instellen.py` bewaart eigen en partnerlezersgegevens interactief in `/etc/iot/ontvangst.geheim.json`, als root:iot met mode 0640. Dit bestand bevat clientwachtwoorden en mag nooit in Git of een notebook terechtkomen. Alleen openbare CA-certificaten worden uitgewisseld, met een via een vertrouwde route gecontroleerde vingerafdruk.

`ontvangen.py` draait als servicegebruiker iot en schrijft `/var/lib/iot/verzamelde_metingen.db`. `meetgegevens.py` valideert en bewaart de inhoud. `ontvangst_status.py` leest een samenhangend overzicht zonder geheimen. De ontvanger start automatisch na reboot en maakt opnieuw verbinding. Mosquitto blijft handmatig te starten.

De [controlehandleiding voor 05](../documentatie/notebook_05_controleren.md) beschrijft tests, volledige aantallen, beveiliging en de nog noodzakelijke echte-serverproef.

## Meetgegevens opvragen vanaf notebook 06

`webdienst.py` leest `/var/lib/iot/verzamelde_metingen.db` via GET-aanvragen. De bestaande API-aanmelding, certificaten, Nginx-configuratie en interne poort blijven behouden. Installeer `configuratie/api-uitbreiding.conf` als systemd-aanvulling op `iot-status.service` en herstart die dienst volgens het notebook. De oorspronkelijke statusdienst blijft beschikbaar als herstelroute.

Het [API-contract](../documentatie/api_gegevenscontract.md) beschrijft filters, tijdsgrenzen, paginering en foutcodes. De [controlehandleiding voor 06](../documentatie/notebook_06_controleren.md) beschrijft de uitgevoerde tests en de resterende proef op een echte Droplet. De uitbreiding verandert de MQTT-ontvanger en de handmatige start van Mosquitto niet.
