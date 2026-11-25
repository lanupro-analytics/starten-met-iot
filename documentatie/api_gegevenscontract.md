# API-gegevenscontract, versie 1

De API uit notebook 06 leest de verzameldatabase uit notebook 05. De ontvanger en het MQTT-contract blijven ongewijzigd. De dienst gebruikt de bestaande Nginx-configuratie, TLS-certificaten en het account `eigenaar` met het afzonderlijke **API-Droplet wachtwoord**. HTTP Basic wordt uitsluitend over HTTPS gebruikt. De controlewaarde blijft in `/etc/iot/api.controlewaarde`. Geen wachtwoord of serveradres komt in het inleververslag.

## Paden en antwoorden

Alle vier GET-paden vragen authenticatie. De interne Uvicorn-poort 8000 luistert alleen op 127.0.0.1. Extern blijft uitsluitend HTTPS 443 nodig.

| Pad | Antwoord |
|---|---|
| `/gezondheid` | Bestaande statusvelden plus `api_versie: 1` |
| `/metadata` | Vaste opslaggrens, aantallen en inhoudsvingerafdruk per bron, beschikbare hokcodes, eenheden en kalenderinterpretatie |
| `/metingen` | `api_versie`, `grens`, `aantal`, `volgende_na` en een lijst `metingen` |
| `/openapi.json` | Beveiligde OpenAPI-documentatie |

Er is geen schrijfeindpunt. Swagger UI is niet ingeschakeld. De bestaande strikte Content-Security-Policy hoeft daardoor niet verruimd te worden voor externe scripts. De notebook toont de OpenAPI-parameters als tabel.

## Filters

| Parameter | Betekenis |
|---|---|
| `meettype` | `gewichten` of `voederopname`, weglaten levert beide |
| `hok`, `dier_id` | Exacte tekstvergelijking, maximaal 100 tekens |
| `vanaf` | Bronkalenderdatum vanaf deze datum, inclusief |
| `tot` | Bronkalenderdatum vóór deze datum, exclusief |
| `limiet` | 1 tot 1000, standaard 20 |
| `na` | Interne opslagpositie van de vorige pagina, standaard 0 |
| `grens` | Vaste maximale opslagpositie voor deze overdracht |

Datums gebruiken ISO-datumtekst `JJJJ-MM-DD` en het opgeslagen veld `datum`, afkomstig uit `bronrecord.DATE`. Dit is geen filter op bezoekstart of -einde. Zonder tijdzonebevestiging vindt geen UTC-conversie plaats. Vanaf moet vóór tot liggen. Onbekende of herhaalde parameters worden afgewezen. SQL gebruikt gebonden parameterwaarden.

Gewichten blijven kg, voederopname g. `record_id` blijft exact tekst van 27 of 28 cijfers. `null` blijft ontbrekend en nul blijft een getalwaarde. De API levert de volledige canonieke meetinhoud uit 05, inclusief `hokmetadata`, `bronrecord` en kwaliteitsvlaggen. Het transportveld `deelnemer` ontbreekt. Er wordt geen analytische selectie uitgevoerd.

## Paginering en consistentie

De volgorde is oplopende SQLite-rowid, de interne opslagvolgorde. Dit is geen chronologische of analytische volgorde. De cliënt vraagt `/metadata` op en gebruikt de ontvangen `grens` voor alle volgende pagina's. Vervolgens volgt hij `volgende_na` tot dit `null` is. Filters en grens blijven gelijk. De grens is uitsluitend een overdrachtspositie, geen meetidentificatie.

De ontvanger uit 05 voegt records toe en wijzigt of verwijdert bestaande metingen niet. Daardoor vormen records tot de vastgelegde grens een stabiele selectie terwijl nieuwe records binnenkomen. Deze nieuwere records worden bij de volgende volledige import opgehaald. Vervanging, VACUUM, verwijdering of rechtstreekse wijziging van de verzameldatabase tijdens import valt buiten dit contract. De eindcontrole vergelijkt aantallen en SHA-256 per bron met de metadata van de start. Een afwijking draait de lokale import terug. Een grens boven het huidige maximum geeft 409.

Iedere aanvraag gebruikt een korte SQLite-leestransactie met `mode=ro` en `query_only`. De metadata worden binnen één transactie berekend. De API houdt geen servertransactie open tussen HTTP-aanvragen.

## Fouten en hervatten

| HTTP-status | Betekenis |
|---|---|
| 200 | Geldige aanvraag, eventueel lege selectie |
| 401 | Ontbrekende of ongeldige aanmelding |
| 404 | Onbekend pad |
| 405 | HTTP-methode niet ondersteund |
| 409 | Opslaggrens past niet meer bij de database |
| 422 | Ongeldige parameters |
| 429 | Nginx-aanvraaglimiet bereikt |
| 502 | Nginx kan Uvicorn niet bereiken |
| 503 | Verzameldatabase ontbreekt of is tijdelijk niet leesbaar |

De API publiceert geen databasepaden of stacktraces in foutantwoorden. Nginx-fouten kunnen HTML zijn. De client controleert de status vóór JSON wordt verwerkt. Clientaanvragen hebben verbindings- en leestime-outs en volgen geen redirects met credentials. Certificaatcontrole blijft ingeschakeld. API-antwoorden krijgen `Cache-Control: no-store`.

## Analysedatabase en inlevering

`gegevens/werk/analyse_06.db` heeft application_id 600106. Een bestaand bestand zonder deze markering wordt geweigerd voordat het wordt gewijzigd. De meettabel heeft `(bron, record_id)` als sleutel en bewaart zoekvelden, volledige JSON en inhoudsvingerafdruk. De tabel `ophalen` bewaart de laatste gecontroleerde metadata en tijd. Gegevens voor 07 worden dus niet afhankelijk van opgeslagen Python-variabelen.

Een volledige import vereist beide niet-lege bronnen. De client valideert ontvangen inhoud met de bestaande validator, controleert paginering, weigert dubbele records binnen één overdracht en vergelijkt beide inhoudsmanifesten. Herhaald ophalen slaat dezelfde inhoud over. Afwijkende inhoud bij dezelfde sleutel wordt niet overschreven. De gehele import is één lokale transactie. Bij een fout blijft de vorige geslaagde inhoud behouden. Een nieuw bestand kan dan leeg achterblijven. Een volgende uitvoering hervat door de volledige selectie opnieuw op te halen.

`06_apicontrole.json` bevat uitgevoerde selectie, foutproef, importresultaten en vergelijking met 05. De notebook maakt dit automatisch. Het bewijst inhoudelijke overeenkomst met de ontvangen gegevens, niet hun geschiktheid voor voederconversie.
