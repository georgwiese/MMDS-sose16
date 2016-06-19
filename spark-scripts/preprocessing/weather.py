"""
Script that preprocesses the entire NOAA daily summeries weather dataset.

Precomputes a table with the schema:
- Time: date
- {STATION}_PRCP: Precipitation in tenth of mm; one column per station
- {STATION}_TMIN: Minimum temperature in celsius degrees to tenths; one column per station
- {STATION}_TMAX: Maximum temperature in celsius degrees to tenths; one column per station
- {STATION}_AWND: Average daily wind speed in tenths of meters per second; one column per station

Missing values are added using the average value of the three nearest stations on that day. If no station has a value, the overall average is used. 
"""

import sys
import datetime

from pyspark import SparkContext
from pyspark import SparkConf
from pyspark.sql import SQLContext, Row
from pyspark.sql.types import DateType
import pyspark.sql.functions as func
from pyspark.sql.functions import udf, col, when

import numpy as np
from sklearn.neighbors import NearestNeighbors


# Get file paths from arguments
if len(sys.argv) != 3:
    print "Usage: weather.py INPUT_FILE OUTPUT_FILE"
    sys.exit()
input_file = sys.argv[1]
output_file = sys.argv[2]

# Configure Spark
conf = (SparkConf().setAppName('weather-preprocessing'))
sc = SparkContext(conf=conf)
sql_context = SQLContext(sc)

# Read csv file
weather_df = sql_context.read.format('com.databricks.spark.csv').options(header='true', inferschema='true').load(input_file)
weather_df = weather_df.replace(-9999, np.nan)

# Parse dates
parse_date = lambda date: datetime.datetime.strptime(str(date), '%Y%m%d').date()
parse_date_udf = udf(parse_date, DateType())
weather_df = weather_df.withColumn('DATE', parse_date_udf(weather_df.DATE))

# Rename columns consistently
weather_df = weather_df.withColumnRenamed('DATE', 'Date')
weather_df = weather_df.withColumnRenamed('LATITUDE', 'Lat')
weather_df = weather_df.withColumnRenamed('LONGITUDE', 'Lon')
weather_df = weather_df.withColumnRenamed('STATION', 'Station')

# Filter unnecessary columns
value_columns = ['TMIN', 'TMAX', 'PRCP', 'AWND']
weather_df = weather_df.select(weather_df.Date, weather_df.Lat, weather_df.Lon, weather_df.Station, *value_columns)

# Get avg values for all value columns
avg_values = {}
for column in value_columns:
    avg_values[column] = weather_df.select(column).where(func.isnan(column) == False).groupby().avg().map(lambda row: row[0]).first()


# Get stations and their coordinates
station_columns = [weather_df.Station, weather_df.Lat, weather_df.Lon]
agg = [func.avg(weather_df.Lat).alias('Lat'), func.avg(weather_df.Lon).alias('Lon')]
stations_df = weather_df.select(station_columns).groupby(weather_df.Station).agg(*agg).orderBy(weather_df.Station)
stations = stations_df.select(weather_df.Station).map(lambda row: row[0]).collect()
station_coords = stations_df.map(lambda row: (row[0], (row[1], row[2]))).collectAsMap()

# Get neighbors for each station ordered by distance
station_neighbors = {}
for station in stations:
    neighbors = [s for s in stations if s != station]
    neighbors_coords = [station_coords[s] for s in neighbors]
    model = NearestNeighbors(n_neighbors=len(neighbors), algorithm='ball_tree').fit(neighbors_coords)
    distances, indices = model.kneighbors([station_coords[station]])
    station_neighbors[station] = [neighbors[i] for i in indices[0]]

# Transform schema: One row per date and stations as columns
def column_name(column, station):
    return '%s_%s' % (column, station)

match_conditons = (weather_df.Station == station) & (weather_df[column] != None)
columns = [when(match_conditons, weather_df[column]).otherwise(None).alias(column_name(column, station)) 
           for column in value_columns for station in stations]
sums = [func.sum(col(column_name(column, station))).alias(column_name(column, station))
        for column in value_columns for station in stations]

prep_weather_df = weather_df.select(weather_df.Date, *columns)
prep_weather_df = prep_weather_df.groupby(weather_df.Date).agg(*sums)

# Add missing values
def get_missing_value(station, column, row):
    neighbor_values = [row[column_name(column, station)] for station in station_neighbors[station]]
    neighbor_values = [x for x in neighbor_values if x != None][:3]        
    if neighbor_values:
        return sum(neighbor_values) / len(neighbor_values)
    else:
        return avg_values[column]

def add_missing_values(row):
    values = {
        'Date': row.Date
    }
    for column in value_columns:
        for station in stations:
            if row[column_name(column, station)] is None:
                values[column_name(column, station)] = get_missing_value(station, column, row)
            else:
                values[column_name(column, station)] = row[column_name]
        
    return Row(**values)
    
prep_weather_df = prep_weather_df.map(add_missing_values).toDF()

# Save preprocessed data frame
prep_weather_df.write.parquet(output_file)