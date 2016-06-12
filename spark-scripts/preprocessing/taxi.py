"""
Script that preprocesses the entire yellow taxi data.

Precomputes a table with the schema:
- Time: datetime, with minutes and seconds discarded
- Lat: Discretized Latitute
- Lon: Discretized Longitude
- Pickup_Count: Number of Pickups in this district & hour
- Dropoff_Count: Number of Dropoffs in this district & hour

Lat / Lon discretization is achieved by rounding the floats to two decimal
places.
"""

import sys
import datetime

import pyspark.sql.functions as sqlfunctions

from pyspark import SparkContext
from pyspark import SparkConf
from pyspark.sql import SQLContext, Row
from pyspark.sql.types import BooleanType
from pyspark.sql.functions import udf

# Get file paths from arguments
if len(sys.argv) != 4:
    print "Usage: taxi.py FILELOCATION_BASE INPUT_FILE_LIST_FILE OUTPUT_FILE"
    sys.exit()
file_location_base = sys.argv[1]
input_file_list_file = sys.argv[2]
output_file = sys.argv[3]

# Even though columns are named differently, the column indices of the ones
# we're interested in are consistent across years
COLUMN_INDEX_TO_NAME = {
  1 : "Pickup_Time",
  2 : "Dropoff_Time",
  5 : "Start_Lon",
  6 : "Start_Lat",
  9 : "End_Lon",
  10 : "End_Lat",
}

# Setup Spark
conf = (SparkConf().setAppName('taxi-preprocessing'))
sc = SparkContext(conf=conf)
sql_context = SQLContext(sc)

# Read & Parse file list.
# From lines like "2009/yellow_tripdata_2009-03.csv", it extracts the file name.
with open(input_file_list_file) as filelist_file:
    filelist = [line.strip().split("/")[1] for line in filelist_file.readlines()]

# Read in all CSVs, project the relation to the column we need & concatenate
df = None
for csv_file in filelist:
    new_df = sql_context.read.format('com.databricks.spark.csv')\
             .options(header='true', inferschema='true')\
             .load(file_location_base + csv_file)

    for column_index, column_name in COLUMN_INDEX_TO_NAME.iteritems():
        new_df = new_df.withColumnRenamed(new_df.columns[column_index], column_name)

    new_df = new_df.select(COLUMN_INDEX_TO_NAME.values())

    if df is None:
        df = new_df
    else:
        df = df.unionAll(new_df)

# Clean
df_pickups = df.filter((df.Start_Lon >= -80) & (df.Start_Lon <= -70) & (df.Start_Lat >= 40) & (df.Start_Lat <= 50))
df_dropoffs = df.filter((df.End_Lon >= -80) & (df.End_Lon <= -70) & (df.End_Lat >= 40) & (df.End_Lat <= 50))

def is_float(value):
  try:
    float(value)
    return True
  except ValueError:
    return False

is_float_udf = udf(is_float, BooleanType())
df_pickups = df_pickups.filter((is_float_udf(df.Start_Lon)) & (is_float_udf(df.Start_Lat)))
df_dropoffs = df_dropoffs.filter((is_float_udf(df.End_Lon)) & (is_float_udf(df.End_Lat)))

# Discretize Location
df_pickups = df_pickups.withColumn("Lon", sqlfunctions.round(df.Start_Lon, 2))
df_pickups = df_pickups.withColumn("Lat", sqlfunctions.round(df.Start_Lat, 2))
df_dropoffs = df_dropoffs.withColumn("Lon", sqlfunctions.round(df.End_Lon, 2))
df_dropoffs = df_dropoffs.withColumn("Lat", sqlfunctions.round(df.End_Lat, 2))

# Select Columns
df_pickups = df_pickups.select(df_pickups.Pickup_Time, df_pickups.Lon, df_pickups.Lat)
df_dropoffs = df_dropoffs.select(df_dropoffs.Dropoff_Time, df_dropoffs.Lon, df_dropoffs.Lat)

# Discretize Time
def discretize_time(row):
    return Row(
        Lat=row.Lat,
        Lon=row.Lon,
        Time=datetime.datetime(row.Time.year,
                               row.Time.month,
                               row.Time.day,
                               row.Time.hour)
    )

df_pickups = df_pickups.withColumnRenamed("Pickup_Time", "Time")
df_dropoffs = df_dropoffs.withColumnRenamed("Dropoff_Time", "Time")
df_pickups = df_pickups.map(discretize_time).toDF()
df_dropoffs = df_dropoffs.map(discretize_time).toDF()

# Aggregate counts
pickup_summary = df_pickups.groupby('Time', 'Lat', 'Lon')\
                  .count().withColumnRenamed("count", "Pickup_Count")
dropoff_summary = df_dropoffs.groupby('Time', 'Lat', 'Lon')\
                  .count().withColumnRenamed("count", "Dropoff_Count")

# Join pickup_summary & dropoff_summary
preprocessed_features_df = pickup_summary.join(dropoff_summary, ["Time", "Lat", "Lon"], "outer")
# Replace null values with 0
preprocessed_features_df = preprocessed_features_df.na.fill(0)

# Output
preprocessed_features_df.write.parquet(output_file)
