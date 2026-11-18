# MQTT-gegevenscontract, versie 1

Notebook 04 publiceert een kleine selectie echte bronrecords. Dit contract legt de aansluiting op de ontvanger in notebook 05 vast. Een brokerbevestiging is geen opslagbevestiging van die ontvanger.

## Verbinding en topics

- MQTT 5, Paho-callbackinterface versie 2, TLS op TCP 8883 met controle van CA en serveradres.
- Account `eigenaar` publiceert binnen de eigen rechten uit notebook 03. Het toekomstige partneraccount `lezer` heeft alleen leesrechten.
- Oefenberichten: `practicum/{deelnemerscode}/controle/json`.
- Bronmetingen: `practicum/{deelnemerscode}/metingen/{rol}`, met `gewichten` of `voederopname` als rol.
- Publicaties gebruiken QoS 1 en `retain=False`. Abonnementen worden bevestigd voordat een proefpublicatie begint.
- De korte notebooksessies sluiten na elke handeling. Na uitval herstelt de gebruiker de verbinding en herhaalt de publicatie. Er is geen onbeheerde reconnectlus in notebook 04.

## Berichtvelden

| Veld | Type | Herkomst of betekenis |
|---|---|---|
| schema_versie | integer | 1 |
| deelnemer | tekst | Publicerende deelnemer, geen deel van de meetidentiteit |
| bron | tekst | asserva of schauer |
| meettype | tekst | gewichten of voederopname |
| record_id | tekst | Exacte ROW_ID van 27 of 28 cijfers |
| dier_id | tekst of null | Oorspronkelijke EID, ook niet-diercodes blijven behouden |
| hok | tekst | Oorspronkelijke PEN |
| tijd | object | start en einde als ISO-datumtijd zonder UTC-offset, of null bij ontbrekende bronwaarde |
| tijdzone | tekst | Onbevestigd, vermoedelijk Europe/Brussels |
| meetveld | tekst | VBW of VFI |
| waarde | getal of null | Ongewijzigde VBW of VFI |
| eenheid | tekst | kg bij VBW, g bij VFI |
| hokmetadata | object | hok, gebouw, afdeling, oppervlakte_m2 uit notebook 02 |
| bronrecord | object | Alle oorspronkelijke velden en waarden, inclusief kwaliteitsvlaggen |

Asserva-tijdstempels worden gelezen met `%Y%m%d%H%M%S`. Schauer gebruikt `%Y-%m-%d %H:%M:%S`. Er vindt geen tijdzoneconversie plaats. De oorspronkelijke tekst blijft in bronrecord aanwezig. De JSON-omzetting weigert NaN en Infinity. SQL NULL wordt JSON null. Getal nul blijft nul. De payloadlimiet is 60.000 bytes, overeenkomstig de brokerconfiguratie.

## Identiteit, selectie en herstel

De logische sleutel is `(bron, record_id)`. Gebruik geen nieuwe UUID per verzending en geen MQTT-pakketnummer als meetidentiteit. Verschillende deelnemers kunnen dezelfde aangeleverde bronrij publiceren. De toekomstige ontvanger controleert de combinatie van topic, deelnemer, bron en meettype en valideert de payload vóór opslag. Identieke bronmetingen worden niet dubbel opgeslagen. Inhoudelijke conflicten worden zichtbaar gemeld, niet stilzwijgend overschreven.

`lees_metingen` levert records in de volgorde DATE, ROW_ID. Standaard gaat het om twintig records. `limiet=None` levert alle records als iterator. De selectie verwijdert geen kwaliteitsvlaggen en voert geen analytische filtering uit. Hokmetadata zijn een momentopname bij de publicatie. Deze versie deelt toevoegingen, geen latere wijzigingen of verwijderingen.

`publiceer_selectie` registreert een succesvolle PUBACK per bestemming, topic, bron en record_id in een aparte lokale SQLite-administratie. Een gewone herhaling slaat bevestigde records binnen de aangeboden selectie over. `opnieuw=True` verstuurt die selectie opnieuw. Gewijzigde inhoud bij een eerder geregistreerde identiteit geeft een fout. De administratie is geen meetdatabase en geen bewijs van ontvangst bij een partner.

Een onderbreking tussen brokerbevestiging en lokale registratie kan een herhaling veroorzaken. Verlies van de lokale administratie kan eveneens leiden tot herpublicatie. Een toekomstige ontvanger moet daarom altijd duplicaten afhandelen. Start in notebook 05 eerst beide ontvangers, herpubliceer daarna beide volledige beginsets en controleer de opgeslagen aantallen. Dit geldt ook wanneer notebook 04 reeds is afgerond.

## Uitvoering vanaf notebook 05

De ontvanger valideert strikt schema, bron/rol/eenheid, topic/deelnemer, lange tekstidentificaties, bronvelden, tijdrepresentatie en hokmetadata. Ongeldige berichten verhogen een teller en stoppen de ontvanger niet. Nul blijft een geldige getalwaarde en null blijft ontbrekend. Kwaliteitsvlaggen blijven behouden.

De serverdatabase bewaart `(bron, record_id)` als samengestelde primaire sleutel. `inhoud_json` bevat de canonieke inhoud zonder deelnemer. `eerste_deelnemer` bewaart afzonderlijk de eerste transportherkomst. Identieke herhalingen verhogen dubbel. Afwijkende inhoud bij een bestaande sleutel verhoogt conflict en overschrijft niets. Een inhoudsmanifest vergelijkt op record_id gesorteerde regels `record_id:inhoud_sha256` met de broncontrole.

De ontvanger gebruikt één SQLite-schrijver met WAL en synchronous FULL. Ontvangstbevestigingen worden pas na de transactie verstuurd. Na uitval maakt iedere client opnieuw verbinding en vraagt hetzelfde abonnement opnieuw aan. Historie wordt expliciet hergepubliceerd.

De volledige publicatie gebruikt groepen van maximaal honderd records. Brokerbuffers zijn begrensd via `server/configuratie/ontvangst-capaciteit.conf`. Een buffer kan bij overbelasting vollopen. Daarom vormen bron- en ontvangstmanifesten, niet uitsluitend PUBACK-tellingen, de eindcontrole. Alle oorspronkelijke metingen blijven bewaard, ook wanneer ze voor latere analyse moeten worden uitgesloten.
