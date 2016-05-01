# Given a directory of taxi data, create <year>_sample.csv files that contains
# 1% of the original tuples.
# Expacts files to be named yellow_tripdata_<year>-<month>.csv

import sys
import os
import random

KEEP_FRACTION = 0.01
YEARS = [2009, 2010, 2011, 2012, 2013, 2014, 2015]

if not len(sys.argv) > 1:
  print "Usage: %s <data_dir>" % sys.argv[0]

data_dir = sys.argv[1]
files = [f for f in os.listdir(data_dir) if not f.startswith(".")]

for year in YEARS:
  first = True
  with open(os.path.join(data_dir, "%d_sample.csv" % year), "w") as sample_file:

    for month in range(1, 13):
      fname = "yellow_tripdata_%d-%02d.csv" % (year, month)
      print "File:", fname

      with open(os.path.join(data_dir, fname)) as original_file:
        for line in original_file:

          if first:
            # Write header
            sample_file.write(line)
            first = False

          if random.random() < KEEP_FRACTION:
            sample_file.write(line)
