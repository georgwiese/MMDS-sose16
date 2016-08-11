# Crawls event data from http://www.nyc.gov/events for the given time span
# The url_format given below allows accessing all events in the given time span arranged on pages.
#
# parameters: <start_date> <end_date> <output_file>
#             date format:   month/day/year hour(0-11):minutes period(AM/PM)

import sys
import math
import json
import time
import requests
from dateutil import parser

# API endpoint
url_format = "http://www1.nyc.gov/calendar/api/json/search.htm?&sort=DATE&startDate={start_date}&endDate={end_date}&pageNumber={page}"

# Check number of arguments
if len(sys.argv) != 4:
  print("Usage: %s <start_date> <end_date> <output_file> " % sys.argv[0])
  sys.exit(1)

# Parse arguments
try:
  start_date = parser.parse(sys.argv[1]).strftime("%m/%d/%Y %I:%M %p")
  end_date = parser.parse(sys.argv[2]).strftime("%m/%d/%Y %I:%M %p")
except ValueError:
  print("Invalid date format, use: month/day/year hour(0-11):minutes period(AM/PM)")
  sys.exit(1)
output_file = sys.argv[3]

# Crawl event data page by page
current_page = 1
last_page = math.inf
events = []
tries = 1
while current_page <= last_page:
  sys.stdout.write("\rCrawling event data ({0}/{1} pages)".format(current_page, last_page))

  url = url_format.format(start_date=start_date, end_date=end_date, page=current_page)
  response = requests.get(url)
  if not response.ok:
    if tries >= 10:
      print(" => skip page because of http error {0}".format(response.status_code))
      tries = 0
      current_page += 1
    else:
      time.sleep(1)
    tries += 1
    continue

  response_obj = json.loads(response.text)
  events += response_obj['items']
  last_page = response_obj["pagination"]["numPages"]
  current_page += 1

# Write event data to file
with open(output_file, 'w') as file:
  file.write(json.dumps(events))
