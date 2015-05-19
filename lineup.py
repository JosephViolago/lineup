from bs4 import BeautifulSoup

import requests

from time import *
from datetime import datetime, date, time, timedelta

from collections import defaultdict

import re
import sys

import json

import pprint

base = 'http://www.mysteryland.us'
path = '/en/line-up/detailed-lineup/schedule'

r = requests.get(base + path)

# Try/catch
print(r.status_code)

data = r.text
soup = BeautifulSoup(data)

events = {}

today      = date.today()
start_day  = datetime(today.year, 5, 22)
event_meta = {
    'day': {
        '4': start_day,
        '5': start_day + timedelta(1),
        '6': start_day + timedelta(2),
    },
}

time_re = '^([0-9]{1,2}):00 (AM|PM)$'

for data_day in soup.find_all('div', {'class': 'schedule-container'}):
    day                       = data_day.get('data-day')
    events[day]               = defaultdict(list)
    event_meta[day]           = defaultdict(list)
    event_meta[day]['venues'] += []

    for day_venue in data_day.find_all('div', {'class': 'schedule-area'}):
        for data_venue in day_venue.find_all('span'):
            venue = data_venue.get_text()
            event_meta[day]['venues'].append(venue)

    first_hour = data_day.find('div', {'class': 'schedule-time'}).find('li').get_text()
    matches    = re.search(time_re, first_hour)
    start_hour = int(matches.group(1))
    start_hour += 12 if start_hour != 12 and matches.group(2) == 'PM' else 0

    i = 0

    for day_venue_row in data_day.find_all('div', {'class': 'schedule-row'}):
        venue = event_meta[day]['venues'][i]
        events[day][venue] += []

        start_time = timedelta(hours=start_hour)
        end_time   = start_time

        for event in day_venue_row.find_all(None, {'class': 'schedule-item'}):
            event_details = {
                'day'      : event_meta['day'][event.get('data-day')],
                'duration' : event.get('data-schedule-duration'), # minutes
                'info'     : event.get('href'),
                'name'     : event.get_text().strip(),
                'venue'    : event.get('data-area'),
            }

            # Slow
            # if event_details['info'] is not None:
            #     r_info = requests.get(base + event_details['info'])
            #     # print(r_info.status_code)

            #     info_data = r.text
            #     info_soup = BeautifulSoup(info_data)

            #     event_blurb = info_soup.find('div', {'classs': 'mb'})

            #     if event_blurb is not None:
            #         event_details.update({'info', event_blurb.get_text})

            end_time += timedelta(minutes=int(event_details['duration']))
            event_details.update({'start': str(event_details['day'] + start_time)})
            event_details.update({'end': str(event_details['day'] + end_time)})
            event_details.update({'day': str(event_meta['day'][event.get('data-day')])})
            start_time = end_time

            if event.get('class')[1] == 'schedule--artist':
                event_details.pop('day', None)
                event_details.pop('duration', None)
                events[day][venue].append(event_details)

        i += 1

    # print("\n")

# pprint.pprint(events)

events_json = json.dumps(events, sort_keys=True, indent=4, separators=(',', ': '))
print events_json


