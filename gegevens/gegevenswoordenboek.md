# Gegevenswoordenboek

## Bestanden en selectie

`asserva.db` bevat gewichtsgegevens en `schauer.db` voederopnamegegevens. Dit zijn SQLite-lesdatabanken, opgebouwd uit de aangeleverde verwerkte bezoekgegevens. De namen verwijzen naar de toestelfabrikanten; de tabellen zijn geen officiële fabrikantenschema's.

Elke databank bevat `metingen` en `metadata`. De basisselectie gebruikt het bronveld `DATE`: vanaf 24 augustus 2023, tot 21 september 2023 exclusief. Dat levert 80.028 gewichtsrecords en 146.649 voederopnamerecords op. De 52.194 latere gewichtsrecords en 86.952 latere voederopnamerecords blijven buiten deze startbestanden. De latere Excel-aanvulling behoort bij notebook 08.

Alle dieren, herkomstcodes en kwaliteitsvlaggen binnen de basisperiode zijn behouden. Een rij is een record uit de verwerkte bron; door handmatige en geïmputeerde gewichten is niet elke rij noodzakelijk een rechtstreeks gemeten bezoek. De eerste meetdag begint rond de middag. Een reeks van 28 kalenderdagen bewijst geen volledige meetdekking van 28 etmalen.

## Velden in beide bronnen

De oorspronkelijke kolomnamen blijven behouden. Daardoor blijft de koppeling met de bronnen controleerbaar. Nieuwe oefentabellen en eigen kolommen hebben Nederlandse namen.

| Bronveld | SQLite-type | Betekenis en gebruik |
|---|---|---|
| `ROW_ID` | TEXT, PRIMARY KEY, NOT NULL | Unieke recordidentificatie binnen één bron. 27 of 28 cijfers; altijd als tekst bewaren. |
| `EID` | TEXT | Dieridentificatie. Gedeelde code voor koppeling tussen bronnen; aanwezigheid in beide bronnen is nog geen geldige analyseset. |
| `PEN` | TEXT | Hokcode zoals aangeleverd. |
| `TREAT` | TEXT | Behandelingscode; betekenis van de categorieën nog niet vastgelegd. |
| `GENDER` | TEXT | Geslachtscode zoals aangeleverd; categoriebetekenis nog niet bevestigd. Numeriek ogende codes zoals `0` en `0.0` worden als brontekst behouden. |
| `DATE` | TEXT | Datum in `JJJJ-MM-DD`; gebruikt voor de splitsing in basis en aanvulling. |
| `TIMEstart`, `TIMEstop` | TEXT | Start- en eindtijd volgens de bron, zonder tijdzone-offset. |
| `TIMESTAMPstart`, `TIMESTAMPstop` | TEXT | Gewichten: compacte tijdstempel `JJJJMMDDuummss`; voeder: datum en tijd als tekst. Niet omgerekend. |
| `PROCESSTIME` | REAL | Numeriek verwerkingsveld; definitie en eenheid nog te bevestigen. |
| `TRIALDAY` | REAL | Numeriek proefdagveld; referentiepunt nog te bevestigen. |
| `DTMARKER`, `DTMARKER_INT` | REAL | Numerieke markeringen uit de bronverwerking; interpretatie nog te bevestigen. |
| `DATAORIGIN` | TEXT | Herkomstcode, bijvoorbeeld `0`, `imputed`, `manualweighing`, `allocation` of `exit`; beschikbare codes verschillen per bron. |
| `ERROR` | TEXT | Foutcode of tekst uit de bronverwerking, bijvoorbeeld `no error`. |
| `FILTER` | TEXT | Filterstatus uit de bronverwerking: onder andere `0`, `flagged` en `errored`. |

## Gewichtsbron

| Bronveld | SQLite-type | Betekenis en eenheid |
|---|---|---|
| `VBW` | REAL | Lichaamsgewicht, **kg**. |
| `FLAG_VBW_polyn` | TEXT | Kwaliteitsvlag uit de bronverwerking; algoritme en beslisregel nog niet vastgelegd. |
| `FLAG_VBW_hampel` | TEXT | Idem; oorspronkelijke waarde behouden. |
| `FLAG_VBW_matern1` | TEXT | Idem; oorspronkelijke waarde behouden. |
| `FLAG_VBW_matern2` | TEXT | Idem; oorspronkelijke waarde behouden. |

## Voederbron

| Bronveld | SQLite-type | Betekenis en eenheid |
|---|---|---|
| `VFI` | REAL | Voederopname per bezoek, **g**. Een nulwaarde is geen ontbrekende waarde. |
| `VD` | REAL | Bezoekgerelateerd numeriek veld; definitie en eenheid nog te bevestigen. |
| `VFIS` | REAL | Voedergerelateerd numeriek veld; definitie en eenheid nog te bevestigen. |
| `FLAG_VFI`, `FLAG_VD`, `FLAG_VFIS` | TEXT | Kwaliteitsvlaggen. De betekenis van bijvoorbeeld `below 2 g` is zichtbaar in de tekst; de volledige beslisregels zijn nog niet vastgelegd. |
| `BWCLASS` | TEXT | Klassecode uit de bronverwerking; klassegrenzen nog te bevestigen. |

## Identificatie, tijd en kwaliteit

De eenheden kg voor `VBW` en g voor `VFI` zijn bevestigd. De tijd is vermoedelijk Belgische lokale tijd. De bronnen bevatten geen expliciete tijdzone-offset; er wordt daarom geen UTC-label toegevoegd of tijdzoneconversie toegepast. De selectie gebruikt uitsluitend de bronkalenderdatum. Bezoeken die over middernacht lopen vragen bij latere intervalberekeningen een expliciete keuze.

Tekstvelden blijven letterlijk behouden, inclusief broncodes. Niet-lege waarden in de numerieke velden worden als SQLite REAL opgeslagen; dit zijn binaire benaderingen van decimale waarden. Lege numerieke velden worden NULL, niet nul. Lange identificaties gaan nooit door een getalconversie. De oorspronkelijke CSV-bestanden blijven het referentiepunt voor de exacte bronnotatie.

Een primaire sleutel dwingt uniciteit af. SQLite gebruikt verder een flexibele typering: een opgegeven gegevenstype is niet in alle omstandigheden een harde inhoudscontrole. Daarom controleert de aangeleverde code ook de feitelijke inhoud en niet alleen de kolomdefinitie.

Kwaliteitsvlaggen zijn geen automatische opdracht om een rij te verwijderen. De regels voor een biologische analyse worden later afzonderlijk vastgelegd. Ook moet dan worden nagegaan of imputaties gebruikmaken van metingen uit latere dagen. Notebook 02 inspecteert en bewaart deze informatie; het berekent nog geen voederconversie.

## Oefengegevens

`oefenhokken.xlsx` en `oefenhokken.csv` bevatten dezelfde vier **fictieve contextrecords**. De tabel `oefen_hokken` heeft de kolommen `hok` (TEXT PRIMARY KEY NOT NULL), `afdeling` (TEXT), `controlevolgorde` (INTEGER) en `notitie` (TEXT). De namen en notities beschrijven geen werkelijke proefinrichting. De optionele vergelijkingstabel `oefen_hokken_csv` is geen tweede bron van meetgegevens.

## Herkomstcontrole

Brongewichten: `20240207_processed_data_body_weight_by_visit.csv`.

Bronvoeder: `20240225_processed_data_feed_intake_by_visit.csv`.

De verwerkingsdatum in de bestandsnaam is niet de meetdatum. De broncontrolesommen, databasecontrolesommen, kolomtypes en aantallen staan in `origineel/maakcontrole.json`. De metadata in iedere database bevatten de bronidentiteit en selectiegrenzen. Het hulpmiddel `hulpmiddelen/maak_startdatabanken.py` maakt de selectie reproduceerbaar en weigert bestaande startdatabanken te overschrijven.
