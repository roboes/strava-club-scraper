## Helsedirektoratet Strava scraper

Script og actions for å hente resultater fra Helsedirektoratet sin stravaklubb og publisere dette som resultatlister i forbindelse med sykle til jobben aksjonen.

### Arkitektur

![arkitektur](plantuml-source/arkitektur.png)

### Komponenter

* Scraper'en er en fork av [strava club scraper](https://github.com/roboes/strava-club-scraper)
  * Forutsetter at det eksisterer en bruker som er medlem i Helsedirektoratet sin stravaklubb, passord og brukernavn ligger som hemmeligheter i repoet.