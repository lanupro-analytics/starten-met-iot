# Notebook 05 controleren

De volledige versie staat in `docent/notebooks/05_metingen_ontvangen_en_opslaan.ipynb`. Ze bouwt voort op de werkdatabase uit 02, de serverinrichting uit 03 en de berichtstructuur uit 04. De studentenversie wordt later afgeleid door uitsluitend de gemarkeerde oplossingscellen te verwijderen.

## Proefroute

1. Gebruik twee eigen deelnemersomgevingen met verschillende rollen. Behoud de oorspronkelijke bronbestanden en de bestaande notebooks.
2. Kopieer de nieuwe serverbestanden en het begrensde brokerbufferbestand naar iedere server. Herstart de broker om de aanvullende configuratie te laden.
3. Stel eerst alleen de eigen bron in met het eigen lezersaccount. Start de ontvanger als gebruiker iot en controleer de abonnementsbevestiging.
4. Publiceer twintig eigen records. Bekijk ze via SQLite en download het serveroverzicht.
5. Wissel partnergegevens, openbare CA, vertrouwd bevestigde vingerafdruk en lezerswachtwoord uit. Houd beheerders- en eigenaarswachtwoorden privé.
6. Voeg op beide servers de partner toe. Controleer twee gereedmeldingen per ontvanger.
7. Maak en deel de broncontrolebestanden. Publiceer beide volledige beginsets.
8. Vergelijk op beide servers aantallen en inhoudsvingerafdrukken met beide broncontroles.
9. Herpubliceer twintig records en verstuur het opzettelijk ongeldige oefenobject. Controleer gelijke meetinhoud en toenemende fout-/dubbel-tellers.
10. Herstart ontvanger en broker, controleer opnieuw abonneren en behoud van gegevens. Maak een nieuw controleoverzicht en bewaar de inleverbestanden.

## Onderdelen en bevoegdheden

- `server/meetgegevens.py`: strikte berichtvalidatie, SQLite-schema, idempotente opslag en inhoudscontrole.
- `server/ontvangen.py`: onafhankelijke MQTT/TLS-clients met herverbinden en opnieuw abonneren. Eén schrijver verwerkt beide stromen in begrensde transacties.
- `server/ontvangst_instellen.py`: verborgen wachtwoordinvoer en atomische configuratieopslag als root:iot, mode 0640. Het clientwachtwoord moet beschikbaar blijven voor herverbinden en wordt daarom beschermd opgeslagen, niet gehasht alsof het een servercontrolewaarde is.
- `server/ontvangst_status.py`: consistente alleen-lezen momentopname zonder geheimen.
- `server/diensten/iot-ontvanger.service`: service onder iot, schrijfbereik beperkt tot /var/lib/iot, automatische herstart bij procesfout.
- `server/configuratie/ontvangst-capaciteit.conf`: maximaal 100 uitgaande onbevestigde berichten, 50.000 wachtende berichten en 64 MiB wachtende payloads per abonnee. De eerste bereikte wachtrijgrens geldt.
- `programmatuur/beginset_publiceren.py`: bewuste herpublicatie van de volledige aangeboden selectie in groepen van maximaal honderd, met gecontroleerde MQTT-5-PUBACK-redenen.

Mosquitto blijft na een serverherstart handmatig te starten. De ontvanger wordt wel ingeschakeld als service en herstelt zijn verbinding zodra de broker beschikbaar is. De ontvanger gebruikt op beide brokers alleen account lezer. Er worden geen topicrechten verruimd en geen nieuwe externe poorten geopend.

## Inhoudscontrole

De logische sleutel blijft `(bron, record_id)`. De database bewaart genormaliseerde zoekvelden en de volledige berichtinhoud zonder transportveld deelnemer. De eerste publicerende deelnemer staat afzonderlijk opgeslagen. Identieke broninhoud van verschillende publishers is daardoor dezelfde meting. Andere inhoud bij dezelfde sleutel verhoogt de conflictteller en overschrijft de bewaarde rij niet.

Het manifest bevat per bron het aantal en SHA-256 over op record_id gesorteerde regels `record_id:inhoud_sha256`. Zowel de publisher als de ontvanger gebruikt dezelfde canonieke JSON-serialisatie. Het manifest bewijst inhoudelijke overeenkomst met de aangewezen broncontrole, niet analytische bruikbaarheid van iedere bronrij.

MQTT-QoS bevestigt de publicatie naar de broker afzonderlijk van de verwerking bij een ontvanger. De ontvanger bevestigt zijn ontvangen berichten pas na de SQLite-transactie. De publishersessie blijft begrensd en gebruikt geen retained historie. Herpublicatie plus inhoudscontrole is de expliciete herstelroute.

## Uitgevoerde lokale verificatie

De controle gebruikt twee afzonderlijke brokers, certificaatautoriteiten, ontvangerprocessen en verzameldatabases in een tijdelijke Debian 13-container. Beide partijen ontvangen de volledige 80.028 gewichtsrecords en 146.649 voederrecords. De proefomgeving is begrensd op één CPU en 512 MiB RAM zonder extra swap. Dit is een lokale belastingsproef, geen DigitalOcean-VM of campusproef.

De test controleert eerst uitsluitend de eigen stroom, daarna de partnerstroom, vervolgens beide volledige beginsets. De inhoudsvingerafdrukken moeten op beide servers overeenkomen met de bronbestanden. De vijf gerichte validatietests controleren schemafouten, exacte identifiers, null versus nul, verkeerde topics, payloadgrootte, dubbelen en inhoudelijke conflicten.

De kernelproef voert de notebookcodecellen voor beide rollen uit met echte MQTT-verbindingen en serverdatabases. Tijdens de expliciete handmatige pauzes maakt de test de bijbehorende serveroverzichten en voert procesherstarts uit. Alleen wachtwoord- en bestandsuitwisseling worden automatisch ingevuld. De bewaarde voorbeeldoutput bevat fictieve testdeelnemers en localhost, geen echte credentials.

Een afzonderlijke inrichtingstest controleert de mode 0640 en eigenaar/groep root:iot van de instellingen, behoud bij hervatten, weigering van een verkeerde CA-vingerafdruk, toevoegen van de partner, de systemd-unitsyntaxis en de syntaxis van vijftien afzonderlijke Bash-cellen. De lokale ontvangprocessen worden rechtstreeks gestart in de container. Dit is geen uitvoering onder een volledige systemd-bootomgeving.

Een eerste belastingsproef met de standaardbrokerwachtrij van duizend berichten verloor records, ondanks geslaagde publisherbevestigingen. Daarom wordt in 05 de begrensde aanvullende buffer geïnstalleerd en wordt volledigheid altijd inhoudelijk gecontroleerd. Een grotere buffer is geen onbeperkte leveringsgarantie. Langdurige uitval of een structureel te trage ontvanger vereist herstel en herpublicatie.

## Nog op een echte oefenserver controleren

- Interactieve SSH-aanmelding, verborgen wachtwoordinvoer, partnercertificaatoverdracht en bestandsrechten met de eigen accounts.
- De daadwerkelijke systemd-service, reboot van de Droplet en het handmatig starten van Mosquitto na die reboot.
- Bereikbaarheid van beide brokers vanuit de echte server- en Codespaces-omgevingen, inclusief campusbediening.
- Opslagcapaciteit en belasting naast Nginx, de statusdienst en later de volledige API. De lokale test vervangt die complete VM-proef niet.
- Ontvangsttijd en volledigheid over het echte internet. Herhaal de inhoudscontrole na iedere herstelactie.

## Technische controles herhalen

Voer deze ontwikkeltests uitsluitend uit in een wegwerpcontainer met de image van `controles/server_03.Dockerfile`. Kopieer de repository naar een lokaal Linux-bestandssysteem binnen de container voordat je SQLite-testkopieën maakt. Een Windows-bindmount kan databaselezingen sterk vertragen.

```bash
/opt/iot/venv/bin/python controles/test_ontvangst_05.py
/opt/iot/venv/bin/python controles/controleer_keten_05.py
/opt/iot/venv/bin/python controles/controleer_inrichting_05.py
```

`controleer_keten_05.py` weigert buiten Docker te werken. `UITVOER_05` kan een map aanwijzen voor testverslagen en uitgevoerde notebooks. Er worden geen cloudresources aangemaakt en geen echte servers benaderd.
