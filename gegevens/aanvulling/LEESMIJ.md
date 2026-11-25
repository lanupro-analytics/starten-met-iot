# Aanvullende metingen voor notebook 08

De bestanden bevatten vijftien kalenderdagen, van 21 september tot en met 5 oktober 2023. De eerste vier weken blijven in `gegevens/origineel/`.

| Bestand | week_5 | resterende_dagen | Totaal |
|---|---:|---:|---:|
| asserva_aanvullende_metingen.xlsx | 23.546 | 28.648 | 52.194 |
| schauer_aanvullende_metingen.xlsx | 38.876 | 48.076 | 86.952 |

Alleen deze twee meetbladen worden geïmporteerd. `toelichting` bevat leesinstructies. ROW_ID en andere tekstkolommen blijven tekst. De werkboeken behouden de bronkolommen, meetwaarden en kwaliteitsvlaggen. TREAT is bewust leeggelaten om geen behandelingssleutel te geven. Dit veld wordt niet gebruikt voor groei, voederopname of voederconversie.

De bronbestandsnamen en SHA-256, kolomtypen, aantallen en werkboekhashes staan in `maakcontrole.json`. De oorspronkelijke CSV-bestanden zijn ongewijzigd. De werkboeken zijn na export volledig teruggelezen en vergeleken met de bedoelde bronselectie, inclusief alle cijfers van de identificaties.

Gebruik de vrijgegeven bestanden zonder opnieuw op te slaan in Excel. De import controleert de bestandshash. Voer de import uitsluitend uit in de eigen werkdatabase volgens notebook 08. De analyse ontvangt de metingen vervolgens via MQTT, serveropslag en API.
