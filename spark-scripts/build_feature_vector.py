"""
Script that joins the given datasets (taxi, weather, events) and extracts the features per hour and district.

Precomputes a table with the schema:
- Time: datetime, with minutes and seconds discarded
- Lat: latitude of the district
- Lon: longitude of the district
- Pickup_Count: Number of pickups in the corresponding hour and district
- Dropoff_Count: Number of dropoffs in the corresponding hour and district

- Number of pickups/dropoffs in the last 1/4 hours in the corresponding district
    - Pickup_Count_Dis_1h
    - Dropoff_Count_Dis_1h
    - Pickup_Count_Dis_4h
    - Dropoff_Count_Dis_4h
    
- Number of pickups/dropoffs in the last 1/4 hours in the neighboring districts
    - Pickup_Count_Nb_1h
    - Dropoff_Count_Nb_1h
    - Pickup_Count_Nb_4h
    - Dropoff_Count_Nb_4h
    
- Number of pickups/dropoffs in the last 1/4 hours in entire NYC
    - Pickup_Count_Nyc_1h
    - Dropoff_Count_Nyc_1h
    - Pickup_Count_Nyc_4h
    - Dropoff_Count_Nyc_4h

- Hour: hour of the time (one-hot-encoding) 
- Day: day of the time (one-hot-encoding) 
- Month: month of the time (one-hot-encoding) 
- Year: year of the time (one-hot-encoding) 
- Weekday: weekday of the time (one-hot-encoding) 
- IsHoliday: bool that determines, whether the current date was a holiday or not

- Weather data for each of the 11 weather stations
    - {STATION}_PRCP: Precipitation in tenth of mm; one column per station
    - {STATION}_TMIN: Minimum temperature in celsius degrees to tenths; one column per station
    - {STATION}_TMAX: Maximum temperature in celsius degrees to tenths; one column per station
    - {STATION}_AWND: Average daily wind speed in tenths of meters per second; one column per station

- Vector with one entry per venue that contains the number of occuring events in the corresponding hour(+/-3h) and venue
    - Venues_-3h
    - Venues_-2h
    - Venues_-1h
    - Venues_0h
    - Venues_1h
    - Venues_2h
    - Venues_3h
"""
import sys
import math
import datetime

from pyspark import SparkContext
from pyspark import SparkConf
from pyspark.sql import SQLContext
import pyspark.sql.functions as func
from pyspark.sql.functions import udf, col, when
from pyspark.sql.types import TimestampType, IntegerType, DoubleType, BooleanType
from pyspark.ml.feature import OneHotEncoder
from pyspark.mllib.regression import LabeledPoint

import holidays

from spark_application import create_spark_application


# Get file paths from arguments
if len(sys.argv) != 5:
    print "Usage: build_feature_vector.py TAXI_FILE WEATHER_FILE EVENTS_FILE OUTPUT_FILE"
    sys.exit()
taxi_file = sys.argv[1]
weather_file = sys.argv[2]
events_file = sys.argv[3]
output_file = sys.argv[4]

spark_context, sql_context = create_spark_application('build_feature_vector')

# Read preprocessed files
def read_df(path):
    return sql_context.read.parquet(path)

taxi_df = read_df(taxi_file)
weather_df = read_df(weather_file)
event_df = read_df(events_file)

# Helpers
index_columns = ['Time', 'Lat', 'Lon']

def sum_aggregations(category, hours=None):
    actual_suffix = ''
    new_suffix = '_%s' % category
    if hours:
        actual_suffix = '_%s' % category
        new_suffix += '_%sh' % hours

    return [func.sum(column + actual_suffix).alias(column + new_suffix) for column in ['Pickup_Count', 'Dropoff_Count']]

def get_agg_taxi_df(df, hours, group_columns, aggregations):
    agg_df = sql_context.createDataFrame([], df.schema)
    for i in range(1, hours + 1):
        add_hours_udf = udf(lambda date_time: date_time + datetime.timedelta(hours=i), TimestampType())
        agg_df = agg_df.unionAll(df.withColumn('Time', add_hours_udf(df.Time)))

    return agg_df.groupby(group_columns).agg(*aggregations)


# Extract features

# Pickups/Dropoffs in Single Districts
taxi_dis_df = taxi_df.withColumnRenamed('Pickup_Count', 'Pickup_Count_Dis').withColumnRenamed('Dropoff_Count', 'Dropoff_Count_Dis').cache()

taxi_dis_1h_df = get_agg_taxi_df(taxi_dis_df, 1, index_columns, sum_aggregations('Dis', 1))
taxi_dis_4h_df = get_agg_taxi_df(taxi_dis_df, 4, index_columns, sum_aggregations('Dis', 4))


# Pickups/Dropoffs in Neighbor Districts
taxi_nb_df = sql_context.createDataFrame([], taxi_df.schema)
for i in range(-1, 2):
    for j in range(-1, 2):
        # Exclude current district
        if i == j == 0:
            continue

        tmp_df = taxi_df.withColumn('Lat', func.round(taxi_df.Lat + i * 0.01, 2))
        tmp_df = tmp_df.withColumn('Lon', func.round(taxi_df.Lon + j * 0.01, 2))
        taxi_nb_df = taxi_nb_df.unionAll(tmp_df)

taxi_nb_df = taxi_nb_df.groupby(index_columns).agg(*sum_aggregations('Nb')).cache()

taxi_nb_1h_df = get_agg_taxi_df(taxi_nb_df, 1, index_columns, sum_aggregations('Nb', 1))
taxi_nb_4h_df = get_agg_taxi_df(taxi_nb_df, 4, index_columns, sum_aggregations('Nb', 4))


# Pickups/Dropoffs in entire NYC
taxi_nyc_df = taxi_df.groupby(taxi_df.Time).agg(*sum_aggregations('Nyc')).cache()

taxi_nyc_1h_df = get_agg_taxi_df(taxi_nyc_df, 1, 'Time', sum_aggregations('Nyc', 1))
taxi_nyc_4h_df = get_agg_taxi_df(taxi_nyc_df, 4, 'Time', sum_aggregations('Nyc', 4))


# Time features
date_df = taxi_df.select(taxi_df.Time).distinct()

weekday_udf = udf(lambda date_time: date_time.weekday(), IntegerType())
is_holiday_udf = udf(lambda date_time: date_time.date() in holidays.UnitedStates(), BooleanType())

date_df = date_df.withColumn('Hour', func.hour(date_df.Time).cast(DoubleType()))
date_df = date_df.withColumn('Day', func.dayofmonth(date_df.Time).cast(DoubleType()))
date_df = date_df.withColumn('Month', func.month(date_df.Time).cast(DoubleType()))
date_df = date_df.withColumn('Year', func.year(date_df.Time).cast(DoubleType()))
date_df = date_df.withColumn('Weekday', weekday_udf(date_df.Time).cast(DoubleType()))
date_df = date_df.withColumn('Is_Holiday', is_holiday_udf(date_df.Time))

cat_columns = ['Hour', 'Day', 'Month', 'Weekday']
vec_cat_columns = [column + '_Vector' for column in cat_columns]
for i in range(len(cat_columns)):
    date_df = OneHotEncoder(inputCol=cat_columns[i], outputCol=vec_cat_columns[i]).transform(date_df)

date_df = date_df.select(date_df.Time, date_df.Year, date_df.Is_Holiday, *vec_cat_columns)


# Aggregate events happening in last and next 3 hours for each hour
event_3h_df = event_df.withColumnRenamed('Venues', 'Venues_0h')
for i in range(-3, 4):
    if i != 0:
        add_hours_udf = udf(lambda date_time: date_time + datetime.timedelta(hours=i), TimestampType())
        event_3h_df = event_3h_df.join(event_df.withColumn('Time', add_hours_udf(event_df.Time)).withColumnRenamed('Venues', 'Venues_%sh' % str(i)), 'Time')


# Join single feature groups
features_df = taxi_df.select(index_columns + [taxi_df.Pickup_Count]) \
                     .join(taxi_dis_1h_df, index_columns) \
                     .join(taxi_dis_4h_df, index_columns) \
                     .join(taxi_nb_1h_df, index_columns) \
                     .join(taxi_nb_4h_df, index_columns) \
                     .join(taxi_nyc_1h_df, 'Time') \
                     .join(taxi_nyc_4h_df, 'Time') \
                     .join(date_df, 'Time') \
                     .join(weather_df, func.to_date(taxi_df.Time) == weather_df.Date).drop(weather_df.Date) \
                     .join(event_3h_df, 'Time')

features_df.write.parquet(output_file)