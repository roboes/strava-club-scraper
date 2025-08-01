# Strava Club Scraper

[!["Buy Me A Coffee"](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://buymeacoffee.com/roboes)

## Description

This web-scraping tool aims to extract activities data from Strava Club to complete the lack of features of the standard Strava API. The main features are:

- Strava Club Activities scraper: imports "Recent Activity" for public or activities that the user has access to a dataset (requires a Strava account).
- Strava Club Leaderboard scraper: imports current and previous week leaderboard information (including athletes' `id`) to a dataset (requires a Strava account).
- Strava Club Members scraper: imports all members that joined a Strava Club (including athletes' `id`) to a dataset (requires a Strava account).
- Strava Club to Google Sheets importer: automatically retrieves data and updates Strava Club Activities, Leaderboard and/or Members dataset(s) into a Google Sheets (requires a Google API key).

> [!WARNING]
> Due to recent changes in Strava's login process, which now requires a 6-digit verification code sent via email, full automation of this project is no longer feasible.

## Strava API

This tool does not rely on the Strava API. Strava's API turned to be very limited in the recent years. For getting [List Club Activities](https://developers.strava.com/docs/reference/#api-Clubs-getClubActivitiesById), it returns only the following variables:
athlete variables: `resource_state`, `firstname` and `lastname` (first letter only);
activity variables: `name`, `distance`, `moving_time`, `elapsed_time`, `total_elevation_gain`, `type` and `workout_type`.

Given that Strava does not offer an `athlete id` variable, athletes with the same first name and first digit of the last name would not be distinguishable.

## Limitations

- Strava Club Activities scraper: the main drawback/limitation of this tool is that Strava's dashboard activity feed is very limited in the number of activities shown. Scrolling until the bottom of the page is not endless; after some scrolls the warning _"No more recent activity available. To see your full activity history, visit your Profile or Training Calendar."_ is shown.
  Strava has the `num_entries` URL query string (e.g. <https://www.strava.com/dashboard?club_id=319098&feed_type=club&num_entries=1000>), but still this string does not necessarily load the requested number of activity entries to the feed.
  This tool also requires that the athletes' activities to be scraped are either public or that the account that is scraping the club activities data has access to the activities to be scraped (by either following the athlete or by owning the activity).

- Strava Club Leaderboard scraper: the club leaderboards include only data for current and previous week; no historical data is provided by Strava. Additionally, club leaderboards display only the weekly top 100 members ([Source](https://support.strava.com/hc/en-us/articles/216918347-Clubs-on-Strava#:~:text=On%20the%20Strava%20website%2C%20club%20leaderboards%20will%20display%20the%20weekly%20top%20100%20members.%20On%20the%20mobile%20app%2C%20the%20top%2010%20members%20will%20appear%20on%20the%20weekly%20leaderboard.)).

To avoid these limitations, this tool offers an integration to Google Sheets, updating/incrementing specified scraped Strava Club(s) data for activities/leaderboard/members, keeping previously scraped data that cannot be accessed anymore in Strava Club.

## Usage

### Use case

Strava allows users to create a [Group Challenge](https://support.strava.com/hc/en-us/articles/360061360791-Group-Challenges), which is limited to up to 25 participants. To circumvent this limitation, one possible use case is to create one or multiple Strava Clubs (e.g. Cycling, Multisport, Run/Walk/Hike), adapt this script to update/increment an existing Google Sheets sheet with the club(s) activities, leaderboard and members information data. The script can be set up to run automatically on a scheduled basis on cloud platform services such as [GitHub Actions](https://github.com/features/actions) (see [GitHub Actions Workflow .yaml template](https://github.com/roboes/tools/blob/main/technology/git/github-actions-workflow/github-actions-workflow.yaml)) and [Railway](https://railway.app) (see [Dockerfile template](https://github.com/roboes/tools/blob/main/technology/docker/Dockerfile)). To connect the script to a Google Sheets file, a [Google Sheets API](https://console.cloud.google.com/apis/library/sheets.googleapis.com) .json key is required and the file needs to be shared with a [Service Account email address](https://cloud.google.com/iam/docs/service-account-overview). The Google Sheets can then be connected to a dashboard tool (e.g. Google Data Studio, Microsoft PowerBI).

### Strava settings

This tool assumes that [Strava's Display Preferences](https://www.strava.com/settings/display) are set to:

- `Units & Measurements` = "Kilometers and Kilograms"
- `Temperature` = "Celsius"
- `Feed Ordering` = "Latest Activities" ([chronological feed](https://support.strava.com/hc/en-us/articles/115001183630-Feed-Ordering))

And that your Strava display language is `English (US)`. To change the language, log in to [Strava](https://www.strava.com) and on the bottom right-hand corner of any page, select `English (US)` from the drop-down menu (more on this [here](https://support.strava.com/hc/en-us/articles/216917337-Changing-your-language-in-the-Strava-App)).

### Installation

```.ps1
python -m pip install "git+https://github.com/roboes/strava-club-scraper.git@main"
```

### Functions

#### `strava_club_activities`

```.py
strava_club_activities(club_ids, filter_activities_type, filter_date_min, filter_date_max, timezone='UTC')
```

##### Description

- Scraps and imports activities belonging to one or multiple Strava Club(s) (public activities or activities that the account that is scraping the data has access to) to a dataset.

##### Parameters

- `club_ids`: _str list_. List of Strava Club ids in which the tool should scrap data from (e.g. `club_ids=['445017', '789955', '1045852']`).
- `filter_activities_type`: _str list_, default: _None_. List of activities type filter (e.g. `filter_activities_type=['E-Bike Ride', 'Hike', 'Ride', 'Run', 'Walk']`).
- `filter_date_min`: _str_. Start date filter (e.g. `filter_date_min='2023-06-05'`).
- `filter_date_max`: _str_. End date filter (e.g. `filter_date_max='2023-07-30'`).
- `timezone`: _str or timezone object_, default: _'UTC'_.

<br>

#### `strava_club_members`

```.py
strava_club_members(club_ids, club_members_teams=None, timezone='UTC')
```

##### Description

- Scraps and imports members of one or multiple Strava Club(s) to a dataset.

##### Parameters

- `club_ids`: _str list_. List of Strava Club ids in which the tool should scrap data from (e.g. `club_ids=['445017', '789955', '1045852']`).
- `club_members_teams`: _dict_, default: _None_. Option to add `athlete_id` to one or multiple teams (stored in the `athlete_team` column). `athlete_id` assigned to multiple teams will have its unique teams assignment comma separated.
- `timezone`: _str or timezone object_, default: _'UTC'_.

Example of `club_members_teams`:

```.py
club_members_teams={
    'Team A': ['1234, 5678'],
    'Team B': ['1234, 12345'],
}
```

<br>

#### `strava_club_leaderboard`

```.py
strava_club_leaderboard(club_ids, filter_date_min, filter_date_max, timezone='UTC')
```

##### Description

- Scraps and imports leaderboard of one or multiple Strava Club(s) to a dataset.

##### Parameters

- `club_ids`: _str list_. List of Strava Club ids in which the tool should scrap data from (e.g. `club_ids=['445017', '789955', '1045852']`).
- `filter_date_min`: _str_. Start date filter (e.g. `filter_date_min='2023-06-05'`).
- `filter_date_max`: _str_. End date filter (e.g. `filter_date_max='2023-07-30'`).
- `timezone`: _str or timezone object_, default: _'UTC'_.

<br>

#### `strava_club_to_google_sheets`

```.py
strava_club_to_google_sheets(df, sheet_id, sheet_name)
```

##### Description

- Update/increment a Google Sheet sheet given an inputted dataset.

##### Parameters

- `df`: _DataFrame_. Input dataset to be updated/incremented in a specified Google Sheets sheet.
- `sheet_id`: _str_. Google Sheets file id.
- `sheet_name`: _str_. Google Sheets sheet/tab where the data should be updated/incremented.

<br>

#### `execution_time_to_google_sheets`

```.py
execution_time_to_google_sheets(sheet_id, sheet_name, timezone='UTC')
```

##### Description

- Update a Google Sheet sheet given the current time that the code was executed.

##### Parameters

- `sheet_id`: _str_. Google Sheets file id.
- `sheet_name`: _str_. Google Sheets sheet/tab where the data should be updated/incremented.
- `timezone`: _str or timezone object_, default: _'UTC'_.

<br>

#### `strava_export_gpx`

```.py
strava_export_activities(activities_id, file_type)
```

##### Description

- Export a list of _activity_id_ to a GPS file.

##### Parameters

- `activities_id`: _int list_ or _str list_. List of activity_id to be exported (e.g. `activities_id=[696657036, 696657037]`).
- `file_type`: _str_, default: _'.gpx'_. Activity export format. Note that the _'.gpx'_ format uses Strava's built-in feature to export the activities, and _'.tcx'_ uses [Sauce for Strava Chrome Extension](https://chrome.google.com/webstore/detail/sauce-for-strava/eigiefcapdcdmncdghkeahgfmnobigha) (which needs to be installed on Selenium's WebDriver to work). Strava's built-in export .gpx feature includes only trackpoints (with latitude and longitude); it is possible to manipulate those .gpx exports by converting them to other GPS file types (e.g. .tcx) and add faketimes using [GPSBabel](https://www.gpsbabel.org) (see [gps_tools.sh](https://github.com/roboes/tools/blob/main/sports/gps_tools.sh)).

<br>

#### `selenium_webdriver_quit`

```.py
selenium_webdriver_quit()
```

##### Description

- Terminates the WebDriver session.

##### Parameters

- None.

### Code Workflow Example

```.py
# Import packages
import configparser
import os

# import numpy as np
import pandas as pd
from strava_club_scraper.strava_club_scraper import strava_club_members, strava_club_to_google_sheets, strava_club_leaderboard, strava_club_activities, execution_time_to_google_sheets


# Settings

## Config
# Required: config['GENERAL']['DATE_MIN'], config['GENERAL']['DATE_MAX'], config['GENERAL']['TIMEZONE'], config['STRAVA']['LOGIN'], config['STRAVA']['PASSWORD'], config['STRAVA']['CLUB_IDS']
# Optional: config['GENERAL']['ACTIVITIES_TYPE'], config['STRAVA']['CLUB_MEMBERS_TEAMS'], config['GOOGLE_DOCS']['SHEET_ID']
config = configparser.ConfigParser()
config.read(filenames=os.path.join(os.path.expanduser('~'), 'Documents', 'Documents', 'Projects', 'strava-club-scraper', 'settings', 'config.ini'), encoding='utf-8')

## Google API
google_api_key = os.path.join(os.path.expanduser('~'), 'Documents', 'Documents', 'Projects', 'strava-club-scraper', 'settings', 'keys.json')
if os.path.exists(google_api_key) is False:
    google_api_key = None

## Club members teams
if 'CLUB_MEMBERS_TEAMS' in config['STRAVA']:
    club_members_teams = pd.DataFrame.from_dict(data=dict(item.split(sep=': ') for item in config['STRAVA']['CLUB_MEMBERS_TEAMS'].split(sep='; ')), orient='index', dtype='str', columns=['athlete_id'])

else:
    club_members_teams = None


# Club members

## Get data (via web-scraping)
club_members_df = strava_club_members(
    strava_login=config['STRAVA']['LOGIN'],
    strava_password=config['STRAVA']['PASSWORD'],
    club_ids=config['STRAVA']['CLUB_IDS'].split(sep=', '),
    club_members_teams=club_members_teams,
    timezone=config['GENERAL']['TIMEZONE'],
)

## Test
print(
    club_members_df.filter(items=['athlete_team', 'athlete_name', 'athlete_id'])
    .query(expr='athlete_team.notna()')
    .drop_duplicates(subset=None, keep='first', ignore_index=True)
    .assign(athlete_team=lambda row: row['athlete_team'].str.split(pat=', ', expand=False))
    .explode(column=['athlete_team'])
    .sort_values(by=['athlete_team', 'athlete_name'], ignore_index=True),
)

## Update Google Sheets sheet
if google_api_key is not None:
    club_members_df = strava_club_to_google_sheets(df=club_members_df, club_members_df=club_members_df, sheet_id=config['GOOGLE_DOCS']['SHEET_ID'], sheet_name='Members')


# Club leaderboard

## Get data (via web-scraping)
club_leaderboard_df = strava_club_leaderboard(
    strava_login=config['STRAVA']['LOGIN'],
    strava_password=config['STRAVA']['PASSWORD'],
    club_ids=config['STRAVA']['CLUB_IDS'].split(sep=', '),
    filter_date_min=config['GENERAL']['DATE_MIN'],
    filter_date_max=config['GENERAL']['DATE_MAX'],
    timezone=config['GENERAL']['TIMEZONE'],
)

## Update Google Sheets sheet
if google_api_key is not None:
    strava_club_to_google_sheets(df=club_leaderboard_df, club_members_df=club_members_df, sheet_id=config['GOOGLE_DOCS']['SHEET_ID'], sheet_name='Leaderboard')


# Club activities
if config['GENERAL'].getboolean('SCRAP_CLUB_ACTIVITIES') is True:
    # Get data (via web-scraping)
    club_activities_df = strava_club_activities(
        strava_login=config['STRAVA']['LOGIN'],
        strava_password=config['STRAVA']['PASSWORD'],
        club_ids=config['STRAVA']['CLUB_IDS'].split(sep=', '),
        filter_activities_type=None,
        filter_date_min=config['GENERAL']['DATE_MIN'],
        filter_date_max=config['GENERAL']['DATE_MAX'],
        timezone=config['GENERAL']['TIMEZONE'],
    )

    # Update Google Sheets sheet
    if google_api_key is not None:
        strava_club_to_google_sheets(df=club_activities_df, club_members_df=club_members_df, sheet_id=config['GOOGLE_DOCS']['SHEET_ID'], sheet_name='Activities')

## Save as .csv
# club_activities_df.to_csv(path_or_buf='club_activities.csv', sep=',', na_rep='', header=True, index=False, index_label=None, encoding='utf-8')

# # Export club activities to .gpx files
# club_activities_sample_df = (read_google_sheets(sheet_id=config['GOOGLE_DOCS']['SHEET_ID'], sheet_name='Activities')
# .drop(columns=['club_id'], axis=1, errors='ignore')
# .drop_duplicates(subset=None, keep='first', ignore_index=True)
# .query(expr='activity_type.isin(["Ride", "E-Bike Ride", "Mountain Bike Ride", "E-Mountain Bike Ride", "Race", "Run", "Trail Run", "Walk", "Hike"])')
# .assign(activity_type=lambda row: np.where((row['activity_type'] == 'Race') & (row['pace'].notna()), 'Run', (np.where((row['activity_type'] == 'Race') & (row['pace'].isna()), 'Ride', row['activity_type']))))
# .assign(activity_type=lambda row: np.where(row['activity_type'].isin(['Ride', 'E-Bike Ride', 'Mountain Bike Ride', 'E-Mountain Bike Ride']), 'Cycling', (np.where(row['activity_type'].isin(['Run', 'Trail Run', 'Walk', 'Hike']), 'Run/Walk/Hike', row['activity_type']))))
# .sort_values(by=['activity_type', 'activity_date', 'activity_id'], ignore_index=True)
# )
# strava_export_activities(strava_login=config['STRAVA']['LOGIN'], strava_password=config['STRAVA']['PASSWORD'], activities_id=club_activities_sample_df.query(expr='activity_type.isin(["Run/Walk/Hike"])')['activity_id'], file_type='.gpx')

# # Strava Club Leaderboard manual import - For members that joined the challenge later, manually scrap inividual activities and group them by week
# club_leaderboard_manual_df = strava_club_leaderboard_manual(club_activities_df=club_activities_df, club_id=None, club_name=None, club_activity_type=None, club_location=None, filter_activities_type=config['GENERAL']['ACTIVITIES_TYPE'].split(sep=', '))


# Store execution time in Google Sheets

## Update Google Sheets sheet
if google_api_key is not None:
    execution_time_to_google_sheets(sheet_id=config['GOOGLE_DOCS']['SHEET_ID'], sheet_name='Execution Time', timezone=config['GENERAL']['TIMEZONE'])


## Quit WebDriver
if 'driver' in vars():
    driver.quit()
```

## Legal

Please note that the use of this code/tool may not comply with [Strava's Terms of Service](https://www.strava.com/legal/terms) (especially the _"Distributing, or disclosing any part of the Services in any medium, including without limitation by any automated or non-automated “scraping”"_ term) and [Strava's API Agreement](https://www.strava.com/legal/api) (especially the _"You may not use web scraping, web harvesting, or web data extraction methods to extract data from the Strava Platform"_ term). Use this tool at your own risk.

## See also

[Strava Club Tracker](https://github.com/picasticks/StravaClubTracker): Tool that generates a progress tracker/dashboard for Club activities (relies on Strava's API) (HTML, PHP).

[StravaClubActivities](https://github.com/stephenwong/strava_club_activities): Tool that downloads Club activities and generates a .csv for processing virtual race events (relies on Strava's API) (Ruby).
