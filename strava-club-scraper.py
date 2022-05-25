## Strava Club Scraper
# Last update: 2022-05-25


#########################
# ---- initial_setup ----
#########################

## Erase all declared global variables
globals().clear()


## Import packages
from datetime import datetime, timedelta
import locale
import os
import re
import sys
import time

from dateutil import parser, relativedelta
from geopy.geocoders import Nominatim
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import janitor
import lxml.html as lh
import numpy as np
import pandas as pd
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager


## Set working directory to user's 'Documents/Strava Club Scraper' folder
if sys.platform == 'win32':
    os.chdir(os.path.join(os.path.expanduser('~'), 'Documents', 'Strava Club Scraper'))


## Settings

# Strava login
strava_email = 'test@email.com'
strava_password = 'Password12345'

# Strava Clubs
club_ids = ['319098']
filter_activities_type = ['E-Bike Ride', 'Ride', 'Run'] # Only for Strava Clubs with multiple sport types
filter_date_min = '2022-05-09'
filter_date_max = '2022-05-29'

# Google API
google_api_key = os.path.join(os.getcwd(), 'files', 'keys.json')

# Google Sheets
sheet_id = 'GOOGLE_SHEET_ID'




#####################
# ---- functions ----
#####################

### convert_list_to_dictionary
def convert_list_to_dictionary(list):

    list = iter(list)
    dictionary = dict(zip(list, list))

    ## Return objects
    return dictionary



### selenium_webdriver
def selenium_webdriver():

    ## Webdriver options
    chrome_options = webdriver.ChromeOptions()
    chrome_options.page_load_strategy = 'normal'

    # Webdriver download settings
    chrome_options.add_experimental_option('prefs', {
        'download.default_directory': os.path.join(os.path.join(os.getcwd(), 'activities')),
        'download.prompt_for_download': False,
        'profile.default_content_setting_values.automatic_downloads': 1,
    })

    # Webdriver
    if sys.platform=='win32':
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    elif sys.platform=='linux' or sys.platform=='linux2':
        chrome_options.binary_location = os.environ.get('GOOGLE_CHROME_BIN')
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--no-sandbox')
        driver = webdriver.Chrome(service=Service(os.environ.get('CHROMEDRIVER_PATH')), options=chrome_options)


    ## Return objects
    return driver



### strava_login
def strava_login():

    ## Load Selenium webdriver
    driver = selenium_webdriver()

    ## Open website
    driver.get('https://www.strava.com/login')
    time.sleep(2)

    ## Reject cookies
    driver.find_element(by=By.XPATH, value=".//button[@class='btn-deny-cookie-banner']").click()

    ## Login
    driver.find_element_by_id('email').send_keys(strava_email)
    driver.find_element_by_id('password').send_keys(strava_password)
    time.sleep(2)

    driver.find_element(by=By.XPATH, value=".//*[@type='submit']").submit()

    ## Return objects
    return driver



### strava_club_activities
def strava_club_activities(club_ids, filter_activities_type, filter_date_min, filter_date_max):

    ## Extract stats
    # elapsed_time, moving_time: seconds
    # pace: seconds per kilometer
    # distance, elevation_gain: meters
    # max_speed, average_speed: meters/second
    # temperature: degree Celsius

    # Import or create global variables
    global club_activities

    ## Strava login
    driver = strava_login()


    data = []

    for club_id in club_ids:

        ## Open Strava Club activities feed page
        driver.get('https://www.strava.com/dashboard?club_id='+club_id+'&feed_type=club&num_entries=100')
        time.sleep(3)

        ## Scroll to the end of the webpage
        while True:

            try:
                driver.find_element(by=By.XPATH, value="//div[@class='Feed--feed-pagination--yh121 Feed--no-entries--ARKOk']")
                break

            except NoSuchElementException:

                activities = driver.find_elements(by=By.XPATH, value="//div[@data-testid='activity_entry_container']")
                activity_date = activities[-1].find_element(by=By.XPATH, value=".//..//..//..//..//..//time").text
                activity_date = re.sub(r'^(Today at )(.*)$', str(datetime.now().date())+r' \2', activity_date)
                activity_date = re.sub(r'^(Yesterday at )(.*)$', str((datetime.now() - timedelta(1)).date())+r' \2', activity_date)
                activity_date = parser.parse(activity_date)

                if activity_date >= parser.parse(filter_date_min):

                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(6)

                else:
                    break


        ## Get all displayed activities_id, filtering filter_date_min and activity_type (note: activity_type filter does not work for group activities - thus all group activities are kept and verified on a case-by-case base)
        activities_id = []
        activities_id_remove = []

        activities = driver.find_elements(by=By.XPATH, value="//div[@data-testid='activity_entry_container']")

        for activity in activities:

            activity_date = activity.find_element(by=By.XPATH, value=".//..//..//..//..//..//time").text
            activity_date = re.sub(r'^(Today at )(.*)$', str(datetime.now().date())+r' \2', activity_date)
            activity_date = re.sub(r'^(Yesterday at )(.*)$', str((datetime.now() - timedelta(1)).date())+r' \2', activity_date)
            activity_date = parser.parse(activity_date)

            if parser.parse(filter_date_min) <= activity_date < (parser.parse(filter_date_max) + timedelta(days=1)):

                activity_id = activity.find_element(by=By.XPATH, value=".//..//..//h3//a").get_attribute("href")
                activity_id = re.sub(r'^.*/activities/(.*)$', r'\1', activity_id)
                activity_id = re.sub(r'^([0-9]+)(\?|/|#).*$', r'\1', activity_id)
                activities_id.append(activity_id)

                try:
                    activity_type = activity.find_element(by=By.XPATH, value=".//..//..//div[@class='Activity--entry-icon--RlkFx ']//*[local-name()='svg']").get_attribute("title")

                    if activity_type not in filter_activities_type:
                        activities_id_remove.append(activity_id)

                except:
                    pass


        activities_id = list(set(activities_id))
        activities_id = sorted(activities_id)

        activities_id_remove = list(set(activities_id_remove))
        activities_id_remove = sorted(activities_id_remove)

        activities_id = [x for x in activities_id if x not in activities_id_remove]


        for activity in activities_id:

            d = {}

            driver.get('https://www.strava.com/activities/'+activity)

            d['club_id'] = club_id

            # activity_id
            d['activity_id'] = activity


            # athlete_name, activity_type
            d['athlete_name'], d['activity_type'] = driver.find_element(by=By.XPATH, value=".//span[@class='title']").text.split(' – ')[0:2]

            try:
                d['commute'] = driver.find_element(by=By.XPATH, value=".//span[@class='title']").text.split(' – ')[2]
                d['commute'] = re.sub(r'^Commute$', r'True', d['commute'])
                d['commute'] = bool(d['commute'])

            except:
                pass

            # activity_date
            d['activity_date'] = driver.find_element(by=By.XPATH, value=".//div[@class='details-container']//time").text
            d['activity_date'] = re.sub(r'^(.*) on (.*)$', r'\2 \1', d['activity_date'])
            d['activity_date'] = parser.parse(d['activity_date'])

            if d['activity_type'] in filter_activities_type:

                ## Activity stats

                # Click on "Show More" button
                try:
                    driver.find_element(by=By.XPATH, value=".//button[@class='minimal compact']").click()

                except:
                    pass

                # athlete_id
                d['athlete_id'] = driver.find_element(by=By.XPATH, value=".//div[@class='details-container']//a").get_attribute("href")
                d['athlete_id'] = re.sub(r'^.*/athletes/(.*)$', r'\1', d['athlete_id'])

                # activity_name
                d['activity_name'] = driver.find_element(by=By.XPATH, value=".//div[@class='details-container']//h1").text

                # activity_description
                try:
                    d['activity_description'] = driver.find_element(by=By.XPATH, value=".//div[@class='details-container']//div[@class='content']").text

                except:
                    pass

                # activity_location
                try:
                    d['activity_location'] = driver.find_element(by=By.XPATH, value=".//div[@class='details-container']//span[@class='location']").text
                    
                except:
                    pass

                # Inline stats
                inline_stats = driver.find_element(by=By.XPATH, value=".//ul[@class='inline-stats section']").text.split('\n')
                inline_stats = convert_list_to_dictionary(inline_stats)
                inline_stats = {value: name for name, value in inline_stats.items()}

                for item, value in inline_stats.items():
                    d[item] = value

                    # distance
                    try:
                        d['Distance'] = re.sub(r',', r'', d['Distance'])
                        d['Distance'] = re.sub(r'km$', r'', d['Distance'])
                        d['Distance'] = float(d['Distance'])
                        d['Distance'] = d['Distance']*1000

                    except:
                        pass



                    # elevation_gain
                    try:
                        d['Elevation'] = re.sub(r',', r'', d['Elevation'])
                        d['Elevation'] = re.sub(r'm$', r'', d['Elevation'])
                        d['Elevation'] = float(d['Elevation'])

                    except:
                        pass

                    # moving_time
                    try:

                        if len(d['Moving Time'].split(':')) == 1:
                            d['Moving Time'] = re.sub(r'^([0-9]+)s$', r'00:00:\1', d['Moving Time'])

                        if len(d['Moving Time'].split(':')) == 2:
                            d['Moving Time'] = re.sub(r'^(.*)$', r'00:\1', d['Moving Time'])



                    except:
                        pass

                    # pace
                    try:

                        d['Pace'] = re.sub(r'/km', r'', d['Pace'])


                        if len(d['Pace'].split(':')) == 1:
                            d['Pace'] = re.sub(r'^([0-9]+)$', r'00:00:\1', d['Pace'])

                        if len(d['Pace'].split(':')) == 2:
                            d['Pace'] = re.sub(r'^(.*)$', r'00:\1', d['Pace'])

                    except:
                        pass


                # More stats
                try:
                    more_stats = driver.find_element(by=By.XPATH, value=".//div[@class='section more-stats']").text
                    more_stats = re.sub(r'Show Less\n|Avg Max\n', r'', more_stats)
                    more_stats = re.sub(r'^Speed ', r'Average Speed\n', more_stats)
                    more_stats = re.sub(r'^Speed ', r'Average Speed\n', more_stats)
                    more_stats = re.sub(r'(km/h*?) ', r'\1\nMax Speed\n', more_stats)
                    more_stats = re.sub(r'(Calories|Elapsed Time|Temperature) ', r'\1\n', more_stats)
                    more_stats = more_stats.split('\n')
                    more_stats = convert_list_to_dictionary(more_stats)

                    for item, value in more_stats.items():
                        d[item] = value

                        # average_speed
                        try:
                            d['Average Speed'] = re.sub(r'km/h$', r'', d['Average Speed'])
                            d['Average Speed'] = float(d['Average Speed'])
                            d['Average Speed'] = d['Average Speed']/3.6

                        except:
                            pass

                        # elevation_gain
                        try:
                            d['Elevation'] = re.sub(r',', r'', d['Elevation'])
                            d['Elevation'] = re.sub(r'm$', r'', d['Elevation'])
                            d['Elevation'] = float(d['Elevation'])

                        except:
                            pass

                        # max_speed
                        try:
                            d['Max Speed'] = re.sub(r'km/h$', r'', d['Max Speed'])
                            d['Max Speed'] = float(d['Max Speed'])
                            d['Max Speed'] = d['Max Speed']/3.6

                        except:
                            pass


                        # calories
                        try:
                            d['Calories'] = re.sub(r',', r'', d['Calories'])
                            d['Calories'] = re.sub(u'\u2014', 'NaN', d['Calories'])
                            d['Calories'] = float(d['Calories'])

                        except:
                            pass

                        # elapsed_time
                        try:

                            if len(d['Elapsed Time'].split(':')) == 1:
                                d['Elapsed Time'] = re.sub(r'^([0-9]+)s$', r'00:00:\1', d['Elapsed Time'])

                            if len(d['Elapsed Time'].split(':')) == 2:
                                d['Elapsed Time'] = re.sub(r'^(.*)$', r'00:\1', d['Elapsed Time'])

                        except:
                            pass

                        # temperature
                        try:

                            d['Temperature'] = re.sub(r'^([0-9]+).*', r'\1', d['Temperature'])
                            d['Temperature'] = float(d['Temperature'])


                        except:
                            pass
                            
                except:
                    pass

                # activity_device
                try:
                    d['activity_device'] = driver.find_element(by=By.XPATH, value=".//div[@class='section device-section']//div[@class='device spans8']").text
                    
                except:
                    pass

                # activity_kudos
                d['activity_kudos'] = driver.find_element(by=By.XPATH, value=".//span[@class='count']").get_attribute("data-count")
                d['activity_kudos'] = int(d['activity_kudos'])

                data.append(d)

            else:
                pass


    ## Driver quit
    driver.quit()

    ## Create dataframe
    club_activities = pd.DataFrame(data)

    ## Rename columns
    club_activities = club_activities.clean_names()
    club_activities = club_activities.rename(columns={'elevation': 'elevation_gain'})


    ## Change dtypes

    # elapsed_time
    club_activities['elapsed_time'] = pd.to_datetime(club_activities['elapsed_time'], format='%H:%M:%S').dt.time
    club_activities['elapsed_time'] = pd.to_timedelta(club_activities['elapsed_time'].astype(str)).dt.total_seconds()

    # moving_time
    club_activities['moving_time'] = pd.to_datetime(club_activities['moving_time'], format='%H:%M:%S').dt.time
    club_activities['moving_time'] = pd.to_timedelta(club_activities['moving_time'].astype(str)).dt.total_seconds()

    # pace
    club_activities['pace'] = pd.to_datetime(club_activities['pace'], format='%H:%M:%S').dt.time
    club_activities['pace'] = pd.to_timedelta(club_activities['pace'].astype(str)).dt.total_seconds()


    ## Rearrange columns
    club_activities = club_activities.filter(['club_id', 'activity_date', 'athlete_id', 'athlete_name', 'activity_type', 'activity_id', 'activity_name', 'activity_description', 'activity_location', 'elapsed_time', 'moving_time', 'distance', 'max_speed', 'average_speed', 'elevation_gain', 'pace', 'calories', 'activity_device', 'temperature', 'activity_kudos'])

    ## Filter activity types
    club_activities = club_activities[club_activities['activity_type'].isin(filter_activities_type)]

    ## Filter date interval
    club_activities = club_activities[(club_activities['activity_date'] >= parser.parse(filter_date_min)) & (club_activities['activity_date'] < (parser.parse(filter_date_max) + timedelta(1)))].reset_index(drop=True)

    ## Rarrange rows
    club_activities = club_activities.sort_values(by=['club_id', 'activity_date'], ignore_index=True)

    ## Return objects
    return club_activities



### strava_export_gpx
def strava_export_gpx(activities):

    ## Strava login
    driver = strava_login()

    ## Export .gpx files
    for activity in activities:
        driver.get('https://www.strava.com/activities/'+activity+'/export_gpx')

    ## Driver quit
    driver.quit()



### strava_club_leaderboard
def strava_club_leaderboard(club_ids, filter_date_min, filter_date_max):

    ## Extract stats
    # moving_time: seconds
    # pace: seconds per kilometer
    # distance, distance_longest, elevation_gain: meters
    # average_speed: meters/second

    ## Import or create global variables
    global club_leaderboard

    ## Strava login
    driver = strava_login()


    club_leaderboard = pd.DataFrame(data=[], dtype='object')

    for club_id in club_ids:

        ## Open Strava Club leaderboard page
        driver.get('https://www.strava.com/clubs/'+club_id+'/leaderboard')
        time.sleep(3)


        ## Create new variables

        # club_name
        club_name = driver.find_element(by=By.XPATH, value="//h1[@class='mb-sm']").text.split('\n')[0]

        # club_activity_type
        club_activity_type = driver.find_element(by=By.XPATH, value="//div[@class='club-meta']//div[@class='location']//span[@class='app-icon-wrapper  ']").text

        # club_location
        club_location = driver.find_element(by=By.XPATH, value="//div[@class='club-meta']//div[@class='location']").text
        club_location = re.sub(r'^{club_activity_type}(.*)$'.format(club_activity_type=club_activity_type), r'\1', club_location).strip()


        ## Get this week's Strava Club Leaderboard
        try:
            driver.find_element(by=By.XPATH, value="//div[@class='leaderboard']//h4[@class='empty-results']").text

            club_leaderboard_import = pd.DataFrame(data=[], dtype='object')


        except NoSuchElementException:

            leaderboard_html = driver.find_element(by=By.XPATH, value="//table[@class='dense striped sortable']").get_attribute("outerHTML")

            for d in pd.read_html(leaderboard_html):

                # leaderboard_date_start
                d['leaderboard_date_start'] = datetime.now() + relativedelta.relativedelta(weekday=relativedelta.MO(-1))
                d['leaderboard_date_start'] = d['leaderboard_date_start'].dt.floor('d')

                # leaderboard_date_end
                d['leaderboard_date_end'] = datetime.now() + relativedelta.relativedelta(weekday=relativedelta.MO(-1)) + relativedelta.relativedelta(weekday=relativedelta.SU(+1))
                d['leaderboard_date_end'] = d['leaderboard_date_end'].dt.floor('d')

                # athlete_id
                d['athlete_id'] = lh.fromstring(leaderboard_html).xpath(".//tr//td//div//a//@href")
                d['athlete_id'] = d['athlete_id'].str.extract(r'/athletes/([0-9]+)')


            club_leaderboard_import = d


        ## Get last week's Strava Club Leaderboard
        driver.find_element(by=By.XPATH, value="//span[@class='button last-week']").click()

        try:
            driver.find_element(by=By.XPATH, value="//div[@class='leaderboard']//h4[@class='empty-results']").text

            club_leaderboard_import = pd.DataFrame(data=[], dtype='object')


        except NoSuchElementException:

            leaderboard_html = driver.find_element(by=By.XPATH, value="//table[@class='dense striped sortable']").get_attribute("outerHTML")

            for d in pd.read_html(leaderboard_html):

                # leaderboard_date_start
                d['leaderboard_date_start'] = datetime.now() + relativedelta.relativedelta(weekday=relativedelta.MO(-2))
                d['leaderboard_date_start'] = d['leaderboard_date_start'].dt.floor('d')

                # leaderboard_date_end
                d['leaderboard_date_end'] = datetime.now() + relativedelta.relativedelta(weekday=relativedelta.MO(-2)) + relativedelta.relativedelta(weekday=relativedelta.SU(+1))
                d['leaderboard_date_end'] = d['leaderboard_date_end'].dt.floor('d')

                # athlete_id
                d['athlete_id'] = lh.fromstring(leaderboard_html).xpath(".//tr//td//div//a//@href")
                d['athlete_id'] = d['athlete_id'].str.extract(r'/athletes/([0-9]+)')


        ## Concatenate dataframes
        club_leaderboard_import = pd.concat(objs=[club_leaderboard_import, d], ignore_index=True, sort=False)


        ## Create new variables

        # club_id
        club_leaderboard_import['club_id'] = club_id

        # club_name
        club_leaderboard_import['club_name'] = club_name

        # club_activity_type
        club_leaderboard_import['club_activity_type'] = club_activity_type

        # club_location
        club_leaderboard_import['club_location'] = club_location


        ## Rename columns

        if club_activity_type == 'Cycling':
            club_leaderboard_import = club_leaderboard_import.rename(columns={'Rides': 'activities', 'Longest': 'distance_longest', 'Avg. Speed': 'average_speed'})

        if club_activity_type == 'Running':
            club_leaderboard_import = club_leaderboard_import.rename(columns={'Runs': 'activities', 'Avg. Pace': 'pace'})

        ## Concatenate dataframes
        club_leaderboard = pd.concat(objs=[club_leaderboard, club_leaderboard_import], ignore_index=True, sort=False)



    ## Driver quit
    driver.quit()


    ## Concatenate dataframes
    #club_leaderboard = pd.concat(objs=[club_leaderboard, d], ignore_index=True, sort=False)


    ## Rename columns
    club_leaderboard = club_leaderboard.clean_names()
    club_leaderboard = club_leaderboard.rename(columns={'athlete': 'athlete_name', 'time': 'moving_time', 'elev_gain': 'elevation_gain'})


    ## Create new variables

    # leaderboard_week
    club_leaderboard['leaderboard_week'] = club_leaderboard['leaderboard_date_start'].dt.strftime('%Y-%m-%d')+' to '+club_leaderboard['leaderboard_date_end'].dt.strftime('%Y-%m-%d')


    ## Change dtypes

    # average_speed
    if 'average_speed' in club_leaderboard.columns:
        club_leaderboard['average_speed'] = club_leaderboard['average_speed'].str.replace(r'km/h$', r'', regex=True)
        club_leaderboard['average_speed'] = club_leaderboard['average_speed'].astype(float)
        club_leaderboard['average_speed'] = club_leaderboard['average_speed']/3.6

    else:
        club_leaderboard['average_speed'] = float(np.nan)

    # distance
    club_leaderboard['distance'] = club_leaderboard['distance'].str.replace(r',', r'', regex=True)
    club_leaderboard['distance'] = club_leaderboard['distance'].str.replace(r' km$', r'', regex=True)
    club_leaderboard['distance'] = club_leaderboard['distance'].astype(float)
    club_leaderboard['distance'] = club_leaderboard['distance']*1000

    # distance_longest
    if 'distance_longest' in club_leaderboard.columns:
        club_leaderboard['distance_longest'] = club_leaderboard['distance_longest'].str.replace(r',', r'', regex=True)
        club_leaderboard['distance_longest'] = club_leaderboard['distance_longest'].str.replace(r' km$', r'', regex=True)
        club_leaderboard['distance_longest'] = club_leaderboard['distance_longest'].astype(float)
        club_leaderboard['distance_longest'] = club_leaderboard['distance_longest']*1000

    else:
        club_leaderboard['distance_longest'] = float(np.nan)

    # elevation_gain
    club_leaderboard['elevation_gain'] = club_leaderboard['elevation_gain'].str.replace(r'--', r'0 m', regex=True)
    club_leaderboard['elevation_gain'] = club_leaderboard['elevation_gain'].str.replace(r',', r'', regex=True)
    club_leaderboard['elevation_gain'] = club_leaderboard['elevation_gain'].str.replace(r' m$', r'', regex=True)
    club_leaderboard['elevation_gain'] = club_leaderboard['elevation_gain'].astype(float)

    # moving_time: '%H:%M' to seconds
    if 'moving_time' in club_leaderboard.columns:
        club_leaderboard['moving_time'] = club_leaderboard['moving_time'].fillna('0m')
        club_leaderboard['moving_time'] = club_leaderboard['moving_time'].str.replace(r'^([0-9]+m)$', r'00:\1', regex=True)
        club_leaderboard['moving_time'] = club_leaderboard['moving_time'].str.replace(r'h ', r':', regex=True)
        club_leaderboard['moving_time'] = club_leaderboard['moving_time'].str.replace(r'm$', r'', regex=True)
        club_leaderboard['moving_time'] = pd.to_datetime(club_leaderboard['moving_time'], format='%H:%M').dt.time
        club_leaderboard['moving_time'] = pd.to_timedelta(club_leaderboard['moving_time'].astype(str)).dt.total_seconds()

    else:
        club_leaderboard['moving_time'] = float(np.nan)

    # pace
    if 'pace' in club_leaderboard.columns:

        club_leaderboard['pace'] = club_leaderboard['pace'].astype(str)

        club_leaderboard['pace'] = club_leaderboard['pace'].str.replace(r' /km$', r'', regex=True)
        club_leaderboard['pace'] = club_leaderboard['pace'].apply(lambda x: re.sub(r'^([0-9]+)$', r'00:00:\1', x) if(len(x.split(':')) == 1) else re.sub(r'^(.*)$', r'00:\1', x))

        club_leaderboard['pace'] = pd.to_datetime(club_leaderboard['pace'], format='%H:%M:%S').dt.time
        club_leaderboard['pace'] = pd.to_timedelta(club_leaderboard['pace'].astype(str)).dt.total_seconds()


    ## Rearrange columns
    club_leaderboard = club_leaderboard.filter(['club_id', 'club_name', 'club_activity_type', 'club_location', 'leaderboard_week', 'leaderboard_date_start', 'leaderboard_date_end', 'rank', 'athlete_id', 'athlete_name', 'activities', 'moving_time', 'distance', 'distance_longest', 'average_speed', 'elevation_gain', 'pace'])

    # Filter date interval
    club_leaderboard = club_leaderboard[(club_leaderboard['leaderboard_date_start'] >= parser.parse(filter_date_min)) & (club_leaderboard['leaderboard_date_end'] < (parser.parse(filter_date_max) + timedelta(1)))].reset_index(drop=True)

    ## Rarrange rows
    club_leaderboard = club_leaderboard.sort_values(by=['club_id', 'leaderboard_date_start', 'rank'], ignore_index=True)

    # Return objects
    return club_leaderboard



### strava_club_members
def strava_club_members(club_ids):

    ## Import or create global variables
    global club_members

    ## Strava login
    driver = strava_login()


    data = []

    for club_id in club_ids:

        ## Open Strava Club members page
        driver.get('https://www.strava.com/clubs/'+club_id+'/members')
        time.sleep(3)


        ## Create new variables

        # club_name
        club_name = driver.find_element(by=By.XPATH, value="//h1[@class='mb-sm']").text.split('\n')[0]

        # club_activity_type
        club_activity_type = driver.find_element(by=By.XPATH, value="//div[@class='club-meta']//div[@class='location']//span[@class='app-icon-wrapper  ']").text

        # club_location
        club_location = driver.find_element(by=By.XPATH, value="//div[@class='club-meta']//div[@class='location']").text
        club_location = re.sub(r'^{club_activity_type}(.*)$'.format(club_activity_type=club_activity_type), r'\1', club_location).strip()


        ## Get Strava Club members list
        while True:

            try:

                members = driver.find_elements(by=By.XPATH, value="//ul[@class='list-athletes']//li")

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
                    d['athlete_id'] = member.find_element(by=By.XPATH, value=".//div[@class='text-headline']//a").get_attribute("href")
                    d['athlete_id'] = re.sub(r'^.*/athletes/(.*)$', r'\1', d['athlete_id'])

                    # athlete_name
                    d['athlete_name'] = member.find_element(by=By.XPATH, value=".//div[@class='text-headline']").text

                    # athlete_location
                    d['athlete_location'] = member.find_element(by=By.XPATH, value=".//div[@class='location']").text

                    # athlete_picture
                    d['athlete_picture'] = member.find_element(by=By.XPATH, value=".//img[@class='avatar-img']").get_attribute("src")

                    data.append(d)


                driver.find_element(by=By.XPATH, value=".//li[@class='next_page']").click()

            except NoSuchElementException:
                break


    ## Driver quit
    driver.quit()

    ## Create dataframe
    club_members = pd.DataFrame(data)

    ## Replace blank by NA
    club_members['athlete_location'] = club_members['athlete_location'].replace(r'^$', pd.NA, regex=True)

    ## Drop duplicate rows
    club_members = club_members.drop_duplicates()


    ## Create new variables

    # athlete_location_country, athlete_location_country_code
    club_members['athlete_location_country'] = club_members['athlete_location'].apply(lambda row: Nominatim(user_agent='http').geocode(query=row, language='en', exactly_one=True, addressdetails=True) if pd.notna(row) else pd.NA)

    club_members['athlete_location_country_code'] = club_members['athlete_location_country'].apply(lambda row: row.raw.get('address').get('country_code') if pd.notna(row) else pd.NA)
    club_members['athlete_location_country'] = club_members['athlete_location_country'].apply(lambda row: row.raw.get('address').get('country') if pd.notna(row) else pd.NA)


    # join_date: this assumes that the web-scraping is run every day
    club_members['join_date'] = datetime.now() - timedelta(1)
    club_members['join_date'] = club_members['join_date'].dt.floor('d')


    ## Rearrange columns
    club_members = club_members.filter(['club_id', 'club_name', 'club_location', 'club_activity_type', 'athlete_id', 'athlete_name', 'athlete_location', 'athlete_location_country', 'athlete_location_country_code', 'join_date', 'athlete_picture'])

    ## Rarrange rows
    club_members = club_members.sort_values(by=['club_id', 'athlete_id'], ignore_index=True)

    ## Return objects
    return club_members



### google_api_credentials
def google_api_credentials():

    # credentials
    credentials = Credentials.from_service_account_file(filename=google_api_key, scopes=['https://www.googleapis.com/auth/spreadsheets'])

    # service
    service = build('sheets', 'v4', credentials=credentials)

    ## Return objects
    return service



### strava_club_to_google_sheets
def strava_club_to_google_sheets(df, sheet_id, sheet_name):

    ## Import or create global variables
    global club_members

    ## Google API Credentials
    service = google_api_credentials()

    ## Import dataframe stored in Google Sheets
    result = service.spreadsheets().values().get(spreadsheetId=sheet_id, range=sheet_name).execute()
    df_import = pd.DataFrame(data=result.get('values', []), dtype='object')

    if len(df_import) > 0:

        # Rename columns
        df_import = df_import.rename(columns=df_import.iloc[0])
        df_import = df_import.iloc[1:].reset_index(drop=True)

        ## Change dtypes
        df_import = df_import.replace(r'^\s*$', np.nan, regex=True)

        ## club_activities
        if 'activity_id' in df.columns:
        
            ## Change dtypes
            df_import = df_import.astype(dtype={'elapsed_time': 'float64', 'moving_time': 'float64', 'distance': 'float64', 'max_speed': 'float64', 'average_speed': 'float64', 'elevation_gain': 'float64', 'pace': 'float64', 'calories': 'float64', 'activity_kudos': 'int64'})
            df_import['activity_date'] = df_import['activity_date'].apply(parser.parse)
        
            ## Delete Google Sheets dataframe rows present in club_activities, completely overwriting it
            df_import = df_import.merge(df.filter(['club_id', 'activity_id']).drop_duplicates(), how='outer', on=['club_id', 'activity_id'], indicator=True)
            df_import = df_import.query('_merge=="left_only"')
            df_import = df_import.drop('_merge', axis=1)


        ## club_leaderboard
        if 'leaderboard_week' in df.columns:
            
            ## Change dtypes
            df_import = df_import.astype(dtype={'rank': 'int64', 'activities': 'int64', 'moving_time': 'float64', 'distance': 'float64', 'elevation_gain': 'float64'})
            df_import['leaderboard_date_start'] = df_import['leaderboard_date_start'].apply(parser.parse)
            df_import['leaderboard_date_end'] = df_import['leaderboard_date_end'].apply(parser.parse)
            
            try:
                df_import = df_import.astype(dtype={'distance_longest': 'float64'})
                
            except:
                pass
            
            ## Drop columns
            df_import = df_import.drop(['athlete_location_country_code', 'athlete_picture'], axis=1)
            
            ## Delete Google Sheets dataframe rows present in club_leaderboard, completely overwriting it
            df_import = df_import.merge(df.filter(['club_id', 'leaderboard_week']).drop_duplicates(), how='outer', on=['club_id', 'leaderboard_week'], indicator=True)
            df_import = df_import.query('_merge=="left_only"')
            df_import = df_import.drop('_merge', axis=1)


        ## club_members
        if 'athlete_location' in df.columns:
        
            ## Change dtypes
            df_import['join_date'] = df_import['join_date'].apply(parser.parse)

            ## Keep Google Sheets dataframe rows present in club_members, increment with new club members
            df = df.merge(df_import.filter(['club_id', 'athlete_id']).drop_duplicates(), how='outer', on=['club_id', 'athlete_id'], indicator=True)
            df = df.query('_merge=="left_only"')
            df = df.drop('_merge', axis=1)


    else:
        pass


    ## Concatenate dataframes
    df_updated = pd.concat(objs=[df, df_import], ignore_index=True, sort=False)


    ## club_activities data transform
    if 'activity_id' in df.columns:

        ## Change dtypes
        df_updated['activity_date'] = df_updated['activity_date'].dt.strftime('%Y-%m-%d')
        df_updated.fillna('', inplace=True)

        ## Rarrange rows
        df_updated = df_updated.sort_values(by=['club_id', 'activity_date'], ignore_index=True)


    ## club_leaderboard data transform
    if 'leaderboard_week' in df.columns:

        ## Add 'athlete_location_country_code' and 'athlete_picture' variables
        df_updated = df_updated.merge(club_members.filter(['club_id', 'athlete_id', 'athlete_location_country_code', 'athlete_picture']).drop_duplicates(), how='left', on=['club_id', 'athlete_id'], indicator=False)

        ## Change dtypes
        df_updated['leaderboard_date_start'] = df_updated['leaderboard_date_start'].dt.strftime('%Y-%m-%d')
        df_updated['leaderboard_date_end'] = df_updated['leaderboard_date_end'].dt.strftime('%Y-%m-%d')
        df_updated.fillna('', inplace=True)

        ## Rarrange rows
        df_updated = df_updated.sort_values(by=['club_id', 'leaderboard_date_start', 'rank'], ignore_index=True)


    ## club_members data transform
    if 'athlete_location' in df.columns:

        ## Change dtypes
        df_updated['join_date'] = df_updated['join_date'].dt.strftime('%Y-%m-%d')
        df_updated.fillna('', inplace=True)

        ## Drop columns
        df_updated = df_updated.drop(['athlete_location_country_code', 'athlete_picture'], axis=1)

        ## Rarrange rows
        df_updated = df_updated.sort_values(by=['club_id', 'athlete_id'], ignore_index=True)


    ## Dataframe to list
    data = [df_updated.columns.values.tolist()]
    data.extend(df_updated.values.tolist())

    ## Clear sheet contents
    service.spreadsheets().values().clear(spreadsheetId=sheet_id, range=sheet_name, body={}).execute()

    ## Upload/Overwrite dataframe stored in Google Sheets
    service.spreadsheets().values().update(spreadsheetId=sheet_id, range=sheet_name, valueInputOption='USER_ENTERED', body={"values":data}).execute()



### execution_time_to_google_sheets
def execution_time_to_google_sheets(sheet_id, sheet_name):

    ## Google API Credentials
    service = google_api_credentials()

    ## Clear sheet contents
    service.spreadsheets().values().clear(spreadsheetId=sheet_id, range=sheet_name, body={}).execute()

    ## Upload/Overwrite dataframe stored in Google Sheets
    service.spreadsheets().values().update(spreadsheetId=sheet_id, range=sheet_name, valueInputOption='USER_ENTERED', body={"values":[['last_execution'], [str(datetime.now().replace(microsecond=0))]]}).execute()




##########################################
# ---- strava-club-activities-scraper ----
##########################################

## Club activities

# Get data (via web-scraping)
strava_club_activities(club_ids=club_ids, filter_activities_type=filter_activities_type, filter_date_min=filter_date_min, filter_date_max=filter_date_max)

# Save as .csv
# club_activities.to_csv(path_or_buf='club_activities.csv', sep=',', index=False, encoding='utf8')

# Update Google Sheets sheet
strava_club_to_google_sheets(df=club_activities, sheet_id=sheet_id, sheet_name='Activities')

# Export club activities to .gpx files
# strava_export_gpx(activities=club_activities['activity_id'])



## Club members

# Get data (via web-scraping)
strava_club_members(club_ids=club_ids)

# Update Google Sheets sheet
strava_club_to_google_sheets(df=club_members, sheet_id=sheet_id, sheet_name='Members')



## Club leaderboard

# Get data (via web-scraping)
strava_club_leaderboard(club_ids=club_ids, filter_date_min=filter_date_min, filter_date_max=filter_date_max)

# Update Google Sheets sheet
strava_club_to_google_sheets(df=club_leaderboard, sheet_id=sheet_id, sheet_name='Leaderboard')



## Store execution time in Google Sheets

# Update Google Sheets sheet
execution_time_to_google_sheets(sheet_id=sheet_id, sheet_name='Execution Time')
