# Strava Club Reports
# Last update: 2022-05-16


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

from dateutil import parser
import janitor
import numpy as np
import pandas as pd
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager


## Set working directory to user's 'Downloads' folder
os.chdir(os.path.join(os.path.expanduser('~'), 'Downloads'))


## Settings
strava_email = 'email@gmail.com'
strava_password = 'Password12345'



#####################
# ---- functions ----
#####################

### convert_list_to_dictionary
def convert_list_to_dictionary(list):
    list = iter(list)
    dictionary = dict(zip(list, list))
    return dictionary


### selenium_webdriver
def selenium_webdriver():

    # Webdriver options
    chrome_options = webdriver.ChromeOptions()
    chrome_options.page_load_strategy = 'normal'

    # Webdriver download settings
    chrome_options.add_experimental_option('prefs', {
        'download.default_directory': os.path.join(os.path.join(os.getcwd())),
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

    return driver


### strava_login
def strava_login():

    # Load Selenium webdriver
    driver = selenium_webdriver()

    ## Open website
    driver.get('https://www.strava.com/login')
    time.sleep(2)

    # Reject cookies
    driver.find_element(by=By.XPATH, value=".//button[@class='btn-deny-cookie-banner']").click()

    # Login
    driver.find_element_by_id('email').send_keys(strava_email)
    driver.find_element_by_id('password').send_keys(strava_password)
    time.sleep(2)

    driver.find_element(by=By.XPATH, value=".//*[@type='submit']").submit()

    return driver


### strava_club_activities_scraper
def strava_club_activities_scraper(club_id, filter_activities_type, filter_date_min, filter_date_max):

    # Import or create global variables
    global activities

    # Strava login
    driver = strava_login()

    # Open Strava Club feed page
    driver.get('https://www.strava.com/dashboard?club_id='+club_id+'&feed_type=club&num_entries=100')
    time.sleep(3)

    # Scroll to the end of the webpage
    while True:

        try:
            driver.find_element(by=By.XPATH, value="//div[@class='Feed--feed-pagination--yh121 Feed--no-entries--ARKOk']")
            break

        except NoSuchElementException:

            activities = driver.find_elements(by=By.XPATH, value="//div[@data-testid='activity_entry_container']")
            activity_date = activities[-1].find_element(by=By.XPATH, value=".//..//..//..//..//..//time").text
            activity_date = re.sub(r'^(Today at )(.*)$', datetime.now().strftime('%Y-%m-%d')+r' \2', activity_date)
            activity_date = re.sub(r'^(Yesterday at )(.*)$', (datetime.now() - timedelta(1)).strftime('%Y-%m-%d')+r' \2', activity_date)
            activity_date = parser.parse(activity_date)

            if activity_date > parser.parse(filter_date_min):

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
        activity_date = re.sub(r'^(Today at )(.*)$', datetime.now().strftime('%Y-%m-%d')+r' \2', activity_date)
        activity_date = re.sub(r'^(Yesterday at )(.*)$', (datetime.now() - timedelta(1)).strftime('%Y-%m-%d')+r' \2', activity_date)
        activity_date = parser.parse(activity_date)

        if parser.parse(filter_date_min) <= activity_date < (parser.parse(filter_date_max)+timedelta(days=1)):

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


    ## Extract stats
    # elapsed_time, moving_time: seconds
    # pace: seconds per kilometer
    # distance, elevation_gain: meters
    # max_speed, average_speed: meters/second
    # temperature: degree Celsius

    data = []

    for activity in activities_id:

        d = {}

        driver.get('https://www.strava.com/activities/'+activity)

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
            d['activity_location'] = driver.find_element(by=By.XPATH, value=".//div[@class='details-container']//span[@class='location']").text

            # Inline stats
            inline_stats = driver.find_element(by=By.XPATH, value=".//ul[@class='inline-stats section']").text.split('\n')
            inline_stats = convert_list_to_dictionary(inline_stats)
            inline_stats = {value: name for name, value in inline_stats.items()}

            for item, value in inline_stats.items():
                d[item] = value

                # distance
                try:
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
                        d['Moving Time'] = re.sub(r's$', r'', d['Moving Time'])
                        d['Moving Time'] = time.strptime(d['Moving Time'], '%S')
                        d['Moving Time'] = d['Moving Time'].tm_sec

                    if len(d['Moving Time'].split(':')) == 2:
                        d['Moving Time'] = time.strptime(d['Moving Time'], '%M:%S')
                        d['Moving Time'] = d['Moving Time'].tm_min*60 + d['Moving Time'].tm_sec

                    if len(d['Moving Time'].split(':')) == 3:
                        d['Moving Time'] = time.strptime(d['Moving Time'], '%H:%M:%S')
                        d['Moving Time'] = d['Moving Time'].tm_hour*60*60 + d['Moving Time'].tm_min*60 + d['Moving Time'].tm_sec

                except:
                    pass

                # pace
                try:

                    d['Pace'] = re.sub(r'/km', r'', d['Pace'])

                    if len(d['Pace'].split(':')) == 1:
                        d['Pace'] = time.strptime(d['Pace'], '%S')
                        d['Pace'] = d['Pace'].tm_sec

                    if len(d['Pace'].split(':')) == 2:
                        d['Pace'] = time.strptime(d['Pace'], '%M:%S')
                        d['Pace'] = d['Pace'].tm_min*60 + d['Pace'].tm_sec

                    if len(d['Pace'].split(':')) == 3:
                        d['Pace'] = time.strptime(d['Pace'], '%H:%M:%S')
                        d['Pace'] = d['Pace'].tm_hour*60*60 + d['Pace'].tm_min*60 + d['Pace'].tm_sec

                except:
                    pass


            # More stats
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
                        d['Elapsed Time'] = re.sub(r's$', r'', d['Elapsed Time'])
                        d['Elapsed Time'] = time.strptime(d['Elapsed Time'], '%S')
                        d['Elapsed Time'] = d['Elapsed Time'].tm_sec

                    if len(d['Elapsed Time'].split(':')) == 2:
                        d['Elapsed Time'] = time.strptime(d['Elapsed Time'], '%M:%S')
                        d['Elapsed Time'] = d['Elapsed Time'].tm_min*60 + d['Elapsed Time'].tm_sec

                    if len(d['Elapsed Time'].split(':')) == 3:
                        d['Elapsed Time'] = time.strptime(d['Elapsed Time'], '%H:%M:%S')
                        d['Elapsed Time'] = d['Elapsed Time'].tm_hour*60*60 + d['Elapsed Time'].tm_min*60 + d['Elapsed Time'].tm_sec

                except:
                    pass

                # temperature
                try:

                    d['Temperature'] = re.sub(r'^([0-9]+).*', r'\1', d['Temperature'])
                    d['Temperature'] = float(d['Temperature'])


                except:
                    pass

            # activity_device
            d['activity_device'] = driver.find_element(by=By.XPATH, value=".//div[@class='section device-section']//div[@class='device spans8']").text

            # activity_gear
            if d['activity_type'] in filter_activities_type:

                try:
                    d['activity_gear'] = driver.find_element(by=By.XPATH, value=".//div[@class='section device-section']//span[@class='gear-name']").text
                    d['activity_gear'] = re.sub(u'\u2014', 'NaN', d['activity_gear'])

                except:
                    pass

            # activity_kudos
            d['activity_kudos'] = driver.find_element(by=By.XPATH, value=".//span[@class='count']").get_attribute("data-count")
            d['activity_kudos'] = int(d['activity_kudos'])

            data.append(d)

        else:
            pass


    # Driver quit
    driver.quit()

    # Create dataframe
    activities = pd.DataFrame(data)
    activities = activities.clean_names()
    activities = activities.rename(columns={'elevation': 'elevation_gain'})

    # Rearrange columns
    activities = activities.filter(['activity_date', 'athlete_id', 'athlete_name', 'activity_type', 'activity_id', 'activity_name', 'activity_description', 'activity_location','activity_gear', 'elapsed_time', 'moving_time', 'distance', 'max_speed', 'average_speed', 'elevation_gain', 'pace', 'calories', 'activity_device', 'temperature', 'activity_kudos'])

    # Filter activity types
    activities = activities[activities['activity_type'].isin(filter_activities_type)]

    # Filter date interval
    activities = activities[(activities['activity_date'] >= (pd.Timestamp(filter_date_min))) & (activities['activity_date'] < (pd.Timestamp(filter_date_max)))].reset_index(drop=True)

    # Rarrange rows
    activities = activities.sort_values(by=['activity_date'], ignore_index=True)

    return activities


### Export .gpx files
def strava_export_gpx(activities):

    # Strava login
    driver = strava_login()

    for activity in activities:
        driver.get('https://www.strava.com/activities/'+activity+'/export_gpx')

    # Driver quit
    driver.quit()



##########################################
# ---- strava-club-activities-scraper ----
##########################################

# strava_club_activities_scraper
strava_club_activities_scraper(club_id='12345', filter_activities_type=['Ride', 'Run'], filter_date_min='2022-04-01', filter_date_max='2022-05-31')

# Save as .csv
activities.to_csv(path_or_buf='activities.csv', sep=',', index=False, encoding='utf8')

# strava_export_gpx
strava_export_gpx(activities=activities['activity_id'])
