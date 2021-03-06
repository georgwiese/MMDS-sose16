"""
Script that preprocesses the entire merged NYC.gov / Seatgeek event dataset.

Parameters:
  INPUT-FILE: csv obtained from scripts/event-data-retrieval
  OUTPUT-FILE: e.g. hdfs or local path where parquet of event data is stored

Precomputes a table with the schema:
- Time: datetime, with minutes and seconds discarded
- {VENUE_ID}: Number of events happening at the specific venue; one column per venue

Venues are identified by its coordinates.
"""

import sys
import datetime

from pyspark import SparkContext
from pyspark import SparkConf
from pyspark.sql import SQLContext, Row
from pyspark.sql.types import TimestampType
import pyspark.sql.functions as func
from pyspark.sql.functions import udf, col, when
from pyspark.ml.feature import VectorAssembler

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
sc.setLogLevel('WARN')
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
venue_columns = [str(x) for x in range(len(venues))]

columns = [when((event_df.latitude == venue[0]) & (event_df.longitude == venue[1]), 1).otherwise(0).alias(str(i))
           for i, venue in enumerate(venues)]
sums = [func.sum(col(column)).alias(column) for column in venue_columns]

prep_event_df = event_df.select(event_df.start_date, event_df.end_date, *columns)
prep_event_df = prep_event_df.groupby(prep_event_df.start_date, prep_event_df.end_date).agg(*sums)

# Map start and end dates to corresponding hours, in which an event happens
def map_to_hour(row):
    date_range = pd.date_range(row.start_date, row.end_date, freq='H')
    date_range = [x.to_datetime() for x in date_range]
    rows = []
    values = {column: row[column] for column in venue_columns}
    for date in date_range:
        values['Time'] = date

        rows.append(Row(**values))

    return rows

prep_event_df = prep_event_df.flatMap(map_to_hour).toDF()
prep_event_df = prep_event_df.groupby(prep_event_df.Time).agg(*sums)

# Add missing dates within date range (2009 - 2015)
start_date = datetime.datetime(2009, 1, 1)
end_date = datetime.datetime(2015, 12, 31)
date_rdd = sc.parallelize([(x.to_datetime(),) for x in pd.date_range(start_date, end_date, freq='H')])
date_df = sql_context.createDataFrame(date_rdd, ['Time'])
prep_event_df = prep_event_df.join(date_df, 'Time', 'right_outer').fillna(0)

# Combine venue columns to (sparse) vector
assembler = VectorAssembler(inputCols=venue_columns, outputCol='Venues')
prep_event_df = assembler.transform(prep_event_df).select('Time', 'Venues')

# Save preprocessed data
prep_event_df.write.parquet(output_file)
