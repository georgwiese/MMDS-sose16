import sys
import math
import datetime
import dateutil

from pyspark import SparkContext
from pyspark import SparkConf
from pyspark.sql import SQLContext
import pyspark.sql.functions as func
from pyspark.sql.functions import udf
from pyspark.sql.types import TimestampType, IntegerType, BooleanType
from pyspark.mllib.regression import LabeledPoint

import holidays

# Get file paths from arguments
if len(sys.argv) != 4:
    print "Usage: build_feature_vector.py TAXI_FILE WEATHER_FILE EVENTS_FILE"
    sys.exit()
taxi_file = sys.argv[1]
weather_file = sys.argv[2]
events_file = sys.argv[3]

# Configure Spark
conf = (SparkConf().setAppName('build_feature_vector'))
sc = SparkContext(conf=conf)
sql_context = SQLContext(sc)


# Read preprocessed files
def read_df(path):
    return sql_context.read.parquet(WEATHER_FILE_PATH)

taxi_df = read_df(TAXI_FILE_PATH)
weather_df = read_df(WEATHER_FILE_PATH)
event_df = read_df(EVENTS_FILE_PATH)


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
        
        tmp_df = taxi_df.withColumn('Lat', func.round(taxi_df.lat + i * 0.01, 2))
        tmp_df = tmp_df.withColumn('Lon', func.round(taxi_df.lon + j * 0.01, 2))
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

cols = [func.when(func.hour(date_df.Time) == i, True).otherwise(False).alias('Hour_' + str(i)) 
        for i in range(0, 24)]
cols += [func.when(func.dayofmonth(date_df.Time) == i, True).otherwise(False).alias('Day_' + str(i)) 
         for i in range(1, 32)]
cols += [func.when(func.month(date_df.Time) == i, True).otherwise(False).alias('Month_' + str(i)) 
         for i in range(1, 13)]
cols += [func.when(func.year(date_df.Time) == i, True).otherwise(False).alias('Year_' + str(i)) 
         for i in range(2009, 2016)]
cols += [func.when(weekday_udf(date_df.Time) == i, True).otherwise(False).alias('Weekday_' + str(i)) 
         for i in range(0, 7)]

date_df = date_df.select(date_df.Time, *cols).withColumn('Is_Holiday', is_holiday_udf(date_df.Time))


# Join single feature groups
features_df = taxi_df.select(index_columns + [taxi_df.Pickup_Count]) \
                     .join(taxi_dis_1h_df, index_columns) \
                     .join(taxi_dis_4h_df, index_columns) \
                     .join(taxi_nb_1h_df, index_columns) \
                     .join(taxi_nb_4h_df, index_columns) \
                     .join(taxi_nyc_1h_df, 'Time') \
                     .join(taxi_nyc_4h_df, 'Time') \
                     .join(date_df, 'Time') \
                     .join(weather_df, 'Time') \
                     .join(event_df, 'Time')


# Create feature vector for each district
def create_point(row):
    feature_dict = row.asDict()
    for column in ['Time', 'Lat', 'Lon', 'Pickups']:
        del feature_dict[column]
    
    return LabeledPoint(row.Pickup_Count, list(feature_dict.values()))

district_points = features_df.map(lambda row: ((row.lat, row.lon), [create_point(row)])).reduceByKey(lambda x, y: x + y)