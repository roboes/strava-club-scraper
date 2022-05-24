## Description

This web-scraping tool aims to extract public activities data from Strava Clubs to complete the lack of features of the standard API, and includes:
- Strava Club Activities scraper: imports "Recent Activity" for public or activities that the user has access to a dataframe (requires a Strava account).
- Strava Club Leaderboard scraper: imports current week and previous leaderboard information, including athletes' ```id```, to a dataframe (requires a Strava account).
- Strava Club Members scraper: imports all members that joined a Strava Club, including athletes' ```id```, to a dataframe (requires a Strava account).
- Strava Club to Google Sheets importer: automatically retrieves data and updates Strava Club Activities, Leaderboard and/or Members dataframe(s) into a Google Sheets (requires a Google API key).

### Strava API

This project does not rely on the Strava API. Strava's API turned to be very limited in the recent years. For getting [List Club Activities](https://developers.strava.com/docs/reference/#api-Clubs-getClubActivitiesById), it returns only the following variables:  
athlete variables: ```resource_state```, ```firstname``` and ```lastname``` (first letter only);  
activity variables: ```name```, ```distance```, ```moving_time```, ```elapsed_time```, ```total_elevation_gain```, ```type``` and ```workout_type```.

Given that Strava does not offer an ```athlete id``` variable, athletes with the same first name and first digit of the last name would not be distinguishable.


### Limitations

- Strava Club Activities scraper: the main drawback/limitation of this tool is that Strava's dashboard activity feed is very limited in the number of activities shown. Scrolling until the bottom of the page is not endless; after some scrolls the warning *"No more activity in the last 60 days. To see your full activity history, visit your Profile or Training Calendar."* is shown.
This warning is not necessarily shown after 60 days of previous activities are loaded to the dashboard activity feed.
Strava has the ```num_entries``` URL query string (e.g. https://www.strava.com/dashboard?club_id=319098&feed_type=club&num_entries=1000), but still this variable does not load older activities to the feed.  
This tool also requires that the athletes' activities to be scraped are either public or that the account that is scraping the club activities data has access to the activities to be scraped (by either following the athlete or by owning the activity).

- Strava Club Leaderboard: the club leaderboards include only data for current and previous week; no historical data is provided by Strava.

To avoid these limitations, this tool offers an integration to Google Sheets, updating club data for activities/leaderboard/members, overwriting current and previous week stats and incrementing/keeping the previous scraped data that cannot be accessed anymore in Strava Club.

## Usage

### Python dependencies

<code>python -m pip install python-dateutil google-api-python-client google-auth lxml numpy pandas pyjanitor selenium webdriver-manager</code>

### Strava Settings

This tool assumes that [Strava's Display Preferences](https://www.strava.com/settings/display) are set to:  
```Units & Measurements``` = "Kilometers and Kilograms"  
```Temperature``` = "Celsius"  
```Feed Ordering``` = "Latest Activities" ([chronological feed](https://support.strava.com/hc/en-us/articles/115001183630-Feed-Ordering))  

And that your Strava display language is ```English (US)```. To change the language, log in to [Strava](https://www.strava.com) and on the bottom right-hand corner of any page, select ```English (US)``` from the drop-down menu (more on this [here](https://support.strava.com/hc/en-us/articles/216917337-Changing-your-language-in-the-Strava-App)).


## Legal

Please note that the use of this code/tool may not comply with [Strava's Terms of Service](https://www.strava.com/legal/terms) (especially the *"Distributing, or disclosing any part of the Services in any medium, including without limitation by any automated or non-automated “scraping”"* conduct term) and [Strava's API Agreement](https://www.strava.com/legal/api) (especially the *"You cannot use web scraping, web harvesting, or web data extraction methods to extract data from the Strava Platform"* term). Use it at your own risk.

## See also

[Strava Club Tracker](https://github.com/picasticks/StravaClubTracker): Tool that generates a progress tracker/dashboard for Club activities (relies on Strava's API) (HTML, PHP).

[StravaClubActivities](https://github.com/stephenwong/strava_club_activities): Tool that downloads Club activities and generates a .csv for processing virtual race events (relies on Strava's API) (Ruby).
