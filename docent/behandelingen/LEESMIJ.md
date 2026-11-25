# Behandelingen: informatie voor de docent

`behandelingssleutel.csv` bevat de door de docent aangeleverde werkelijke toewijzing. HRE18 en LRE18 hebben elk drie hokken, HRE10 en LRE10 elk twee. De volledige map `docent/` wordt bij het maken van de studentenbranch weggelaten.

## Interpretatie van de voorbeeldoplossing

Notebook 08 gebruikt uitsluitend FILTER = '0' en leest deze sleutel niet. De grensgewichten zijn gemiddelden van de vijf dichtstbijzijnde individuele metingen. De voederopname is de som van alle behouden bezoeken tussen de grenzen. In elk van de fasen dag 1–10, 10–18 en 18–27 tellen 99 dieren mee.

De voorbeeldhypothesen zijn opnieuw vergeleken met de sleutel: 8 van de tien labels kloppen. De code is niet aangepast om de sleutel passend te maken. De uitkomsten blijven beschrijvend en zijn geen onafhankelijke validatie. De vroeg schakelende groepen behouden een lage zekerheid. Bekijk bij alle groepen ook de tijdafstanden van de gekozen gewichten en het aantal dagen met voederrecords.

De eerdere gevoeligheidsverkenningen betroffen de oude interpolatiemethode. De actuele tabellen, grafieken en hypothesen worden opnieuw gemaakt door de notebooks. Er worden geen losse verkenningsbestanden voor uitvoering gebruikt.

## Uitvoering en vrijgave

De [rekenmethode](../../documentatie/rekenmethode_07.md) beschrijft de filtering en berekening. De controlehandleidingen voor [07](../../documentatie/notebook_07_controleren.md) en [08](../../documentatie/notebook_08_controleren.md) beschrijven uitvoering, controles en herhaling. Oude beginsituaties zonder de verplichte filtering mogen niet met de huidige methode worden gecombineerd.

De oorspronkelijke bronkolom `TREAT` bevat nog codes A–D. De analyse selecteert deze niet. Voor een volledig blinde studentenpublicatie moeten die bestaande codes apart worden geneutraliseerd, inclusief actualisering van broncontrolesommen. Alleen het weglaten van de docentmap maakt de bronbestanden niet blind.
