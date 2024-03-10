#!/usr/bin/env python3
"""Module to create html page of data from Strava web scraper"""

import json
import os
from datetime import datetime

# Configuration of global variables
FILE_PATH = 'web/results.html'  # CHANGE BEFORE PUSHING TO REMOTE, FOR DEBUG
# FILE_PATH = 'results.html' # CHANGE BEFORE PUSHING TO REMOTE, FOR DEBUG

directory = 'web'
if not os.path.isdir(directory):
    os.mkdir(directory)

# Load the JSON content from the file

with open('data/result/results.json', 'r') as json_file:
    data = json.load(json_file)


def get_current_week_number():
    """Function to translate weekday to week number"""
    week_number = datetime.now().strftime('%G-W%V')
    return week_number.split('-W')[1]


def format_duration(duration_minutes):
    hours = int((duration_minutes/60)/60)
    return hours


def format_distance(distance):
    km = float(distance/1000)
    return km


def get_ranking():
    ranking_current_week = []
    ranking_previous_week = []
    rankings = {}
    
    for value in data.values():

        if value["week_number"] == int(get_current_week_number()):
            ranking_current_week.append(value["athlete_name"])

        if value["week_number"] == int(get_current_week_number())-1:
            ranking_previous_week.append(value["athlete_name"])
    
    for value in data.values():
        if value["athlete_name"] in ranking_current_week and value["athlete_name"] in ranking_previous_week:
            current_rank = ranking_current_week.index(value["athlete_name"])
            previous_rank = ranking_previous_week.index(value["athlete_name"])

            if current_rank < previous_rank:
                rankings.update({value["athlete_name"]: "🔺"})
            elif current_rank > previous_rank:
                rankings.update({value["athlete_name"]: "🔻"})
            elif current_rank == previous_rank:
                rankings.update({value["athlete_name"]: "⏩"})
        else:
            rankings.update({value["athlete_name"]: "⭐"})

    return rankings

rankings = get_ranking()
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

# Create HTML tables for each section - note, this way of doing this creates whitespace in html
ukens_resultater_table = "<table class='table'>\
                         <tr><th>Navn</th>\
                         <th>Antall aktiviteter</th>\
                         <th>Varighet (timer)</th>\
                         <th>Distanse (km)</th>\
                         <th>Høydemeter</th></tr>"

for key, value in data.items():
    if int(value["week_number"]) == int(get_current_week_number()):
        ukens_resultater_table += (
            f"<tr><td>{rankings[value['athlete_name']]} {value['athlete_name']}</td>"
            f"<td>{value['activities']}</td>"
            f"<td>{format_duration(value['moving_time'])}</td>"
            f"<td>{format_distance(value['distance'])}</td>"
            f"<td>{value['elevation_gain']}</td></tr>"
        )
ukens_resultater_table += "</table>"

forrige_ukes_resultater_table = "<table class='table'>\
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
            f"<td>{format_distance(value['distance'])}</td>"
            f"<td>{value['elevation_gain']}</td></tr>"
        )
forrige_ukes_resultater_table += "</table>"

resultater_hele_perioden_table = "<table class='table'>\
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
        f"<td>{format_distance(summary_data['distance'])}</td>"
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
    <link rel="stylesheet" href="static/styles.css">
    <title>Tittel</title>
</head>
<body>
    <div class="page-wrapper">
        <div class="header" id="header">
            <h1 class=>Tittel</h1>
        </div>
        <div class="tile" id="Aggregrerte data">
            <h2>Placeholder aggregerte data</h2>
            Siste ukes vinner, totalt tid, distanse, høydemeter, co2?
        </div>
        <div class="tile" id="ukens_resultater">
            <h2>Ukens resultater (uke {int(get_current_week_number())})</h2>
            {ukens_resultater_table}
        </div>

        <div class="tile" id="forrige_ukes_resultater">
            <h2>Forrige ukes resultater (uke {int(get_current_week_number())-1})</h2>
            {forrige_ukes_resultater_table}
        </div>

        <div class="tile" id="resultater_hele_perioden">
            <h2>Resultater hele perioden</h2>
            {resultater_hele_perioden_table}
        </div>
    </div>
</body>
</html>
"""



# Write the HTML content to the file
with open(FILE_PATH, 'w', encoding='utf-8') as html_file:
    html_file.write(html_content)

print(f"HTML file created at: {FILE_PATH}")
