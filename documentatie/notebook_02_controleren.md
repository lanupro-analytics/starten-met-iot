# Notebook 02 controleren

## Proefuitvoering

De volledige versie staat in `docent/notebooks/02_databanken_verkennen_en_aanvullen.ipynb`. De instructies noemen de toekomstige studentenmap `notebooks/`: open tijdens deze proef de overeenkomstige notebook in `docent/notebooks/`. Alleen oplossingscellen hebben de tag `oplossing`. Antwoordcellen en hints blijven behouden wanneer later de studentenversie wordt afgeleid.

De ontwikkeling staat op `codex/practicum-02-databanken`. Zolang deze branch niet in `main` is opgenomen, maak je voor een nieuwe proef een eigen `student/voornaam_achternaam`-branch vanuit die ontwikkelbranch. Doorloop notebook 01 op die eigen branch om een passend werkplekcontrolebestand te bewaren. Bewaar bestaand studentenwerk voordat je van branch wisselt.

1. Hervat je eigen Codespace en voer de eerste cel uit. Je rol komt uit notebook 01.
2. Download de bijbehorende startdatabank en het kleine Excelbestand.
3. Volg de lokale DB Browser-route: structuur inspecteren, query uitvoeren, oefentabel maken en vier rijen overnemen. Controleer dat celbewerkingen met Apply zijn bevestigd en daarna met Write Changes worden opgeslagen.
4. Importeer de CSV in de aparte tabel, vergelijk de inhoud en sluit de databank.
5. Upload de bewerkte databank naar `gegevens/werk/invoer/`. Voer de overige codecellen uit, controleer de melding en het inleverbestand.
6. Voer de codecellen opnieuw uit: dezelfde databank moet opnieuw worden aanvaard. Een afwijkende bestaande werkdatabank mag niet worden overschreven.
7. Bewaar notebook en inleverbestand op je eigen branch. Bewaar daarnaast je lokale databankkopie en stop de Codespace.

Let bij de inhoudelijke beoordeling op het onderscheid tussen SQL, SQLite en DB Browser; de uitleg over tekstsleutels, eenheden en tijdstippen; de herkenbaarheid van de knoppen; en de zelfstandige opdrachten. De vier fictieve hokregels beschrijven geen echte proefhuisvesting.

## Automatische controle

Voer vanuit de hoofdmap met de meegeleverde Python-omgeving uit:

```bash
python controles/controleer_notebook_02.py
```

De acht controles behandelen beide databronnen, ontbrekende bestanden, verkeerde rollen, onvolledige oefenrijen, gewijzigde meetwaarden, bescherming van bestaande werkbestanden, de CSV en de volledige notebookcode voor beide rollen, inclusief herhaalde uitvoering. Ze gebruiken tijdelijke mappen en publiceren niets.

## Uitgevoerde controle op 17 november 2026

Alle acht automatische controles slagen in de meegeleverde Dockeromgeving. De volledige notebook is daarnaast met een echte Jupyter-kernel uitgevoerd met een gewichtsdatabank die in DB Browser op Windows is bewerkt en opgeslagen. Deze uitvoer staat in de notebook. De bronbestanden, oorspronkelijke notebooks 00 en aangepaste notebook 01 zijn ongewijzigd gebleven.

In DB Browser 3.13.1 zijn tabelvelden, het toevoegen en bevestigen van een celwaarde, SQL-uitvoering, CSV-import, opslaan en sluiten gecontroleerd. Voor de volledige vier oefenrijen is tijdens de technische proef ook SQL gebruikt; niet iedere cel is afzonderlijk met de muis ingevuld. De schermafbeeldingen komen uit die proef.

Een echte Codespaces-upload, de macOS-bediening en de volledige handmatige deelnemersroute moeten nog door de docent worden doorlopen. De lokale kerneluitvoering controleert geen GitHub-rechten of Codespaces-quota.
