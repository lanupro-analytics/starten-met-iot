# Notebook 02 controleren

## Proefuitvoering

De volledige versie staat in `docent/notebooks/02_databanken_verkennen_en_aanvullen.ipynb`. De instructies noemen de toekomstige studentenmap `notebooks/`: open tijdens deze proef de overeenkomstige notebook in `docent/notebooks/`. Alleen oplossingscellen hebben de tag `oplossing`. Antwoordcellen en hints blijven behouden wanneer later de studentenversie wordt afgeleid.

De ontwikkeling staat op `codex/practicum-02-databanken`. Zolang deze branch niet in `main` is opgenomen, maak je voor een nieuwe proef een eigen `student/voornaam_achternaam`-branch vanuit die ontwikkelbranch. Doorloop notebook 01 op die eigen branch om een passend werkplekcontrolebestand te bewaren. Bewaar bestaand studentenwerk voordat je van branch wisselt.

1. Hervat je eigen Codespace en voer de eerste cel uit. Je rol komt uit notebook 01.
2. Download de bijbehorende startdatabank .
3. Volg de lokale DB Browser-route: structuur inspecteren, unieke hoknummers tellen en opvragen, tabel hokken maken en tien hokrecords handmatig invullen. Controleer dat celbewerkingen met Apply zijn bevestigd en daarna met Write Changes worden opgeslagen.
4. Exporteer hokken naar CSV en importeer die in de aparte tabel hokken_csv, vergelijk de inhoud en sluit de databank.
5. Upload de bewerkte databank naar `gegevens/werk/invoer/`. Voer de overige codecellen uit, controleer de melding en het inleverbestand.
6. Voer de codecellen opnieuw uit: dezelfde databank moet opnieuw worden aanvaard. Een afwijkende bestaande werkdatabank mag niet worden overschreven.
7. Bewaar notebook en inleverbestand op je eigen branch. Bewaar daarnaast je lokale databankkopie en stop de Codespace.

Let bij de inhoudelijke beoordeling op het onderscheid tussen SQL, SQLite en DB Browser; de uitleg over tekstsleutels, eenheden en tijdstippen; de herkenbaarheid van de knoppen; en de zelfstandige opdrachten. De metadata zijn voor elk hok: gebouw M5, afdeling 1, oppervlakte 8 m².

## Automatische controle

Voer vanuit de hoofdmap met de meegeleverde Python-omgeving uit:

```bash
python controles/controleer_notebook_02.py
```

De controles behandelen beide databronnen, ontbrekende bestanden, verkeerde rollen, ontbrekende hokken en foutieve hokmetadata, gewijzigde meetwaarden, bescherming van bestaande werkbestanden, de exacte hoknummers en de volledige notebookcode voor beide rollen, inclusief herhaalde uitvoering. Ze gebruiken tijdelijke mappen en publiceren niets.

## Controle van de aangepaste oefening

De automatische controles voeren alle notebookcode voor beide rollen uit, ook bij hervatten, met tijdelijk voorbereide databanken. Ze controleren daarnaast ontbrekende of verkeerde hoknummers, gebouw, afdeling en oppervlakte, en bescherming van oorspronkelijke meetgegevens en bestaande werkbestanden.

De handmatige DB Browser-route met de nieuwe tabel moet nog door de docent worden doorlopen. De oude schermafbeeldingen van de fictieve tabeldefinitie en CSV-import zijn uit het notebook verwijderd omdat hun velden niet meer overeenkomen. Bestaande uitvoer is gewist zodat resultaten uit de oude oefening niet als nieuwe resultaten worden getoond.
