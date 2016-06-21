"""
DataLoader class that creates a spar application, loads & preprocesses the data
so that it can be used for training or evaluation.
"""

import abc
from datetime import datetime

from pyspark import SparkContext
from pyspark import SparkConf
from pyspark.sql import SQLContext
from pyspark.mllib.regression import LabeledPoint
from pyspark.ml.feature import VectorAssembler

class DataLoader(object):

  EXCLUDE_COLUMNS = ['Time', 'Lat', 'Lon', 'Pickup_Count']
  DISTRICT_COUNT_THRESHOLD = 50

  def __init__(self, app_name, features_file):

    self.app_name = app_name
    self.features_file = features_file


  def initialize(self):
    """Reads the dataset, initializes class members.

    spark_context: The Spark Context
    sql_context: The SQL Context
    features_df: Original DataFrame as read from the features_file.
    vectorized_train_df: A DataFrame with columns Lat, Lon, Pickup_Count and
        vector column Features.
    districts_with_counts: List of tuples (Lat, Lon, count) of all districts
        that exceed DISTRICT_COUNT_THRESHOLD.
    """

    # Configure Spark
    conf = (SparkConf().setAppName(self.app_name))
    self.spark_context = SparkContext(conf=conf)
    self.spark_context.setLogLevel('WARN')
    self.sql_context = SQLContext(self.spark_context)

    # Read feature dataframe
    self.features_df = self.sql_context.read.parquet(self.features_file).cache()

    # Split into train and test data
    split_date = datetime(2015, 1, 1)
    train_df = self.features_df.filter(self.features_df.Time < split_date)
    test_df = self.features_df.filter(self.features_df.Time > split_date)

    # Vectorize features
    feature_columns = [column for column in self.features_df.columns
                              if column not in self.EXCLUDE_COLUMNS]
    assembler = VectorAssembler(inputCols=feature_columns, outputCol='Features')
    self.vectorized_train_df = assembler.transform(train_df).cache()


    self.districts_with_counts = self.features_df \
                                 .groupBy([self.features_df.Lat, self.features_df.Lon]) \
                                 .count()
    self.districts_with_counts = self.districts_with_counts \
        .where(self.districts_with_counts["count"] >= self.DISTRICT_COUNT_THRESHOLD) \
        .map(lambda row: (row["Lat"], row["Lon"], row["count"])) \
        .collect()


  def get_data_for_district(self, df, district):
    """Returns the subset of `df` that contains the district's data."""

    lat, lon = district
    return df.where((df.Lat == lat) & (df.Lon == lon))


  def get_train_data(self, district):
    """Returns an RDD of LabeledPoints."""

    return self.get_data_for_district(self.vectorized_train_df, district) \
           .map(lambda row: LabeledPoint(row.Pickup_Count, row.Features))
