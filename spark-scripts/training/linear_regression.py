"""
Script that trains a linear regression model per district using the preprocessing feature dataframe. 
All rows until {split_date} are used for training. 
The models are stored in the specified {MODEL_FOLDER} using the following file name pattern: model_{LAT}_{LON}
"""

import sys
from datetime import datetime

from pyspark import SparkContext
from pyspark import SparkConf
from pyspark.sql import SQLContext
from pyspark.mllib.regression import LabeledPoint, LinearRegressionWithSGD
from pyspark.ml.feature import VectorAssembler


# Get file paths from arguments
if len(sys.argv) != 3:
  print "Usage: linear_regression.py FEATURES_FILE MODEL_FOLDER"
  sys.exit()
features_file = sys.argv[1]
model_folder = sys.argv[2]

# Configure Spark
conf = (SparkConf().setAppName('train_linear_regression'))
sc = SparkContext(conf=conf)
sql_context = SQLContext(sc)

# Read feature dataframe
features_df = sql_context.read.parquet(features_file)

# Split into train and test data
split_date = datetime(2015, 1, 1)
train_df = features_df.filter(features_df.Time < split_date)
test_df = features_df.filter(features_df.Time > split_date)

# Vectorize features
feature_columns = [column for column in features_df.columns if column not in ['Time', 'Lat', 'Lon', 'Pickup_Count']]
assembler = VectorAssembler(inputCols=feature_columns, outputCol='Features')
vectorized_train_df = assembler.transform(train_df)

# Create feature vector for each district
def get_data_for_district(df, district):
  lat, lon = district
  return df.where((df.Lat == lat) & (df.Lon == lon))

districts = features_df.select(features_df.Lat, features_df.Lon).distinct() \
            .map(lambda row: (row.Lat, row.Lon)).collect()

# Train model per district and save model
vectorized_train_df = vectorized_train_df.cache()
for lat, lon in districts:
  points = get_data_for_district(vectorized_train_df, (lat, lon)).map(lambda row: LabeledPoint(row.Pickup_Count, row.Features))
  if not points.isEmpty():
    model = LinearRegressionWithSGD.train(points, iterations=100, step=0.00000001)
    model.save(sc, '%s/model_%s_%s' % (model_folder, str(lat), str(lon)))
