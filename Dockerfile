## Dockerfile Strava Club Scraper
# Last update: 2023-05-30


# Base image
FROM python:latest


# Set working directory
WORKDIR /


# Debian - Install packages
RUN apt-get update && apt-get install -y \
    chromium \
    cron


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
