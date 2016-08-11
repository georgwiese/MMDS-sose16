# Given a CSV, samples a specified fraction of rows

import sys
import random

if not len(sys.argv) > 3:
  print "Usage: %s <input_csv> <ouput_filename> <percentage>" % sys.argv[0]

[input_csv, ouput_filename, percentage] = sys.argv[1:]
percentage = float(percentage)


first = True
with open(ouput_filename, "w") as ouput_file:
  with open(input_csv) as input_file:
    for line in input_file:

      if first:
        ouput_file.write(line)
        first = False
        continue

      if random.random() < percentage / 100.0:
        ouput_file.write(line)
