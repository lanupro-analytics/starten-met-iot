# Notebook 08 controleren

## Voorwaarden en uitvoering

Gebruik de eigen branch en Codespace uit 01, de werkdatabase uit 02, werkende diensten uit 03–06 en de onveranderde beginsituatie uit 07. De partner gebruikt de andere rol. Notebook 08 vraagt twee MQTT/API-wachtwoorden interactief op en bevat expliciete pauzes voor servercontrole, publicatie door de partner en bestandsuitwisseling. Alle Python-cellen kunnen in volgorde worden uitgevoerd zodra die handelingen zijn gedaan.

De docentbron is `docent/notebooks/08_nieuwe_gegevens_toevoegen_en_interpreteren.ipynb`. Oplossingscellen zijn gemarkeerd. De generator ondersteunt `--nummer 8`. Er is geen studentenversie vrijgegeven door deze wijziging.

## Gegevens en controles

De twee werkboeken in `gegevens/aanvulling/` bevatten 52.194 gewichtsrecords en 86.952 voederrecords. De meetbladen heten `week_5` en `resterende_dagen`. De invoer behoudt ROW_ID als tekst en alle numerieke waarden en kwaliteitsvlaggen. Alleen TREAT is in de aanvulling bewust leeggelaten. De exacte hok-behandelingssleutel wordt niet getoond.

Let op voor publicatie van de volledige reeks: de reeds bestaande startdatabases bevatten een TREAT-kolom met bronwaarden. Notebook 08 verandert die eerdere bestanden niet. Het achterwege laten van die kolom in analyses en grafieken is geen toegangsbeveiliging van de oorspronkelijke behandelingsinformatie. Beoordeel afzonderlijk of de startbestanden voor een volledig blinde oefening moeten worden aangepast.

De import controleert de SHA-256 van de vrijgegeven werkboeken, kolomtypen, datumgrenzen, aantallen en unieke identificaties. Zij schrijft transactioneel. Een bestaande identieke rij wordt overgeslagen, een inhoudsconflict draait de import terug. Ook de oude rijen worden niet vervangen. Een back-up vóór de eerste toevoeging blijft onder `gegevens/werk/`.

Na MQTT-publicatie vergelijken beide partners de API-metadata met de inhoudsvingerafdrukken van de eigen en partnerbron. De API-import actualiseert `analyse_06.db` zonder de oude controlebestanden te herschrijven. Herhaalde import levert nul extra records op. Verwachte totalen zijn 132.222 en 233.601, samen 365.823.

## Rekenmethode

De vier oorspronkelijke intervallen worden met uitsluitend de oorspronkelijke bronperiode opnieuw berekend en met alle vier bewaarde tabellen uit 07 vergeleken. Relatieve en absolute tolerantie zijn 1e-10 wegens de CSV-export met twaalf significante cijfers. Bronpopulatie en methode blijven gelijk.

De tijdgrafieken behouden die vier intervallen en voegen 20–21 september, 21–28 september en 28 september–5 oktober toe. Het overgangsinterval duurt één dag en is gevoeliger voor schommelingen. Alle eindgrenzen zijn exclusief voor voederopname. De gedeeltelijke dag van 5 oktober ondersteunt alleen de schatting van het eindgewicht.

De periodetabel berekent basis (25 augustus–20 september), aanvulling (21 september–5 oktober) en geheel (25 augustus–5 oktober) elk rechtstreeks met dezelfde methode. Zij middelt geen conversies. De drie perioden kunnen verschillende bruikbare dieren bevatten. De optionele oefening vergelijkt een vaste groep over basis en aanvulling.

Controlewaarden:

- Bruikbare dieren in de zeven intervallen: 77, 98, 98, 98, 86, 98, 77.
- Voor hokken 1 en 2 ontbreekt in de aanvulling en gehele periode een omsloten eindgewicht. Geen conversie berekenen of extrapoleren.
- Hok 4, aanvulling: tien dieren, ongeveer 772,503 g groei/dier/dag, 1.046,829 g voeder/dier/dag en conversie 1,355112.
- Hok 9, aanvulling: tien dieren, ongeveer 679,776 g groei/dier/dag, 1.031,743 g voeder/dier/dag en conversie 1,517768.

Behandelingstoewijzing blijft een hypothese. `onbeslist` is geldig met een inhoudelijke verklaring. Het uitgewerkte advies kiest een beperkte vervolgproef met `lager_kort`, niet een aangetoonde optimale strategie. De ontbrekende behandelingssleutel, gezondheid en prijzen verhinderen zo'n conclusie.

## Automatische inlevering

`gegevens/inlevering/` krijgt drie PNG-figuren, `08_eigen_broncontrole.json`, `08_eindcontrole.json`, `08_analysedatabase.db.gz` en `resultaten_08/` met CSV-tabellen, hokhypothesen en advies. De snapshot gebruikt SQLite-back-up, integriteitscontrole en gzip. Een bestand boven 95 MB wordt niet als gewone Git-inlevering aanvaard. De oorspronkelijke analysedatabase blijft in de werkmap.

Een snapshot kan naar een aparte herstelmap worden uitgepakt met `gzip.open` en vervolgens met DB Browser of SQLite worden gelezen. Controleer eerst de SHA-256 uit `08_eindcontrole.json`. Vervang nooit ongemerkt de actuele werkdatabase met een oude snapshot.

## Ontwikkelcontroles

Gebruik Codespaces of Linux voor deze controles, inclusief de Bash-syntaxcontrole. Op Windows moet Git Bash als `bash` in het zoekpad beschikbaar zijn. Voer `python controles/test_aanvulling_08.py` en `python controles/controleer_notebook_08.py` uit. De ketenproef `controles/keten_08.py` weigert uitvoering buiten een wegwerpcontainer. Zij start een lokale TLS-broker, twee ontvangprogramma's en twee HTTPS-diensten. De bestaande basis wordt als fixture ingelezen. Alle 139.146 nieuwe records gaan door MQTT. Beide notebookrollen worden door een echte Jupyter-kernel uitgevoerd. De test vervangt alleen interactieve wachtwoordinvoer, lokale testpoorten en handmatige coördinatiemomenten. Zij controleert broninhoud, herhaling, referentieberekeningen en behoud van de beginsituatie.

De lokale proef is geen nieuwe test van campusnetwerk of DigitalOcean-accountrechten. Er worden geen echte studentservers gewijzigd.

Technische referenties: [openpyxl read-only mode](https://openpyxl.readthedocs.io/en/stable/optimized.html) en [SQLite Connection.backup](https://docs.python.org/3/library/sqlite3.html#sqlite3.Connection.backup).

## Uitgevoerde verificatie

Op 25 november 2026 is de volledige ketenproef geslaagd voor beide rollen, met alle 139.146 aanvullende records en 365.823 records in elke analysedatabase. Herhaalde Excel- en API-import voegden nul records toe. Alle referentiewaarden klopten en de vijf bestanden van beginsituatie_07 bleven byte voor byte behouden. De vier importtests en de notebookcontrole slaagden. De tijdelijke studentenversie bevat 70 cellen, zonder de negen oplossingscellen en zonder bewaarde uitvoer. De docentnotebook bevat 79 cellen, waaronder 21 uitgevoerde codecellen. De voorbeeldsnapshot is ongeveer 52 MB.
