#!/usr/bin/env python3
"""Module to create html page of data from Strava web scraper"""

import json
from datetime import datetime

# Configuration of global variables
FILE_PATH = 'results.html'

# Load the JSON content from the file
with open('results.json', 'r') as json_file:
    data = json.load(json_file)


def get_current_week_number():
    """Function to translate weekday to week number"""
    week_number = datetime.now().strftime('%G-W%V')
    return week_number.split('-W')[1]


def format_duration(duration_minutes):
    hours = int(duration_minutes/60)
    return hours



# Create a dictionary to store the accumulated data for each athlete
athlete_summary = {}

# Accumulate data for each athlete across all weeks
for key, value in data.items():
    athlete_name = value["athlete_name"]

    if athlete_name not in athlete_summary:
        athlete_summary[athlete_name] = {
            'activities': 0,
            'distance': 0,
            'moving_time': 0,
            'elevation_gain': 0
        }

    athlete_summary[athlete_name]['activities'] += value['activities']
    athlete_summary[athlete_name]['distance'] += value['distance']
    athlete_summary[athlete_name]['moving_time'] += value['moving_time']
    athlete_summary[athlete_name]['elevation_gain'] += value['elevation_gain']

# Create HTML tables for each section
ukens_resultater_table = "<table border='1'>\
                         <tr><th>Navn</th>\
                         <th>Antall aktiviteter</th>\
                         <th>Varighet (timer)</th>\
                         <th>Distanse (km)</th>\
                         <th>Høydemeter</th></tr>"

for key, value in data.items():
    if int(value["week_number"]) == int(get_current_week_number()):
        ukens_resultater_table += (
            f"<tr><td>{value['athlete_name']}</td>"
            f"<td>{value['activities']}</td>"
            f"<td>{format_duration(value['moving_time'])}</td>"
            f"<td>{value['distance']}</td>"
            f"<td>{value['elevation_gain']}</td></tr>"
        )
ukens_resultater_table += "</table>"

forrige_ukes_resultater_table = "<table border='1'>\
                                <tr><th>Navn</th>\
                                <th>Antall aktiviteter</th>\
                                <th>Varighet (timer)</th>\
                                <th>Distanse (km)</th>\
                                <th>Høydemeter</th></tr>"

for key, value in data.items():
    if int(value["week_number"]) == int(get_current_week_number())-1:
        forrige_ukes_resultater_table += (
            f"<tr><td>{value['athlete_name']}</td>"
            f"<td>{value['activities']}</td>"
            f"<td>{format_duration(value['moving_time'])}</td>"
            f"<td>{value['distance']}</td>"
            f"<td>{value['elevation_gain']}</td></tr>"
        )
forrige_ukes_resultater_table += "</table>"

resultater_hele_perioden_table = "<table border='1'>\
                                 <tr><th>Navn</th>\
                                 <th>Antall aktiviteter</th>\
                                 <th>Varighet (timer)</th>\
                                 <th>Distanse (km)</th>\
                                 <th>Høydemeter</th></tr>"

for athlete_name, summary_data in athlete_summary.items():
    resultater_hele_perioden_table += (
        f"<tr><td>{athlete_name}</td>"
        f"<td>{summary_data['activities']}</td>"
        f"<td>{format_duration(summary_data['moving_time'])}</td>"
        f"<td>{summary_data['distance']}</td>"
        f"<td>{summary_data['elevation_gain']}</td></tr>"
    )
resultater_hele_perioden_table += "</table>"

# HTML content with the summarized table
html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>My HTML Page</title>
</head>
<body>
    <section id="ukens_resultater">
        <h2>Ukens resultater (uke {int(get_current_week_number())})</h2>
        {ukens_resultater_table}
    </section>

    <section id="forrige_ukes_resultater">
        <h2>Forrige ukes resultater (uke {int(get_current_week_number())-1})</h2>
        {forrige_ukes_resultater_table}
    </section>

    <section id="resultater_hele_perioden">
        <h2>Resultater hele perioden</h2>
        {resultater_hele_perioden_table}
    </section>
</body>
</html>
"""



# Write the HTML content to the file
with open(FILE_PATH, 'w', encoding='utf-8') as html_file:
    html_file.write(html_content)

print(f"HTML file created at: {FILE_PATH}")
