import sys

from pyspark import SparkContext
from pyspark import SparkConf
from pyspark.sql import SQLContext
from pyspark.mllib.regression import LabeledPoint, LinearRegressionWithSGD
from datetime import datetime


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
train_data = features_df.filter(features_df["Time"] < split_date)
valid_data = features_df.filter(features_df["Time"] > split_date)

# Create feature vector for each district
def create_point(row):
  feature_dict = row.asDict()
  for column in ['Time', 'Lat', 'Lon', 'Pickup_Count', 'Date']:
    del feature_dict[column]

  return LabeledPoint(row.Pickup_Count, list(feature_dict.values()))

def get_data_for_district(df, district):
  lat, lon = district
  return df[(df["Lat"] == lat) & (df["Lon"] == lon)]

districts = features_df.select("Lat", "Lon").distinct() \
            .map(lambda row: (row.Lat, row.Lon)).collect()

# Train model per district and save model
for lat, lon in districts:
  points = get_data_for_district(train_data, (lat, lon)).map(create_point)

  model = LinearRegressionWithSGD.train(points, iterations=100, step=0.00000001)
  model.save(sc, '%s/model_%s_%s' % (model_folder, str(lat), str(lon)))
