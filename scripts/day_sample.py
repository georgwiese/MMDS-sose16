# Given a CSV which contains a specific year, this script filters a specific day or range of days

import sys

if not len(sys.argv) > 3:
  print "Usage: %s <input_csv> <startDate> <endDate> Example: ../../yellow_tripdata_2012-10.csv 2012-10-29 2012-10-29" % sys.argv[0]
  print "code runs with given example now"
  input_csv = '../../yellow_tripdata_2013-10.csv'
  startDate = '2013-10-28'
  endDate = '2013-10-28'
  output_filename = '../../yellow_tripdata_' + startDate + '_' + endDate + '.csv'

else: [input_csv, startDate, endDate] = sys.argv[1:]




first = True
rangeStarted = False
endDateReached = False
with open(output_filename, "w") as output_file:
  with open(input_csv) as input_file:
    for line in input_file:

      if first:
        output_file.write(line)
        first = False
        continue

      if not rangeStarted and line.__contains__(startDate):
        if line.split(",")[1].__contains__(startDate):
          rangeStarted = True
      if rangeStarted:
        #break if endDate was already reached but current line contains another date
        if line.split(",")[1].__contains__(endDate):
          endDateReached = True
        #check if date was already bigger than enddate
        elif endDateReached and line.split(",")[1].split(' ')[0]>endDate:
          continue
        if line.split(",")[1].split(' ')[0]<startDate:
          continue
        #if date range started and loop did not continue, write line to output file
        output_file.write(line)
        print 'pickup: '+ line.split(",")[1]
        print 'dropoff: ' + line.split(",")[2]



