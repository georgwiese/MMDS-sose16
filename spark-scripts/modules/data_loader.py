"""
DataLoader class loads & preprocesses the data
so that it can be used for training or evaluation.
"""

import abc
from datetime import datetime

from pyspark.mllib.regression import LabeledPoint
from pyspark.ml.feature import VectorAssembler

class DataLoader(object):

  EXCLUDE_COLUMNS = ['Time', 'Lat', 'Lon', 'Pickup_Count']

  def __init__(self, spark_context, sql_context, features_file):

    self.spark_context = spark_context
    self.sql_context = sql_context
    self.features_file = features_file


  def initialize(self):
    """Reads the dataset, initializes class members.

    features_df: Original DataFrame as read from the features_file.
    vectorized_train_df: A DataFrame with columns Lat, Lon, Pickup_Count and
        vector column Features.
    districts_with_counts: A DataFrame with all districts and their counts.
    """


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
    self.vectorized_test_df = assembler.transform(test_df).cache()


    self.districts_with_counts = self.features_df \
                                 .groupBy([self.features_df.Lat, self.features_df.Lon]) \
                                 .count()


  def get_data_for_district(self, df, district):
    """Returns the subset of `df` that contains the district's data."""

    lat, lon = district
    return df.where((df.Lat == lat) & (df.Lon == lon))


  def vectorized_df_to_labeled_points(self, df, district):
    """Returns an RDD of LabeledPoints."""

    return self.get_data_for_district(df, district) \
           .map(lambda row: LabeledPoint(row.Pickup_Count, row.Features))


  def get_train_data(self, district):

    return self.vectorized_df_to_labeled_points(self.vectorized_train_df,
                                                district)


  def get_test_data(self, district):

    return self.vectorized_df_to_labeled_points(self.vectorized_test_df,
                                                district)
