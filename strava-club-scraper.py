## Strava Club Scraper
# Last update: 2023-06-14


###############
# Initial Setup
###############

# Erase all declared global variables
globals().clear()


# Import packages
from datetime import timedelta
import glob
import os
import re
import sys
import time

from dateutil import parser, relativedelta
from geopy.extra.rate_limiter import RateLimiter
from geopy.geocoders import Nominatim
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from janitor import clean_names
# import lxml
import lxml.html as lh
import numpy as np
import pandas as pd
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager


# Set working directory
if sys.platform == 'win32' or sys.platform == 'darwin':
    os.chdir(path=os.path.join(os.path.expanduser('~'), 'Downloads'))


# Settings

# Timezone
timezone='CET'

# Strava login
strava_email='test@email.com'
strava_password='Password12345'

# Strava Clubs
club_ids=['445017', # E-Bike Ride, Ride
    '789955', # Multisport
    '1045852'] # Run, Walk, Hike
# filter_activities_type=['Ride', 'E-Bike Ride', 'Mountain Bike Ride', 'E-Mountain Bike Ride', 'Indoor Cycling', 'Virtual Ride', 'Run', 'Trail Run', 'Walk', 'Hike']
filter_date_min='2023-06-05'
filter_date_max='2023-07-30'
club_members_teams={
    'Team A': ['1234, 5678'],
    'Team B': ['12345'],
}

# Google API
google_api_key=os.path.join(os.getcwd(), 'files', 'keys.json')

# Google Sheets
sheet_id='GOOGLE_SHEET_ID'




###########
# Functions
###########

# Convert list to dictionary
def convert_list_to_dictionary(*, list):

    list = iter(list)
    dictionary = dict(zip(list, list))


    # Return objects
    return dictionary



# Selenium webdriver
def selenium_webdriver():

    # Webdriver options
    chrome_options = webdriver.ChromeOptions()
    chrome_options.page_load_strategy = 'normal'


    # Webdriver download settings
    chrome_options.add_experimental_option('prefs', {
        # 'download.default_directory': os.path.join(os.path.expanduser('~'), 'Downloads'),
        'download.prompt_for_download': False,
        'profile.default_content_setting_values.automatic_downloads': 1,
    })


    # Webdriver
    if sys.platform == 'linux' or sys.platform == 'linux2':
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('window-size=1400,900')
        chrome_options.add_argument('--start-maximized')

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)


    # Return objects
    return driver



# Selenium webdriver quit
def selenium_webdriver_quit():

        # Import or create global variables
        global driver


        # Driver quit
        driver.quit()


        # Delete objects
        del driver



# Strava login
def strava_login():

    # Import or create global variables
    global driver


    # Load Selenium webdriver
    if 'driver' in vars() or 'driver' in globals():
        if driver.service.is_connectable() == True:
            pass

    else:
        driver = selenium_webdriver()


        # Open website
        driver.get('https://www.strava.com/login')
        time.sleep(2)


        # Reject cookies
        try:
            driver.find_element(by=By.XPATH, value='.//button[@class="btn-deny-cookie-banner"]').click()

        except NoSuchElementException:
            pass


        # Login
        driver.find_element(by=By.ID, value='email').send_keys(strava_email)
        driver.find_element(by=By.ID, value='password').send_keys(strava_password)
        time.sleep(2)

        driver.find_element(by=By.XPATH, value='.//*[@type="submit"]').submit()


        # Return objects
        return driver



# Strava Club activities - scrap individual activities from members of a Strava Club
def strava_club_activities(*, club_ids, filter_activities_type, filter_date_min, filter_date_max, timezone='UTC'):

    """
    elapsed_time, moving_time: seconds
    distance, elevation_gain: meters
    max_speed, average_speed: meters/second
    heart_rate: bpm
    power: W
    temperature: degree Celsius
    """

    # Import or create global variables
    global club_activities
    global driver


    # Settings and variables
    filter_date_min = parser.parse(filter_date_min)
    filter_date_max = parser.parse(filter_date_max)


    # Strava login
    strava_login()


    data = []

    for club_id in club_ids:

        # Open Strava Club activities feed page
        driver.get('https://www.strava.com/dashboard?club_id=' + club_id + '&feed_type=club&num_entries=100')
        time.sleep(3)


        # Scroll to the end of the webpage
        while True:

            try:
                driver.find_element(by=By.XPATH, value='//div[text()="No more recent activity available."]')
                break

            except NoSuchElementException:

                activities = driver.find_elements(by=By.XPATH, value='//div[@data-testid="activity_entry_container"]')
                activity_date = activities[-1].find_element(by=By.XPATH, value='.//..//..//..//..//..//time').text
                activity_date = re.sub(pattern=r'^(Today at )(.*)$', repl=str(pd.Timestamp.now(tz=timezone).date()) + r' \2', string=activity_date)
                activity_date = re.sub(pattern=r'^(Yesterday at )(.*)$', repl=str((pd.Timestamp.now(tz=timezone).date() - timedelta(days=1))) + r' \2', string=activity_date)
                activity_date = parser.parse(activity_date)

                if activity_date >= filter_date_min:
                    driver.execute_script(script='window.scrollTo(0, document.body.scrollHeight);')
                    time.sleep(6)

                else:
                    break


        # Get all displayed activities_id, filtering filter_date_min and activity_type (note: activity_type filter does not work for group activities - thus all group activities are kept and verified on a case-by-case base)
        activities_id = []

        activities = driver.find_elements(by=By.XPATH, value='//div[@data-testid="web-feed-entry"]')

        for activity in activities:

            activity_date = activity.find_element(by=By.XPATH, value='.//time[@data-testid="date_at_time"]').text
            activity_date = re.sub(pattern=r'^(Today at )(.*)$', repl=str(pd.Timestamp.now(tz=timezone).date()) + r' \2', string=activity_date)
            activity_date = re.sub(pattern=r'^(Yesterday at )(.*)$', repl=str((pd.Timestamp.now(tz=timezone).date() - timedelta(days=1))) + r' \2', string=activity_date)
            activity_date = parser.parse(activity_date)

            if filter_date_min <= activity_date < (filter_date_max + timedelta(days=1)):

                activity_ids = activity.find_elements(by=By.XPATH, value='.//div[@data-testid="activity_entry_container"]//h3//a')

                for activity_id in activity_ids:

                    activity_id = activity_id.get_attribute('href')
                    activity_id = re.sub(pattern=r'^.*/activities/(.*)$', repl=r'\1', string=activity_id)
                    activity_id = re.sub(pattern=r'^([0-9]+)(\?|/|#).*$', repl=r'\1', string=activity_id)
                    activities_id.append(activity_id)


        activities_id = list(set(activities_id))
        activities_id = sorted(activities_id)


        for activity in activities_id:

            d = {}

            driver.get('https://www.strava.com/activities/' + activity)

            try:
                driver.find_element(by=By.XPATH, value='//pre[text()="Too Many Requests"]')
                break

            except NoSuchElementException:

                # club_id
                d['club_id'] = club_id

                # activity_id
                d['activity_id'] = activity


                # athlete_name, activity_type
                d['athlete_name'], d['activity_type'] = driver.find_element(by=By.XPATH, value='.//span[@class="title"]').text.split(sep=' – ')[0:2]

                try:
                    d['commute'] = driver.find_element(by=By.XPATH, value='.//span[@class="title"]').text.split(sep=' – ')[2]
                    d['commute'] = re.sub(pattern=r'^Commute$', repl=r'True', string=d['commute'])
                    d['commute'] = bool(d['commute'])

                except:
                    pass


                # activity_date
                d['activity_date'] = driver.find_element(by=By.XPATH, value='.//div[@class="details-container"]//time').text
                d['activity_date'] = re.sub(pattern=r'^(.*) on (.*)$', repl=r'\2 \1', string=d['activity_date'])
                d['activity_date'] = parser.parse(d['activity_date'])


                # Activity stats

                # Click on "Show More" button (if available)
                try:
                    driver.find_element(by=By.XPATH, value='.//button[@class="minimal compact"][text()="Show More"]').click()

                except:
                    pass

                # athlete_id
                d['athlete_id'] = driver.find_element(by=By.XPATH, value='.//div[@class="details-container"]//a').get_attribute('href')
                d['athlete_id'] = re.sub(pattern=r'^.*/athletes/(.*)$', repl=r'\1', string=d['athlete_id'])

                # activity_name
                d['activity_name'] = driver.find_element(by=By.XPATH, value='.//div[@class="details-container"]//h1').text

                # activity_description
                try:
                    d['activity_description'] = driver.find_element(by=By.XPATH, value='.//div[@class="details-container"]//div[@class="content"]').text

                except:
                    pass

                # activity_location
                try:
                    d['activity_location'] = driver.find_element(by=By.XPATH, value='.//div[@class="details-container"]//span[@class="location"]').text

                except:
                    pass

                # Inline stats
                inline_stats = driver.find_element(by=By.XPATH, value='.//ul[@class="inline-stats section"]').text.split(sep='\n')
                inline_stats = convert_list_to_dictionary(list=inline_stats)
                inline_stats = {value: name for name, value in inline_stats.items()}

                for item, value in inline_stats.items():
                    d[item] = value

                    # distance
                    try:
                        d['Distance'] = re.sub(pattern=r',', repl=r'', string=d['Distance'])
                        d['Distance'] = re.sub(pattern=r'km$', repl=r'', string=d['Distance'])
                        d['Distance'] = re.sub(pattern=r'm$', repl=r'', string=d['Distance']) # For activity_type = 'Swim'
                        d['Distance'] = float(d['Distance'])
                        d['Distance'] = d['Distance']*1000

                    except:
                        pass

                    # elevation_gain
                    try:
                        d['Elevation'] = re.sub(pattern=r',', repl=r'', string=d['Elevation'])
                        d['Elevation'] = re.sub(pattern=r'm$', repl=r'', string=d['Elevation'])

                    except:
                        pass

                    # moving_time
                    try:
                        if len(d['Moving Time'].split(sep=':')) == 1:
                            d['Moving Time'] = re.sub(pattern=r'^([0-9]+)s$', repl=r'00:00:\1', string=d['Moving Time'])

                        if len(d['Moving Time'].split(sep=':')) == 2:
                            d['Moving Time'] = re.sub(pattern=r'^(.*)$', repl=r'00:\1', string=d['Moving Time'])

                    except:
                        pass

                    # pace
                    """
                    try:
                        d['Pace'] = re.sub(pattern=r' /km', repl=r'', string=d['Pace'])

                        if len(d['Pace'].split(sep=':')) == 1:

                            if len(d['Pace'].split(sep=':')[0]) == 1:
                                d['Pace'] = re.sub(pattern=r'^([0-9]+)$', repl=r'00:00:0\1', string=d['Pace'])

                            elif len(d['Pace'].split(sep=':')[0]) == 2:
                                d['Pace'] = re.sub(pattern=r'^([0-9]+)$', repl=r'00:00:\1', string=d['Pace'])


                        if len(d['Pace'].split(sep=':')) == 2:

                            if len(d['Pace'].split(sep=':')[0]) == 1:
                                d['Pace'] = re.sub(pattern=r'^(.*)$', repl=r'00:0\1', string=d['Pace'])

                            elif len(d['Pace'].split(sep=':')[0]) == 2:
                                d['Pace'] = re.sub(pattern=r'^(.*)$', repl=r'00:\1', string=d['Pace'])

                    except:
                        pass
                    """


                # More stats
                try:
                    more_stats = driver.find_element(by=By.XPATH, value='.//div[@class="section more-stats"]').text
                    more_stats = re.sub(pattern=r'Show Less\n|Avg Max\n', repl=r'', string=more_stats)

                    # Speed
                    more_stats = re.sub(pattern=r'^Speed ', repl=r'Average Speed\n', string=more_stats)
                    more_stats = re.sub(pattern=r'(km/h*?) ', repl=r'\1\nMax Speed\n', string=more_stats)

                    # Heart Rate
                    more_stats = re.sub(pattern=r'Heart Rate ', repl=r'Average Heart Rate\n', string=more_stats)
                    more_stats = re.sub(pattern=r'(Heart Rate\n[0-9]{2,} bpm) ', repl=r'\1\nMax Heart Rate\n', string=more_stats)

                    # Cadence
                    more_stats = re.sub(pattern=r'Cadence ', repl=r'Average Cadence\n', string=more_stats)
                    more_stats = re.sub(pattern=r'(Average Cadence\n[0-9]{1,}) ([0-9]{1,})', repl=r'\1\nMax Cadence\n\2', string=more_stats)

                    # Power
                    more_stats = re.sub(pattern=r'Power ', repl=r'Average Power\n', string=more_stats)
                    more_stats = re.sub(pattern=r'(Average Power\n[0-9,]{1,} W) ([0-9,]{1,} W)', repl=r'\1\nMax Power\n\2', string=more_stats)

                    # Calories/Temperature/Elapsed Time
                    more_stats = re.sub(pattern=r'(Calories|Temperature|Elapsed Time) ', repl=r'\1\n', string=more_stats)
                    more_stats = more_stats.split(sep='\n')
                    more_stats = convert_list_to_dictionary(list=more_stats)


                    for item, value in more_stats.items():
                        d[item] = value

                        # max_speed
                        try:
                            d['Max Speed'] = re.sub(pattern=r'km/h$', repl=r'', string=d['Max Speed'])
                            d['Max Speed'] = float(d['Max Speed'])/3.6

                        except:
                            pass

                        # average_speed
                        try:
                            d['Average Speed'] = re.sub(pattern=r'km/h$', repl=r'', string=d['Average Speed'])
                            d['Average Speed'] = float(d['Average Speed'])/3.6

                        except:
                            pass

                        # max_heart_rate
                        try:
                            d['Max Heart Rate'] = re.sub(pattern=r' bpm', repl=r'', string=d['Max Heart Rate'])
                            d['Max Heart Rate'] = float(d['Max Heart Rate'])

                        except:
                            pass

                        # average_heart_rate
                        try:
                            d['Average Heart Rate'] = re.sub(pattern=r' bpm', repl=r'', string=d['Average Heart Rate'])
                            d['Average Heart Rate'] = float(d['Average Heart Rate'])

                        except:
                            pass

                        # max_cadence
                        try:
                            d['Max Cadence'] = float(d['Max Cadence'])

                        except:
                            pass

                        # average_cadence
                        try:
                            d['Average Cadence'] = float(d['Average Cadence'])

                        except:
                            pass

                        # max_watts
                        try:
                            d['Max Power'] = re.sub(pattern=r',', repl=r'', string=d['Max Power'])
                            d['Max Power'] = re.sub(pattern=r' W', repl=r'', string=d['Max Power'])
                            d['Max Power'] = float(d['Max Power'])

                        except:
                            pass

                        # average_watts
                        try:
                            d['Average Power'] = re.sub(pattern=r',', repl=r'', string=d['Average Power'])
                            d['Average Power'] = re.sub(pattern=r' W', repl=r'', string=d['Average Power'])
                            d['Average Power'] = float(d['Average Power'])

                        except:
                            pass

                        # elevation_gain
                        try:
                            d['Elevation'] = re.sub(pattern=r',', repl=r'', string=d['Elevation'])
                            d['Elevation'] = re.sub(pattern=r'm$', repl=r'', string=d['Elevation'])
                            d['Elevation'] = float(d['Elevation'])

                        except:
                            pass

                        # calories
                        try:
                            d['Calories'] = re.sub(pattern=r',', repl=r'', string=d['Calories'])
                            d['Calories'] = re.sub(pattern=u'\u2014', repl=r'', string=d['Calories'])
                            d['Calories'] = None if d['Calories'] == '' else float(d['Calories'])

                        except:
                            pass

                        # steps
                        try:
                            d['Steps'] = re.sub(pattern=r',', repl=r'', string=d['Steps'])
                            d['Steps'] = float(d['Steps'])

                        except:
                            pass

                        # average_temperature
                        try:
                            d['Temperature'] = re.sub(pattern=r'^([0-9]+).*', repl=r'\1', string=d['Temperature'])
                            d['Temperature'] = float(d['Temperature'])

                        except:
                            pass

                        # elapsed_time
                        try:

                            if len(d['Elapsed Time'].split(sep=':')) == 1:
                                d['Elapsed Time'] = re.sub(pattern=r'^([0-9]+)s$', repl=r'00:00:\1', string=d['Elapsed Time'])

                            if len(d['Elapsed Time'].split(sep=':')) == 2:
                                d['Elapsed Time'] = re.sub(pattern=r'^(.*)$', repl=r'00:\1', string=d['Elapsed Time'])

                            else:
                                pass


                        except:
                            pass

                except:
                    pass


                # activity_device
                try:
                    d['activity_device'] = driver.find_element(by=By.XPATH, value='.//div[@class="section device-section"]//div[@class="device spans8"]').text

                except:
                    pass

                # activity_kudos
                d['activity_kudos'] = driver.find_element(by=By.XPATH, value='.//span[@data-testid="kudos_count"]').text
                d['activity_kudos'] = int(d['activity_kudos'])


                data.append(d)


    # Create DataFrame
    club_activities = (pd.DataFrame(data=data, index=None, dtype=None)

        # Rename columns
        .clean_names()
        .rename(columns={'elevation': 'elevation_gain', 'max_power': 'max_watts', 'average_power': 'average_watts', 'temperature': 'average_temperature'})

    )


    ## Change dtypes

    # elapsed_time
    if 'elapsed_time' in club_activities.columns:
        club_activities['elapsed_time'] = pd.to_datetime(club_activities['elapsed_time'], format='%H:%M:%S').dt.time
        club_activities['elapsed_time'] = pd.to_timedelta(club_activities['elapsed_time'].astype(dtype='str')).dt.total_seconds()

    # moving_time
    if 'moving_time' in club_activities.columns:
        club_activities['moving_time'] = pd.to_datetime(club_activities['moving_time'], format='%H:%M:%S').dt.time
        club_activities['moving_time'] = pd.to_timedelta(club_activities['moving_time'].astype(dtype='str')).dt.total_seconds()

    # pace
    """
    if 'pace' in club_activities.columns:
        club_activities['pace'] = pd.to_datetime(club_activities['pace'], format='%H:%M:%S').dt.time
        club_activities['pace'] = pd.to_timedelta(club_activities['pace'].astype(dtype='str')).dt.total_seconds()
    """


    club_activities = (club_activities
        .filter(items=['club_id', 'activity_date', 'athlete_id', 'athlete_name', 'activity_type', 'activity_id', 'activity_name', 'activity_description', 'activity_location', 'commute', 'elapsed_time', 'moving_time', 'distance', 'max_speed', 'average_speed', 'pace', 'steps', 'elevation_gain', 'max_heart_rate', 'average_heart_rate', 'max_cadence', 'average_cadence', 'max_watts', 'average_watts', 'calories', 'activity_device', 'average_temperature', 'activity_kudos'])
    )


    # Filter activity types
    if filter_activities_type is not None:

        club_activities = (club_activities
            .query('activity_type.isin(@filter_activities_type)')
        )

    # Filter date interval
    if filter_date_min is not None and filter_date_max is not None:

        club_activities = (club_activities
            .query('activity_date >= @filter_date_min & activity_date <= @filter_date_max')
        )

    # Rearrange rows
    club_activities = (club_activities
        .sort_values(by=['club_id', 'activity_date'], ignore_index=True)
    )


    # Return objects
    return club_activities



# Strava export to .gpx - for a list of activity_id, export the .gpx file
def strava_export_gpx(*, activities_id):

    # Import or create global variables
    global driver


    # Strava login
    strava_login()


    # Export .gpx files
    for activity_id in activities_id:

        driver.get('https://www.strava.com/activities/' + str(activity_id) + '/export_gpx')

        # time.sleep(3)

        # Rename downloaded .gpx file
        # latest_file = max(glob.glob(pathname=os.path.join(os.getcwd(), 'activities', '*.gpx'), recursive=False), key=os.path.getctime)
        # latest_file_new_filename = os.path.join(os.getcwd(), 'activities', '{}_{}.gpx').format(row['activity_type'], row['activity_id'])
        # os.rename(src=latest_file, dst=latest_file_new_filename)



# Strava Club members - scrap list of members that joined a Strava Club
def strava_club_members(*, club_ids, club_members_teams=None, timezone='UTC'):

    # Import or create global variables
    global club_members
    global driver


    # Settings and variables
    geolocator = Nominatim(user_agent='strava-club-scraper')
    geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1)


    # Strava login
    strava_login()


    data = []

    for club_id in club_ids:

        # Open Strava Club members page
        driver.get('https://www.strava.com/clubs/' + club_id + '/members')
        time.sleep(3)


        # Create variables

        # club_name
        club_name = driver.find_element(by=By.XPATH, value='//h1[@class="mb-sm"]').text.split(sep='\n')[0]

        # club_activity_type
        club_activity_type = driver.find_element(by=By.XPATH, value='//div[@class="club-meta"]//div[@class="location"]//span[@class="app-icon-wrapper  "]').text

        # club_location
        club_location = driver.find_element(by=By.XPATH, value='//div[@class="club-meta"]//div[@class="location"]').text
        club_location = re.sub(pattern=r'^{}(.*)$'.format(club_activity_type), repl=r'\1', string=club_location).strip()


        # Get Strava Club members list
        while True:

            try:
                members = driver.find_elements(by=By.XPATH, value='//ul[@class="list-athletes"]//li')

                for member in members:

                    d = {}

                    # club_id
                    d['club_id'] = club_id

                    # club_name
                    d['club_name'] = club_name

                    # club_activity_type
                    d['club_activity_type'] = club_activity_type

                    # club_location
                    d['club_location'] = club_location

                    # athlete_id
                    d['athlete_id'] = member.find_element(by=By.XPATH, value='.//div[@class="text-headline"]//a').get_attribute('href')
                    d['athlete_id'] = re.sub(pattern=r'^.*/athletes/(.*)$', repl=r'\1', string=d['athlete_id'])

                    # athlete_name
                    d['athlete_name'] = member.find_element(by=By.XPATH, value='.//div[@class="text-headline"]').text

                    # athlete_location
                    d['athlete_location'] = member.find_element(by=By.XPATH, value='.//div[@class="location"]').text
                    d['athlete_location'] = d['athlete_location'].strip()

                    # athlete_picture
                    d['athlete_picture'] = member.find_element(by=By.XPATH, value='.//img[@class="avatar-img"]').get_attribute('src')

                    data.append(d)


                driver.find_element(by=By.XPATH, value='.//li[@class="next_page"]').click()

            except NoSuchElementException:
                break


    # Create DataFrame
    club_members = (pd.DataFrame(data=data, index=None, dtype=None)

        # Replace blank by NA
        .assign(athlete_location = lambda row: row['athlete_location'].mask(row['athlete_location'] == ''))

        # Remove duplicate rows
        .drop_duplicates(subset=None, keep='first', ignore_index=True)

    )


    # Create DataFrame with distinct 'athlete_location' values
    club_members_geolocation = (club_members
        .filter(items=['athlete_location'])
        .query('athlete_location.notna()')
        .drop_duplicates(subset=None, keep='first', ignore_index=True)
        .sort_values(by=['athlete_location'], ignore_index=True)
    )


    # Create 'athlete_geolocation' column
    club_members_geolocation['athlete_geolocation'] = club_members_geolocation.apply(lambda row: geocode(row['athlete_location'], language='en', exactly_one=True, addressdetails=True, namedetails=True, timeout=None) if pd.notna(row['athlete_location']) else None, axis=1)

    # Create 'athlete_location_country_code' column
    club_members_geolocation['athlete_location_country_code'] = club_members_geolocation.apply(lambda row: row['athlete_geolocation'].raw.get('address').get('country_code') if pd.notna(row['athlete_geolocation']) else None, axis=1)

    # Create 'athlete_location_country' column
    club_members_geolocation['athlete_location_country'] = club_members_geolocation.apply(lambda row: row['athlete_geolocation'].raw.get('address').get('country') if pd.notna(row['athlete_geolocation']) else None, axis=1)


    # Left join 'club_members' with 'club_members_geolocation'
    club_members = club_members.merge(club_members_geolocation, how='left', on=['athlete_location'], indicator=False)


    # Create 'athlete_team' column
    if club_members_teams is not None:

        club_members_teams = (pd.DataFrame.from_dict(data=club_members_teams, orient='index', dtype='str', columns=['athlete_id'])


            # Index to column
            .reset_index(level=None, drop=False)
            .rename(columns={'index': 'athlete_team'})


            # Replace multiple whitespaces by single whitespace in all columns
            .replace(to_replace=r'\s+', value=r' ', regex=True)


            # Separate collapsed  'athlete_id' column into multiple rows
            .assign(athlete_id = lambda row: row['athlete_id'].str.split(pat=', ', expand=False))
            .explode(column=['athlete_id'])


            # Rearrange rows
            .sort_values(by=['athlete_id', 'athlete_team'], ignore_index=True)


            # Remove duplicate rows
            .drop_duplicates(subset=None, keep='first', ignore_index=True)


            # Group 'athlete_id' and collapse 'athlete_team' into one row
            .groupby(by=['athlete_id'], axis=0, level=None, as_index=False, sort=True, dropna=True)
            .agg(athlete_team=('athlete_team', lambda row: ', '.join(row)))


            # Rearrange rows
            .sort_values(by=['athlete_id'], ignore_index=True)

        )


        # Left join 'club_members_teams'
        club_members = club_members.merge(club_members_teams, how='left', on=['athlete_id'], indicator=False)


    else:
        club_members['athlete_team'] = None


    club_members = (club_members

        # Remove columns
        .drop(columns=['athlete_geolocation'], axis=1)

        # Create 'join_date' column
        .assign(join_date = pd.Timestamp.now(tz=timezone).replace(tzinfo=None).floor(freq='d').to_pydatetime())

        # Select columns
        .filter(items=['club_id', 'club_name', 'club_location', 'club_activity_type', 'athlete_id', 'athlete_name', 'athlete_location', 'athlete_location_country_code', 'athlete_location_country', 'join_date', 'athlete_team', 'athlete_picture'])

        # Rearrange rows
        .sort_values(by=['club_id', 'athlete_id'], ignore_index=True)

    )


    # Return objects
    return club_members



# Strava Club leaderboard - scrap current and previous Strava Club activities leaderboard
def strava_club_leaderboard(*, club_ids, filter_date_min, filter_date_max, timezone='UTC'):

    """
    moving_time: seconds
    distance, distance_longest, elevation_gain: meters
    average_speed: meters/second
    """

    # Import or create global variables
    global club_leaderboard
    global driver


    # Settings and variables
    filter_date_min = parser.parse(filter_date_min)
    filter_date_max = parser.parse(filter_date_max)


    # Strava login
    strava_login()


    club_leaderboard = pd.DataFrame(data=None, index=None, dtype='object')

    for club_id in club_ids:

        # Open Strava Club leaderboard page
        driver.get('https://www.strava.com/clubs/' + club_id + '/leaderboard')
        time.sleep(3)


        # Create variables

        # club_name
        club_name = driver.find_element(by=By.XPATH, value='//h1[@class="mb-sm"]').text.split(sep='\n')[0]

        # club_activity_type
        club_activity_type = driver.find_element(by=By.XPATH, value='//div[@class="club-meta"]//div[@class="location"]//span[@class="app-icon-wrapper  "]').text

        # club_location
        club_location = driver.find_element(by=By.XPATH, value='//div[@class="club-meta"]//div[@class="location"]').text
        club_location = re.sub(pattern=r'^{}(.*)$'.format(club_activity_type), repl=r'\1', string=club_location).strip()


        # Get current week Strava Club Leaderboard
        try:
            driver.find_element(by=By.XPATH, value='//div[@class="leaderboard"]//h4[@class="empty-results"]').text

            club_leaderboard_import = pd.DataFrame(data=None, index=None, dtype='object')


        except NoSuchElementException:
            leaderboard_html = driver.find_element(by=By.XPATH, value='//table[@class="dense striped sortable"]').get_attribute('outerHTML')

            for d in pd.read_html(io=leaderboard_html, flavor='lxml'):

                # leaderboard_date_start
                d['leaderboard_date_start'] = pd.Timestamp.now(tz=timezone).replace(tzinfo=None).floor(freq='d').to_pydatetime() + relativedelta.relativedelta(weekday=relativedelta.MO(-1))

                # leaderboard_date_end
                d['leaderboard_date_end'] = pd.Timestamp.now(tz=timezone).replace(tzinfo=None).floor(freq='d').to_pydatetime() + relativedelta.relativedelta(weekday=relativedelta.MO(-1)) + relativedelta.relativedelta(weekday=relativedelta.SU(+1))

                # athlete_id
                d['athlete_id'] = lh.fromstring(leaderboard_html).xpath('.//tr//td//div//a//@href')
                d['athlete_id'] = d['athlete_id'].str.extract(r'/athletes/([0-9]+)')


            club_leaderboard_import = d


        # Get last week Strava Club Leaderboard
        driver.find_element(by=By.XPATH, value='//span[@class="button last-week"]').click()

        try:
            driver.find_element(by=By.XPATH, value='//div[@class="leaderboard"]//h4[@class="empty-results"]').text

            club_leaderboard_import = pd.DataFrame(data=None, index=None, dtype='object')


        except NoSuchElementException:
            leaderboard_html = driver.find_element(by=By.XPATH, value='//table[@class="dense striped sortable"]').get_attribute('outerHTML')

            for d in pd.read_html(io=leaderboard_html, flavor='lxml'):

                # leaderboard_date_start
                d['leaderboard_date_start'] = pd.Timestamp.now(tz=timezone).replace(tzinfo=None).floor(freq='d').to_pydatetime() + relativedelta.relativedelta(weekday=relativedelta.MO(-2))

                # leaderboard_date_end
                d['leaderboard_date_end'] = pd.Timestamp.now(tz=timezone).replace(tzinfo=None).floor(freq='d').to_pydatetime() + relativedelta.relativedelta(weekday=relativedelta.MO(-2)) + relativedelta.relativedelta(weekday=relativedelta.SU(+1))

                # athlete_id
                d['athlete_id'] = lh.fromstring(leaderboard_html).xpath('.//tr//td//div//a//@href')
                d['athlete_id'] = d['athlete_id'].str.extract(r'/athletes/([0-9]+)')


        # Concatenate DataFrames
        club_leaderboard_import = pd.concat(objs=[club_leaderboard_import, d], axis=0, ignore_index=True, sort=False)

        club_leaderboard_import = (club_leaderboard_import

            # Create 'club_id' column
            .assign(club_id = lambda row: club_id)

            # Create 'club_name' column
            .assign(club_name = lambda row: club_name)

            # Create 'club_activity_type' column
            .assign(club_activity_type = lambda row: club_activity_type)

            # Create 'club_location' column
            .assign(club_location = lambda row: club_location)

            # Rename columns
            .clean_names()

        )


        # Rename columns
        if club_activity_type == 'Cycling':
            club_leaderboard_import = (club_leaderboard_import
                .rename(columns={'rides': 'activities', 'longest': 'distance_longest', 'avg_speed': 'average_speed'})
            )

        if club_activity_type == 'Running':
            club_leaderboard_import = (club_leaderboard_import
                .rename(columns={'runs': 'activities', 'avg_pace': 'pace'})
            )

        if club_activity_type == 'Run/Walk/Hike':
            pass


        # Concatenate DataFrames
        club_leaderboard = pd.concat(objs=[club_leaderboard, club_leaderboard_import], axis=0, ignore_index=True, sort=False)


    # Rename columns
    club_leaderboard = club_leaderboard.rename(columns={'athlete': 'athlete_name', 'time': 'moving_time', 'elev_gain': 'elevation_gain'})


    # Create columns

    # leaderboard_week
    club_leaderboard['leaderboard_week'] = club_leaderboard['leaderboard_date_start'].dt.strftime('%Y-%m-%d') + ' to ' + club_leaderboard['leaderboard_date_end'].dt.strftime('%Y-%m-%d')


    # Change dtypes

    # average_speed
    if 'average_speed' in club_leaderboard.columns:
        club_leaderboard['average_speed'] = club_leaderboard['average_speed'].replace(to_replace=r'km/h$', value=r'', regex=True)
        club_leaderboard['average_speed'] = club_leaderboard['average_speed'].astype(dtype='float')
        club_leaderboard['average_speed'] = club_leaderboard['average_speed']/3.6

    # distance
    if 'distance' in club_leaderboard.columns:
        club_leaderboard['distance'] = club_leaderboard['distance'].replace(to_replace=r'^--$', value=r'0 km', regex=True)
        club_leaderboard['distance'] = club_leaderboard['distance'].replace(to_replace=r',', value=r'', regex=True)
        club_leaderboard['distance'] = club_leaderboard['distance'].replace(to_replace=r' km$', value=r'', regex=True)
        club_leaderboard['distance'] = club_leaderboard['distance'].astype(dtype='float')
        club_leaderboard['distance'] = club_leaderboard['distance']*1000

    # distance_longest
    if 'distance_longest' in club_leaderboard.columns:
        club_leaderboard['distance_longest'] = club_leaderboard['distance_longest'].replace(to_replace=r',', value=r'', regex=True)
        club_leaderboard['distance_longest'] = club_leaderboard['distance_longest'].replace(to_replace=r' km$', value=r'', regex=True)
        club_leaderboard['distance_longest'] = club_leaderboard['distance_longest'].astype(dtype='float')
        club_leaderboard['distance_longest'] = club_leaderboard['distance_longest']*1000

    # elevation_gain
    if 'elevation_gain' in club_leaderboard.columns:
        club_leaderboard['elevation_gain'] = club_leaderboard['elevation_gain'].replace(to_replace=r'^--$', value=r'0 m', regex=True)
        club_leaderboard['elevation_gain'] = club_leaderboard['elevation_gain'].replace(to_replace=r',', value=r'', regex=True)
        club_leaderboard['elevation_gain'] = club_leaderboard['elevation_gain'].replace(to_replace=r' m$', value=r'', regex=True)
        club_leaderboard['elevation_gain'] = club_leaderboard['elevation_gain'].astype(dtype='float')

    # moving_time: '%H:%M' to seconds
    if 'moving_time' in club_leaderboard.columns:
        club_leaderboard['moving_time'] = club_leaderboard['moving_time'].fillna(value='0m')
        club_leaderboard['moving_time'] = club_leaderboard['moving_time'].replace(to_replace=r'^([0-9]+m)$', value=r'00:\1', regex=True)
        club_leaderboard['moving_time'] = club_leaderboard['moving_time'].replace(to_replace=r'h ', value=r':', regex=True)
        club_leaderboard['moving_time'] = club_leaderboard['moving_time'].replace(to_replace=r'm$', value=r'', regex=True)
        club_leaderboard['moving_time'] = club_leaderboard['moving_time'].apply(lambda row: float(row.split(sep=':')[0])*3600 + float(row.split(sep=':')[1])*60)

    # pace
    """
    if 'pace' in club_leaderboard.columns:

        club_leaderboard['pace'] = club_leaderboard['pace'].astype(dtype='str')

        club_leaderboard['pace'] = club_leaderboard['pace'].replace(to_replace=r' /km$', value=r'', regex=True)
        club_leaderboard['pace'] = club_leaderboard['pace'].apply(lambda row: re.sub(pattern=r'^([0-9]+)$', value=r'00:00:\1', string=row) if(len(row.split(sep=':')) == 1) else re.sub(pattern=r'^(.*)$', repl=r'00:\1', string=row), axis=1)

        club_leaderboard['pace'] = pd.to_datetime(club_leaderboard['pace'], format='%H:%M:%S').dt.time
        club_leaderboard['pace'] = pd.to_timedelta(club_leaderboard['pace'].astype(dtype='str')).dt.total_seconds()
    """


    club_leaderboard = (club_leaderboard

        # Select columns
        .filter(items=['club_id', 'club_name', 'club_activity_type', 'club_location', 'leaderboard_week', 'leaderboard_date_start', 'leaderboard_date_end', 'rank', 'athlete_id', 'athlete_name', 'activities', 'moving_time', 'distance', 'distance_longest', 'average_speed', 'pace', 'elevation_gain'])

        # Filter date interval
        .query('leaderboard_date_start >= @filter_date_min & leaderboard_date_end <= @filter_date_max')

        # Rearrange rows
        .sort_values(by=['club_id', 'leaderboard_date_start', 'rank'], ignore_index=True)

    )


    # Return objects
    return club_leaderboard



# Strava Club Leaderboard manual import - For members that joined the challenge later, manually scrap inividual activities and group them by week
def strava_club_leaderboard_manual(*, club_activities_df, club_id=None, club_name=None, club_activity_type=None, club_location=None, filter_activities_type=None):

    # Import or create global variables
    global club_leaderboard_manual


    club_leaderboard_manual = (club_activities_df

        # Filter activity types
        .query('activity_type.isin(@filter_activities_type)')

        .assign(

            # Create 'club_id' column
            club_id = club_id,

            # Create 'club_name' column
            club_name = club_name,

            # Create 'club_activity_type' column
            club_activity_type = club_activity_type,

            # Create 'club_location' column
            club_location = club_location

        )

    )


    # leaderboard_date_start
    club_leaderboard_manual['leaderboard_date_start'] = club_leaderboard_manual.apply(lambda row: (row['activity_date'].floor(freq='d') + relativedelta.relativedelta(weekday=relativedelta.MO(-1))), axis=1)

    # leaderboard_date_end
    club_leaderboard_manual['leaderboard_date_end'] = club_leaderboard_manual.apply(lambda row: (row['activity_date'].floor(freq='d') + relativedelta.relativedelta(weekday=relativedelta.MO(-1)) + relativedelta.relativedelta(weekday=relativedelta.SU(+1))), axis=1)

    club_leaderboard_manual = (club_leaderboard_manual

        # Create 'leaderboard_week' column
        .assign(leaderboard_week = lambda row: row['leaderboard_date_start'].dt.strftime('%Y-%m-%d') + ' to ' + row['leaderboard_date_end'].dt.strftime('%Y-%m-%d'))

        # Create 'rank' column
        .assign(rank = 999)

        # Aggregate rows
        .groupby(by=['club_id', 'club_name', 'club_activity_type', 'club_location', 'leaderboard_week', 'leaderboard_date_start', 'leaderboard_date_end', 'rank', 'athlete_id', 'athlete_name'], axis=0, level=None, as_index=False, sort=True, dropna=False)
        .agg(activities=('activity_id', 'nunique'), moving_time=('moving_time', 'sum'), distance=('distance', 'sum'), distance_longest=('distance', 'max'), average_speed=('average_speed', 'mean'), elevation_gain=('elevation_gain', 'sum'))

        # Select columns
        .filter(items=['club_id', 'club_name', 'club_activity_type', 'club_location', 'leaderboard_week', 'leaderboard_date_start', 'leaderboard_date_end', 'rank', 'athlete_id', 'athlete_name', 'activities', 'moving_time', 'distance', 'distance_longest', 'average_speed', 'elevation_gain'])

        # Rearrange rows
        .sort_values(by=['club_id', 'leaderboard_date_start', 'athlete_name'], ignore_index=True)

    )


    # Return objects
    return club_leaderboard_manual



# Google API credentials
def google_api_credentials():

    # Credentials settings
    credentials = Credentials.from_service_account_file(filename=google_api_key, scopes=['https://www.googleapis.com/auth/spreadsheets'])


    # service
    service = build(serviceName='sheets', version='v4', credentials=credentials)


    # Return objects
    return service



# Strava Club to Google Sheets
def strava_club_to_google_sheets(*, df, sheet_id, sheet_name):

    # Import or create global variables
    global club_members


    # Google API Credentials
    service = google_api_credentials()


    # Import DataFrame stored in Google Sheets
    result = service.spreadsheets().values().get(spreadsheetId=sheet_id, range=sheet_name).execute()
    df_import = pd.DataFrame(data=result.get('values', []), index=None, dtype='object')

    if not df_import.empty:

        # Rename columns
        df_import = df_import.rename(columns=df_import.iloc[0])
        df_import = df_import.iloc[1:].reset_index(level=None, drop=True)


        # Change dtypes
        df_import = df_import.replace(to_replace=r'^\s*$', value=None, regex=True)


        # club_activities
        if 'activity_id' in df.columns:

            # Change dtypes
            df_import = (df_import
                .astype(dtype={'elapsed_time': 'float', 'moving_time': 'float', 'distance': 'float', 'max_speed': 'float', 'average_speed': 'float', 'steps': 'float', 'elevation_gain': 'float', 'max_heart_rate': 'float', 'average_heart_rate': 'float', 'max_cadence': 'float', 'average_cadence': 'float', 'max_watts': 'float', 'average_watts': 'float', 'calories': 'float', 'average_temperature': 'float', 'activity_kudos': 'int'})
                .assign(activity_date = lambda row: row['activity_date'].apply(parser.parse))

            )


            # Delete Google Sheets DataFrame rows present in club_activities, completely overwriting it
            df_import = (df_import

                # Outer join 'df'
                .merge(df.filter(items=['club_id', 'activity_id']).drop_duplicates(subset=None, keep='first', ignore_index=True), how='outer', on=['club_id', 'activity_id'], indicator=True)

                # Filter rows
                .query('_merge == "left_only"')

                # Remove columns
                .drop(columns=['_merge'], axis=1)

            )


        # club_members
        if 'join_date' in df.columns:

            # Change dtypes
            df_import['join_date'] = df_import['join_date'].apply(parser.parse)


            # Keep Google Sheets DataFrame rows present in club_members, increment with new club members
            df = (df

                # Outer join 'df_import'
                .merge(df_import.filter(items=['club_id', 'athlete_id']).drop_duplicates(subset=None, keep='first', ignore_index=True), how='outer', on=['club_id', 'athlete_id'], indicator=True)


                # Filter rows
                .query('_merge == "left_only"')


                # Remove columns
                .drop(columns=['_merge'], axis=1)

            )


        # club_leaderboard
        if 'leaderboard_week' in df.columns:

            # Change dtypes
            df_import = (df_import
                .astype(dtype={'rank': 'int', 'activities': 'int', 'moving_time': 'float', 'distance': 'float', 'distance_longest': 'float', 'average_speed': 'float', 'elevation_gain': 'float'})
                .assign(leaderboard_date_start = lambda row: row['leaderboard_date_start'].apply(parser.parse))
                .assign(leaderboard_date_end = lambda row: row['leaderboard_date_end'].apply(parser.parse))
            )


            try:
                df_import = df_import.astype(dtype={'distance_longest': 'float'})

            except:
                pass


            # Delete Google Sheets DataFrame rows present in club_leaderboard, completely overwriting it
            df_import = (df_import

                # Remove columns
                .drop(columns=['athlete_location', 'athlete_location_country_code', 'athlete_location_country', 'athlete_team', 'athlete_picture'], axis=1)

                # Outer join 'df'
                .merge(df.filter(items=['club_id', 'leaderboard_week']).drop_duplicates(subset=None, keep='first', ignore_index=True), how='outer', on=['club_id', 'leaderboard_week'], indicator=True)

                # Filter rows
                .query('_merge == "left_only"')

                # Remove columns
                .drop(columns=['_merge'], axis=1)

            )


    else:
        pass


    # Concatenate DataFrames
    df_updated = pd.concat(objs=[df, df_import], axis=0, ignore_index=True, sort=False)


    # club_activities transform
    if 'activity_id' in df.columns:

        # Change dtypes
        df_updated['activity_date'] = df_updated['activity_date'].dt.strftime('%Y-%m-%d')


        # Select columns
        df_updated = df_updated.filter(items=['club_id', 'activity_date', 'athlete_id', 'athlete_name', 'activity_type', 'activity_id', 'activity_name', 'activity_description', 'activity_location', 'commute', 'elapsed_time', 'moving_time', 'distance', 'max_speed', 'average_speed', 'pace', 'steps', 'elevation_gain', 'max_heart_rate', 'average_heart_rate', 'max_cadence', 'average_cadence', 'max_watts', 'average_watts', 'calories', 'activity_device', 'average_temperature', 'activity_kudos'])


        # Rearrange rows
        df_updated = df_updated.sort_values(by=['club_id', 'activity_date'], ignore_index=True)


    # club_members transform
    if 'join_date' in df.columns:

        # Change dtypes
        df_updated['join_date'] = df_updated['join_date'].dt.strftime('%Y-%m-%d')


        # Remove columns
        df_updated = df_updated.drop(['athlete_team'], axis=1)


        # Left join 'club_members'
        df_updated = df_updated.merge(club_members.filter(items=['club_id', 'athlete_id', 'athlete_location', 'athlete_location_country_code', 'athlete_location_country', 'athlete_team', 'athlete_picture']), how='left', on=['club_id', 'athlete_id'], indicator=False)

        # In case club_members scraped 'club_id' and 'athlete_id' information, update 'df_updated'
        df_updated['athlete_location'] = df_updated['athlete_location_y'].fillna(df_updated['athlete_location_x'])
        df_updated['athlete_location_country_code'] = df_updated['athlete_location_country_code_y'].fillna(df_updated['athlete_location_country_code_x'])
        df_updated['athlete_location_country'] = df_updated['athlete_location_country_y'].fillna(df_updated['athlete_location_country_x'])
        df_updated['athlete_picture'] = df_updated['athlete_picture_y'].fillna(df_updated['athlete_picture_x'])
        df_updated = df_updated.drop(['athlete_location_x', 'athlete_location_y', 'athlete_location_country_code_x', 'athlete_location_country_code_y', 'athlete_location_country_x', 'athlete_location_country_y', 'athlete_picture_x', 'athlete_picture_y'], axis=1)


        df_updated = (df_updated

            # Select columns
            .filter(items=['club_id', 'club_name', 'club_location', 'club_activity_type', 'athlete_id', 'athlete_name', 'athlete_location', 'athlete_location_country_code', 'athlete_location_country', 'join_date', 'athlete_team', 'athlete_picture'])


            # Rearrange rows
            .sort_values(by=['club_id', 'athlete_id'], ignore_index=True)

        )


    # club_leaderboard transform
    if 'leaderboard_week' in df.columns:

        # Left join 'club_members'
        df_updated = df_updated.merge(club_members.filter(items=['club_id', 'athlete_id', 'athlete_location', 'athlete_location_country_code', 'athlete_location_country', 'athlete_team', 'athlete_picture']), how='left', on=['club_id', 'athlete_id'], indicator=False)


        # Change dtypes
        df_updated['leaderboard_date_start'] = df_updated['leaderboard_date_start'].dt.strftime('%Y-%m-%d')
        df_updated['leaderboard_date_end'] = df_updated['leaderboard_date_end'].dt.strftime('%Y-%m-%d')


        # Select columns
        df_updated = df_updated.filter(items=['club_id', 'club_name', 'club_activity_type', 'club_location', 'leaderboard_week', 'leaderboard_date_start', 'leaderboard_date_end', 'rank', 'athlete_id', 'athlete_name', 'activities', 'moving_time', 'distance', 'distance_longest', 'average_speed', 'pace', 'elevation_gain', 'athlete_location', 'athlete_location_country_code', 'athlete_location_country', 'athlete_team', 'athlete_picture'])


        # Rearrange rows
        df_updated = df_updated.sort_values(by=['club_id', 'leaderboard_date_start', 'rank'], ignore_index=True)


    # Change dtypes
    df_updated = df_updated.fillna(value='')


    # DataFrame to list
    data = [df_updated.columns.values.tolist()]
    data.extend(df_updated.values.tolist())


    # Clear sheet contents
    service.spreadsheets().values().clear(spreadsheetId=sheet_id, range=sheet_name, body={}).execute()


    # Upload/Overwrite DataFrame stored in Google Sheets
    service.spreadsheets().values().update(spreadsheetId=sheet_id, range=sheet_name, valueInputOption='USER_ENTERED', body={'values': data}).execute()


    # Return objects
    return df_updated



# Execution time to Google Sheets
def execution_time_to_google_sheets(*, sheet_id, sheet_name, timezone='UTC'):

    # Google API Credentials
    service = google_api_credentials()

    # Clear sheet contents
    service.spreadsheets().values().clear(spreadsheetId=sheet_id, range=sheet_name, body={}).execute()

    # Upload/Overwrite DataFrame stored in Google Sheets
    service.spreadsheets().values().update(spreadsheetId=sheet_id, range=sheet_name, valueInputOption='USER_ENTERED', body={'values': [['last_execution'], [str(pd.Timestamp.now(tz=timezone).replace(microsecond=0, tzinfo=None))]]}).execute()




################################
# Strava Club activities scraper
################################

## Club activities

# Get data (via web-scraping)
# strava_club_activities(club_ids=club_ids, filter_activities_type=None, filter_date_min=filter_date_min, filter_date_max=filter_date_max, timezone=timezone)

# Update Google Sheets sheet
# strava_club_to_google_sheets(df=club_activities, sheet_id=sheet_id, sheet_name='Activities')

# Save as .csv
# club_activities.to_csv(path_or_buf='club_activities.csv', sep=',', na_rep='', header=True, index=False, index_label=None, encoding='utf8')

# Export club activities to .gpx files
# club_activities = pd.read_csv(filepath_or_buffer='activities.csv', sep=',', header=0, index_col=None, skiprows=0, skipfooter=0, dtype=None, engine='python', encoding='utf8')
# club_activities = club_activities.astype(dtype={'activity_id': 'str'})
# club_activities_sample = club_activities.loc[club_activities['activity_type'].isin(['Ride', 'E-Bike Ride', 'Run', 'Walk', 'Hike'])]
# strava_export_gpx(activities_id=club_activities_sample['activity_id'])

# Strava Club Leaderboard manual import - For members that joined the challenge later, manually scrap inividual activities and group them by week
# strava_club_leaderboard_manual(club_activities_df=club_activities, club_id=None, club_name=None, club_activity_type=None, club_location=None, filter_activities_type=['Ride', 'E-Bike Ride'])



## Club members

# Get data (via web-scraping)
strava_club_members(club_ids=club_ids, club_members_teams=club_members_teams, timezone=timezone)

# Test
(club_members
	.filter(items=['athlete_team', 'athlete_name', 'athlete_id'])
    .query('athlete_team.notna()')
    .drop_duplicates(subset=None, keep='first', ignore_index=True)
    .assign(athlete_team = lambda row: row['athlete_team'].str.split(pat=', ', expand=False))
    .explode(column=['athlete_team'])
	.sort_values(by=['athlete_team', 'athlete_name'], ignore_index=True)
)

# Update Google Sheets sheet
club_members = strava_club_to_google_sheets(df=club_members, sheet_id=sheet_id, sheet_name='Members')



## Club leaderboard

# Get data (via web-scraping)
strava_club_leaderboard(club_ids=club_ids, filter_date_min=filter_date_min, filter_date_max=filter_date_max, timezone=timezone)

# Update Google Sheets sheet
strava_club_to_google_sheets(df=club_leaderboard, sheet_id=sheet_id, sheet_name='Leaderboard')



## Store execution time in Google Sheets

# Update Google Sheets sheet
execution_time_to_google_sheets(sheet_id=sheet_id, sheet_name='Execution Time', timezone=timezone)


## Quit Selenium webdriver
selenium_webdriver_quit()
