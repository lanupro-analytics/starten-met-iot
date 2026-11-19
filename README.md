# Gegevensuitwisseling bij biggen

Dit practicum onderzoekt hoe gewichten en voederopname worden opgeslagen, uitgewisseld en gecombineerd. Je werkt in GitHub Codespaces, onderzoekt lokaal een databank en richt vervolgens een eigen server in.

## Beginnen

De bestaande [introductie 00](notebooks/00_start_hier.ipynb) blijft beschikbaar.

Begin met **[01 · Je eigen werkomgeving inrichten](notebooks/01_werkomgeving_inrichten.ipynb)**. De studentenversies staan in `notebooks/`, zonder vooraf ingevulde antwoorden of docent-hulpcellen.

1. Gebruik als basisbranch **`main`**, zodra de gewenste lesbestanden daarin beschikbaar zijn.
2. Maak jouw eigen **`student/voornaam_achternaam`**-branch, met kleine letters en zonder spaties.
3. Start een Codespace op die branch en open notebook 01.
4. Ga verder met **[02 · Databanken verkennen en aanvullen](notebooks/02_databanken_verkennen_en_aanvullen.ipynb)**.
5. Doorloop vervolgens **[03 · Je eigen server inrichten](notebooks/03_eigen_server_inrichten.ipynb)**. Iedere deelnemer gebruikt een eigen Droplet in team `lanupro-tech`, project `starten-met-iot`.

Voor een docent-proefuitvoering vanuit `docent/notebooks/` kun je `student/proefdocent` gebruiken. Bewaar een bestaande eigen branch om werk te hervatten. Zolang een notebook op de ontwikkelbranch staat, volg je de bijbehorende controlehandleiding in `documentatie/` voor het kiezen van de proefbranch.

Ga daarna verder met **[04 · Metingen publiceren met MQTT](notebooks/04_metingen_publiceren_met_mqtt.ipynb)**. Je maakt een JSON-bericht, volgt de ontvangst en publiceert een kleine selectie uit je eigen werkdatabase.

Vervolg met **[05 · Metingen ontvangen en opslaan](notebooks/05_metingen_ontvangen_en_opslaan.ipynb)**. Je richt de ontvanger op je eigen server in, voegt de stroom van een andere gebruiker toe en controleert de volledige databases.

Notebooks 06–08 zijn nog niet beschikbaar. De oude oefeningen staan in het [archief](archief/LEESMIJ.md).

## Bestanden

| Map | Inhoud |
|---|---|
| `notebooks/` | Ongewijzigde introductie 00 en studentenversies 01–05 |
| `docent/notebooks/` | Volledig uitgewerkte docentversies 01–05 |
| `hulpmiddelen/` | Scripts voor startdatabanken en studentenversies |
| `gegevens/origineel/` | Vrijgegeven lesdatabanken met de eerste vier weken |
| `gegevens/oefeningen/` | Vier fictieve oefenrijen in Excel en CSV |
| `gegevens/werk/` | Werkbestanden in de Codespace, niet opgenomen in Git |
| `gegevens/inlevering/` | Kleine, bewust bewaarde inleverbestanden |
| `server/` | Programma's, pakketversies en configuraties voor notebooks 03 en 05 |
| `programmatuur/` | Controles en ondersteunende notebookcode |
| `afbeeldingen/schermafbeeldingen/` | Bedieningsvoorbeelden met bronvermelding |
| `documentatie/` | Controle- en voorbereidingsinstructies |
| `controles/` | Technische uitvoeringscontroles |
| `archief/` | Eerdere oefeningen en bijbehorende bestanden |

Een branch is geen besloten opslagplaats. Deze repository is openbaar. Bewaar geen wachtwoorden, tokens, privésleutels of niet-vrijgegeven onderzoeksdata in Git.

## Hervatten

Bewaar aan het eind van een sessie het notebook, commit de bedoelde bestanden en push naar je eigen branch. Controleer je bestanden op GitHub. Stop daarna de Codespace via [github.com/codespaces](https://github.com/codespaces). Hervat dezelfde Codespace tijdens de volgende sessie.

GitHub Codespaces en DigitalOcean hebben afzonderlijke facturering. Voor notebooks 01 en 02 is geen DigitalOcean-server nodig. Vanaf notebook 03 blijven de oefenservers beschikbaar volgens de afspraak met de docent; uitzetten is niet hetzelfde als verwijderen of stoppen met betalen.

## Docentcontrole

Zie [notebook 01 controleren](documentatie/notebook_01_controleren.md), [notebook 02 controleren](documentatie/notebook_02_controleren.md), [notebook 03 controleren](documentatie/notebook_03_controleren.md), [notebook 04 controleren](documentatie/notebook_04_controleren.md) en [notebook 05 controleren](documentatie/notebook_05_controleren.md) voor de testvolgorde, uitgevoerde controles en beperkingen.

## Licentie

Lesmateriaal: CC BY-NC-SA 4.0. Broncode: MIT. De oorspronkelijke reeks staat met haar bronvermeldingen in het archief. Voor afbeeldingen van derden gelden de afzonderlijke bronvermeldingen en rechten in [BRONNEN.md](afbeeldingen/schermafbeeldingen/BRONNEN.md).
