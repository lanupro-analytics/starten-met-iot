# Notebook 01 controleren

## Uitvoering als deelnemer

1. Open de branch `codex/practicum-01-werkomgeving` op GitHub.
2. Lees notebook 01 en maak daarvan een eigen branch, bijvoorbeeld `student/proefdocent`.
3. Start een Codespace op die branch en open `docent/notebooks/01_werkomgeving_inrichten.ipynb`.
4. Doorloop de instructies. De code en modelantwoorden zijn al ingevuld. De rol `gewichten` is geschikt voor deze proef.
5. Controleer de echte handelingen: branch maken, Codespace starten, tekstbestand aanpassen, selectief committen, pushen, controleren op GitHub en hervatten.

De docentnotebook is de inhoudelijke bron. Er is nog geen studentenversie gegenereerd en er zijn nog geen nieuwe notebooks 02–08.

## Beoordelingspunten

- Is bij iedere stap duidelijk of je op GitHub, in de Codespace-editor of in een codecel werkt?
- Kun je de knop terugvinden met de tekst en de schermafbeelding?
- Stopt de eerste codecel begrijpelijk als je nog niet op je eigen branch staat?
- Begrijp je na de opslagproef waar het werkbestand staat?
- Komt alleen het bedoelde werk in de commit?
- Verschijnt het controlebestand op de eigen branch?
- Blijft de eigen notitie behouden bij hervatten?

Leg opmerkingen vast met sectienummer en cel-ID, zonder geheime gegevens.

## Technische controle

Voer vanuit de hoofdmap in de meegeleverde Python-omgeving uit:

```bash
python controles/controleer_notebook_01.py
```

Deze controle gebruikt tijdelijke Git-repositories. Ze schrijft geen branches naar GitHub en maakt geen cloudservers. Ze controleert uitvoering vanuit een ondermap, opnieuw uitvoeren, bescherming van gedeelde branches, ongeldige rolkeuze en de controlesommen van notebook 00.

Een succesvolle lokale controle is geen bewijs van GitHub-accountrechten of van een geslaagde echte Codespace-start. Die onderdelen worden met de deelnemersroute gecontroleerd.

## Voorbereiding door de docent

Controleer de schrijfrechten op de gedeelde repository, de aangewezen basisbranch en Codespaces-beschikbaarheid. Gebruik deelnemerscodes zonder spaties of persoonsgegevens. Wijs de rolverdeling zelf toe.

De interne specificatie en bronverkenning blijven lokaal beschikbaar, maar worden niet meegepubliceerd. De repository bevat nog geen onderzoeksdata. Definitieve verspreiding van die data en de studentenversies wordt afzonderlijk voorbereid.

## Uitgevoerde controle op 17 november 2026

De Dockeromgeving is opgebouwd met de meegeleverde Dockerfile en requirements.txt. Alle zes automatische controles slagen. De vijf codecellen zijn bovendien achtereenvolgens uitgevoerd met een echte Jupyter-kernel in een tijdelijke repository op student/proefdocent. De voorbeelduitvoer is opgenomen in de docentnotebook. De relatieve notebooklinks en de oorspronkelijke bestanden in het archief zijn gecontroleerd.

De GitHub- en Codespaces-bedieningsstappen moeten nog via de deelnemersroute hierboven worden doorlopen. De lokale uitvoering bewijst niet dat accountrechten, quota en de editorbediening in een echte Codespace correct zijn ingesteld.
