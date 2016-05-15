# Crawls event venue data from https://seatgeek.com.

import sys
import math
import json
import time
import requests

# API endpoint
url_format = "https://api.seatgeek.com/2/venues?city=New%20York&client_id={client_id}&page={page}&per_page=5000"

# Check number of arguments
if len(sys.argv) != 2:
  print("Usage: %s <output_file>" % sys.argv[0])
  sys.exit(1)

# Parse arguments
output_file = sys.argv[1]

# Read client id
with open("SEATGEEK_CLIENT_ID", "r") as file:
  client_id = file.readline()

# Crawl venue data page by page
current_page = 1
venues = []
total_venues_count = math.inf
tries = 1
while len(venues) < total_venues_count:
  url = url_format.format(client_id=client_id, page=current_page)
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
  venues += response_obj['venues']
  total_venues_count = response_obj["meta"]["total"]
  current_page += 1

  sys.stdout.write("\rCrawling venues data ({0}/{1})".format(len(venues), total_venues_count))

# Write event data to file
with open(output_file, 'w') as file:
  file.write(json.dumps(venues))
