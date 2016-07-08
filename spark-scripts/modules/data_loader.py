"""
DataLoader class loads & preprocesses the data
so that it can be used for training or evaluation.
"""

import abc
from datetime import datetime

from pyspark.sql.types import DoubleType
from pyspark.mllib.regression import LabeledPoint
from pyspark.ml.feature import VectorAssembler, StandardScaler, StringIndexer, OneHotEncoder

class DataLoader(object):

  EXCLUDE_COLUMNS = ['Time', 'Lat', 'Lon', 'Pickup_Count']
  SCALE_COLUMNS = ['Pickup_Count_Dis_1h',
                   'Dropoff_Count_Dis_1h',
                   'Pickup_Count_Dis_4h',
                   'Dropoff_Count_Dis_4h',
                   'Pickup_Count_Nb_1h',
                   'Dropoff_Count_Nb_1h',
                   'Pickup_Count_Nb_4h',
                   'Dropoff_Count_Nb_4h',
                   'Pickup_Count_Nyc_1h',
                   'Dropoff_Count_Nyc_1h',
                   'Pickup_Count_Nyc_4h',
                   'Dropoff_Count_Nyc_4h',
                   'AWND_GHCND:US1NJBG0018',
                   'AWND_GHCND:US1NYKN0003',
                   'AWND_GHCND:US1NYKN0025',
                   'AWND_GHCND:US1NYNS0007',
                   'AWND_GHCND:US1NYQN0002',
                   'AWND_GHCND:US1NYRC0001',
                   'AWND_GHCND:US1NYRC0002',
                   'AWND_GHCND:USC00300961',
                   'AWND_GHCND:USW00014732',
                   'AWND_GHCND:USW00094728',
                   'AWND_GHCND:USW00094789',
                   'PRCP_GHCND:US1NJBG0018',
                   'PRCP_GHCND:US1NYKN0003',
                   'PRCP_GHCND:US1NYKN0025',
                   'PRCP_GHCND:US1NYNS0007',
                   'PRCP_GHCND:US1NYQN0002',
                   'PRCP_GHCND:US1NYRC0001',
                   'PRCP_GHCND:US1NYRC0002',
                   'PRCP_GHCND:USC00300961',
                   'PRCP_GHCND:USW00014732',
                   'PRCP_GHCND:USW00094728',
                   'PRCP_GHCND:USW00094789',
                   'TMAX_GHCND:US1NJBG0018',
                   'TMAX_GHCND:US1NYKN0003',
                   'TMAX_GHCND:US1NYKN0025',
                   'TMAX_GHCND:US1NYNS0007',
                   'TMAX_GHCND:US1NYQN0002',
                   'TMAX_GHCND:US1NYRC0001',
                   'TMAX_GHCND:US1NYRC0002',
                   'TMAX_GHCND:USC00300961',
                   'TMAX_GHCND:USW00014732',
                   'TMAX_GHCND:USW00094728',
                   'TMAX_GHCND:USW00094789',
                   'TMIN_GHCND:US1NJBG0018',
                   'TMIN_GHCND:US1NYKN0003',
                   'TMIN_GHCND:US1NYKN0025',
                   'TMIN_GHCND:US1NYNS0007',
                   'TMIN_GHCND:US1NYQN0002',
                   'TMIN_GHCND:US1NYRC0001',
                   'TMIN_GHCND:US1NYRC0002',
                   'TMIN_GHCND:USC00300961',
                   'TMIN_GHCND:USW00014732',
                   'TMIN_GHCND:USW00094728',
                   'TMIN_GHCND:USW00094789']
  ONE_HOT_COLUMNS = ['Hour', 'Day', 'Month', 'Weekday']
  CATEGORY_VALUES_COUNT = {
    'Hour': 24,
    'Day': 31,
    'Month': 12,
    'Weekday': 7,
    'Is_Holiday': 2
  }

  def __init__(self, spark_context, sql_context, features_file):

    self.spark_context = spark_context
    self.sql_context = sql_context
    self.features_file = features_file


  def initialize(self, do_scaling=True, do_onehot=True):
    """Reads the dataset, initializes class members.

    features_df: Original DataFrame as read from the features_file.
    train_df: A DataFrame with columns Lat, Lon, Pickup_Count and
        vector columns Features & ScaledFeatures. Contains only data before 2015.
    test_df: As train_df, but only containing data of 2015.
    districts_with_counts: A DataFrame with all districts and their counts.
    """

    # Read feature dataframe
    self.features_df = self.sql_context.read.parquet(self.features_file).cache()

    # Set exclude columns to default
    exclude_columns = self.EXCLUDE_COLUMNS

    # Scale features
    if do_scaling:
      assembler = VectorAssembler(inputCols=self.SCALE_COLUMNS,
                                  outputCol='FeaturesToScale')
      self.features_df = assembler.transform(self.features_df)
      scaler = StandardScaler(inputCol='FeaturesToScale',
                              outputCol=('ScaledFeatures'),
                              withStd=True, withMean=False)
      self.features_df = scaler.fit(self.features_df).transform(self.features_df)

      exclude_columns += self.SCALE_COLUMNS + ['FeaturesToScale']

    # Adopt categorical features that do not have a value range of [0, numCategories)
    for column in ['Day', 'Month']:
      self.features_df = self.features_df.withColumn(column, self.features_df[column] - 1)

    # Encode categorical features using one-hot encoding
    if do_onehot:
      vec_category_columns = ['%s_Vector' % column for column in self.ONE_HOT_COLUMNS]
      for i in range(len(self.ONE_HOT_COLUMNS)):
        column = self.ONE_HOT_COLUMNS[i]
        self.features_df = self.features_df.withColumn(column, self.features_df[column].cast(DoubleType()))
        encoder = OneHotEncoder(inputCol=column,
                                outputCol=vec_category_columns[i])
        self.features_df = encoder.transform(self.features_df)
      exclude_columns += self.ONE_HOT_COLUMNS

    # Vectorize features
    feature_columns = [column for column in self.features_df.columns
                              if column not in exclude_columns]
    assembler = VectorAssembler(inputCols=feature_columns, outputCol='Features')
    self.features_df = assembler.transform(self.features_df)

    # Set number of distinct values for categorical features (identified by index)
    self.categorical_features_info = {}
    if not do_onehot:
        self.categorical_features_info = {i:self.CATEGORY_VALUES_COUNT[feature_columns[i]]
                                          for i in range(len(feature_columns))
                                          if feature_columns[i] in self.CATEGORY_VALUES_COUNT.keys()}

    # Split into train and test data
    split_date = datetime(2015, 1, 1)
    self.train_df = self.features_df.filter(self.features_df.Time < split_date).cache()
    self.test_df = self.features_df.filter(self.features_df.Time > split_date).cache()

    # Compute Districts with counts
    self.districts_with_counts = self.features_df \
                                 .groupBy([self.features_df.Lat, self.features_df.Lon]) \
                                 .count()


  def get_data_for_district(self, df, district):
    """Returns the subset of `df` that contains the district's data."""

    lat, lon = district
    return df.where((df.Lat == lat) & (df.Lon == lon))


  def df_to_labeled_points(self, df, district):
    """Returns an RDD of LabeledPoints, features taken from Features."""

    return self.get_data_for_district(df, district) \
           .map(lambda row: LabeledPoint(row.Pickup_Count, row.Features))


  def get_train_data(self, district):

    return self.df_to_labeled_points(self.train_df, district)


  def get_test_data(self, district):

    return self.df_to_labeled_points(self.test_df, district)

  def get_categorical_features_info(self):

    return self.categorical_features_info
