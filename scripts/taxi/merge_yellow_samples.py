# Merges data/yello_samples/<year>_sample.csv files into one
# data/yellow_sample.csv file by concatenating them and only keeping relevant
# columns.

import random

YEARS = [2009, 2010, 2011, 2012, 2013, 2014, 2015]
INPUT_FILE_PATTERN = "data/yellow_samples/%d_sample.csv"
OUTPUT_FILENAME = "data/yellow_sample.csv"

# Even though columns are named differently, the column indices of the ones
# we're interested in are consistent across years
COLUMN_INDICES = [
  1,  # Pickup time
  2,  # Dropoff time
  3,  # Passenger Count
  4,  # Trip Distance
  5,  # Start Lon
  6,  # Start Lat
  9,  # End Lon
  10  # End Lat
]

def filter_columns(line, column_indices):
  cells = line.split(",")
  filtered_cells = [cells[index] for index in column_indices]
  return ",".join(filtered_cells)

with open(OUTPUT_FILENAME, "w") as output_file:
  first_file = True

  for year in YEARS:
    print "Year:", year

    with open(INPUT_FILE_PATTERN % year) as sample_file:

      first_line = True

      for l in sample_file:

        line = l.strip()

        if first_line:
          if first_file:
            # Write header
            output_file.write(filter_columns(line, COLUMN_INDICES) + "\n")
            first_file = False
          first_line = False
          continue

        if line:
          output_line = filter_columns(line, COLUMN_INDICES)
          if random.random() < 0.00001:
            print output_line
          output_file.write(output_line + "\n")
