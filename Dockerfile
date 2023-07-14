## Dockerfile Strava Club Scraper
# Last update: 2023-07-05


# Base image
FROM python:latest


# Set working directory
WORKDIR /


# Debian - Install packages
RUN apt-get update && apt-get install -y \
    cron \
	wget


# Install Google Chrome
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add -
RUN sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list'
RUN apt-get -y update && apt-get install -y \
	google-chrome-stable


# Python - Install dependencies
RUN python -m pip install --upgrade pip
RUN python -m pip install python-dateutil geopy google-api-python-client google-auth lxml numpy pandas selenium webdriver-manager


# Python - Get Python pathway
RUN which python


# Copy all files to the container
COPY . .


# Create 'crontab-scheduler' configuration file
RUN echo "00 10 * * * cd / && /usr/local/bin/python strava-club-scraper.py 2>&1" >> crontab-scheduler
RUN echo "00 17 * * * cd / && /usr/local/bin/python strava-club-scraper.py 2>&1" >> crontab-scheduler
RUN echo "30 21 * * * cd / && /usr/local/bin/python strava-club-scraper.py 2>&1" >> crontab-scheduler
# RUN echo "30 20 * * 1,4 cd / && /usr/local/bin/python strava-club-scraper-activities.py 2>&1" >> crontab-scheduler


# Copy 'crontab-scheduler' configuration file to '/etc/cron.d/'
COPY crontab-scheduler /etc/cron.d/crontab-scheduler


# List all directories and files (in a Linux container)
RUN dir -s


# Run the Python code once while building the container
RUN /usr/local/bin/python strava-club-scraper.py


# Apply cron job given crontab-scheduler configuration file
RUN crontab crontab-scheduler


# Command to execute cron job on container startup
CMD ["cron", "-f"]
