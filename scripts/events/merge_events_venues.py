# Merges crawled event and venue data.
# Merging is done by mapping the geolocations of event addresses obtained from Google Maps to the closest venues.

import sys
import math
import json
import time
import requests
import numpy as np
from scipy.spatial import cKDTree
from geopy.distance import vincenty

# Google Maps geocoding API endpoint
url = "https://maps.googleapis.com/maps/api/geocode/json?address={0}"

geocode_requests_count = 0
def geocode(query, retries=0):
  global geocode_requests_count

  response = requests.get(url.format(query))

  geocode_requests_count += 1
  if geocode_requests_count % 10 == 0:
    time.sleep(1)

  if response.ok:
    response = json.loads(response.text)
    if "results" in response and response["results"]:
      return response["results"][0]["geometry"]["location"]
    elif "error_message" in response:
      if retries < 3:
        sys.stdout.write("You have exceeded your daily request quota. Renew your ip and press enter.")
        sys.stdin.read(1)
        return geocode(query, retries + 1)
  else:
    print("\nError {} while geocoding!".format(response.status_code))


def isfloat(value):
  try:
    float(value)
    return True
  except ValueError:
    return False


# Check number of arguments
if len(sys.argv) != 4:
  print("Usage: %s <event_file> <venue_file> <output_file>" % sys.argv[0])
  sys.exit(1)

# Parse arguments
event_file = sys.argv[1]
venue_file = sys.argv[2]
output_file = sys.argv[3]

# Load files as json
print("Load events from file...")
with open(event_file, "r") as file:
  events = json.load(file)

print("Load venues from file...")
with open(venue_file, "r") as file:
  venues = json.load(file)

# Group events by address
grouped_events = {}
for event in events:
  if ("geometry" not in event or not event["geometry"]) and "address" in event:
    address = event["address"]
    if address in grouped_events:
      grouped_events[address].append(event)
    else:
      grouped_events[address] = [event]


# Add missing coordinates to events
progress_count = 0
for address, event_group in grouped_events.items():
  progress_count += 1
  sys.stdout.write("\rGeocode addresses ({0}/{1})...".format(progress_count, len(grouped_events)))

  location = geocode(address)
  if location:
    for event in event_group:
      event["geometry"] = [location]
print()

# Group events by coordinates
grouped_events = {}
for event in events:
  if "geometry" in event and event["geometry"]:
    coords = (event["geometry"][0]["lat"], event["geometry"][0]["lng"])
    if coords in grouped_events:
      grouped_events[coords].append(event)
    else:
      grouped_events[coords] = [event]

# Map events with coordinates to venues
progress_count = 0
coordinate_venues = [venue for venue in venues if "location" in venue and venue["location"]]
coordinates = np.array([(venue["location"]["lat"], venue["location"]["lon"]) for venue in coordinate_venues])
tree = cKDTree(coordinates)
for event_coords, event_group in grouped_events.items():
  progress_count += 1
  sys.stdout.write("\rMap events to nearest venue ({0}/{1})...".format(progress_count, len(grouped_events)))

  if isfloat(event_coords[0]) and isfloat(event_coords[1]):
    min_distance, venue_index = tree.query(event_coords)
    if vincenty(event_coords, coordinates[venue_index]).meters < 50:
      for event in event_group:
        event["venue"] = coordinate_venues[venue_index]
print()

# Write results to file
print("Write results to file...")
with open(output_file, "w") as file:
  json.dump(events, file)
