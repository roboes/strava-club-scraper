# Helsedirektoratet Strava scraper

Script og actions for å hente resultater fra Helsedirektoratet sin stravaklubb og publisere dette som resultatlister i forbindelse med sykle til jobben aksjonen.

## Arkitektur

![arkitektur](plantuml-source/arkitektur.png)

## Komponenter

### Strava club scraper

* Scraper startes av et [action script](https://github.com/hdir/strava-club/blob/main/.github/workflows/hdir-scrape.yaml), planen er at dette skal kjøre omtrent en gang om dagen, men akkurat nå startes dette manuelt.  
* Scraper applikasjonen er en fork av [strava club scraper](https://github.com/roboes/strava-club-scraper)
  * Forutsetter at det eksisterer en bruker som er medlem i Helsedirektoratet sin stravaklubb, passord og brukernavn ligger som hemmeligheter i repoet.  
  * Scraper koden er modifisert slik at output er csv filer istedenfor google sheets.
  * Scraper koden er modifisert slik at python scriptet kjører feilfritt i en Github Action.
  * Scraper koden er modifisert slik at brukernavn og passord ligger som hemmeligheter i repoet istedenfor som klartekst i config.ini.  

### Databehandler

Tar de siste CSV filene fra scraper og produserer to resultatlister som json.
**Trigger** Nye eller oppdaterte CSV filer fra scraper. Kan muligens startes direkte fra samme script som scraper.

* En akkumulert resultatliste for en bestemt periode over en predefinert periode.
* En resultatliste for den siste uken.

### Presentatør

Tar Json filer fra databehandler og presenterer resultatlistene på en pen måte som html filer.
**Trigger** Databehandleren startes av et script.

Resultatet legges på gh-pages branch for visning på github.io.
