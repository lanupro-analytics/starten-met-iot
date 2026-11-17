# Serverbestanden voor notebook 03

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

Een MQTT-broker slaat berichten niet vanzelf in een SQLite-database op. Deze installatie biedt nog geen ontvanger voor meetrecords of meetgegevens-API. Die worden toegevoegd in de daaropvolgende notebooks.

Zie `documentatie/notebook_03_controleren.md` voor de uitgevoerde lokale controles en de nog noodzakelijke DigitalOcean- en Codespaces-proef.
