# parses the json file obtained by merge_events_venues.py to a csv file
# parameters: jsonInputFile, csvOutputFile

import sys
import csv
import json

# Check number of arguments
if len(sys.argv) != 3:
  print("Usage: %s <json_file> <output_file>" % sys.argv[0])
  sys.exit(1)

# Parse arguments
input_file = sys.argv[1]
output_file = sys.argv[2]

with open(input_file, "r") as file:
  events = json.load(file)

with open(output_file, "w") as file:
  csv_writer = csv.writer(file, delimiter=',')
  csv_writer.writerow(["id", "guid", "start_date", "end_date", "all_day", "score", "latitude", "longitude"])

  for event in events:
    if not event.get("canceled", False) and "geometry" in event and event["geometry"]:
      id = event["id"]
      guid = event["guid"]
      start_date = event["startDate"]
      end_date = event.get("startDate")
      all_day = event["allDay"]
      score = -1
      if "venue" in event:
        score = event["venue"].get("score")
      latitude = event["geometry"][0]["lat"]
      longitude = event["geometry"][0]["lng"]

      csv_writer.writerow([id, guid, start_date, end_date, all_day, score, latitude, longitude])
