import sys
import datetime

from pyspark import SparkContext
from pyspark import SparkConf
from pyspark.sql import SQLContext, Row
from pyspark.sql.types import TimestampType
import pyspark.sql.functions as func
from pyspark.sql.functions import udf, col, when

import pandas as pd


# Get file paths from arguments
if len(sys.argv) != 3:
    print "Usage: events.py INPUT_FILE OUTPUT_FILE"
    sys.exit()
input_file = sys.argv[1]
output_file = sys.argv[2]

# Configure Spark
conf = (SparkConf().setAppName('events-preprocessing'))
sc = SparkContext(conf=conf)
sql_context = SQLContext(sc)

# Read csv file
event_df = sql_context.read.format('com.databricks.spark.csv').options(header='true', inferschema='true').load(input_file)

# Parse dates to datetime and discretize dates by hour
parse_date = lambda date_time: datetime.datetime.strptime(date_time[:19], '%Y-%m-%dT%H:%M:%S')
discretize_date = lambda date_time: datetime.datetime(date_time.year, date_time.month, date_time.day, date_time.hour)
parse_and_discretize = udf(lambda date_time: discretize_date(parse_date(date_time)), TimestampType())
event_df = event_df.withColumn('start_date', parse_and_discretize(event_df.start_date))
event_df = event_df.withColumn('end_date', parse_and_discretize(event_df.end_date))

# Transform schema: One column per venue
venues = event_df.select(event_df.latitude, event_df.longitude).distinct().map(lambda row: (row[0], row[1])).collect()

columns = [when((event_df.latitude == venue[0]) & (event_df.longitude == venue[1]), 1).otherwise(0).alias(str(i)) 
           for i, venue in enumerate(venues)]
sums = [func.sum(col(str(i))).alias(str(i)) for i in range(len(venues))]

prep_event_df = event_df.select(event_df.start_date, event_df.end_date, *columns)
prep_event_df = prep_event_df.groupby(prep_event_df.start_date, prep_event_df.end_date).agg(*sums)

# Map start and end dates to corresponding hours, in which an event happens
def map_to_hour(row):
    date_range = pd.date_range(row.start_date, row.end_date, freq='H')
    date_range = [x.to_datetime() for x in date_range]
    rows = []
    for date in date_range:
        values = {column: row[column] for column in row.asDict() if column not in ['start_date', 'end_date']}
        values['Time'] = date
        
        rows.append(Row(**values))
    
    return rows
    
prep_event_df = prep_event_df.flatMap(map_to_hour).toDF()
prep_event_df = prep_event_df.groupby(prep_event_df.Time).agg(*sums)


# Save preprocessed data
prep_event_df.write.parquet(output_file)