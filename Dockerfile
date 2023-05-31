## Dockerfile Strava Club Scraper
# Last update: 2023-05-31


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


# Python - Update pip
RUN python -m pip install --upgrade pip


# Python - Install packages
RUN python -m pip install python-dateutil geopy google-api-python-client google-auth lxml numpy pandas pyjanitor selenium webdriver-manager


# Python - Get Python pathway
RUN which python


# Copy all files to the container
COPY . .


# List all directories and files (in a Linux container)
RUN dir -s


# Run the Python code once while building the container
RUN /usr/local/bin/python strava-club-scraper.py


# Apply cron job given crontab scheduler configuration file
RUN crontab crontab-scheduler


# Command to execute cron job on container startup
CMD ["cron", "-f"]
