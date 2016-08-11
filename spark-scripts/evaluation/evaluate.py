"""
Script that evaluates a given model.
"""

import sys
import os
import math

import numpy as np

from pyspark.mllib.regression import LinearRegressionModel
from pyspark.mllib.tree import RandomForestModel
from pyspark.mllib.evaluation import RegressionMetrics

from spark_application import create_spark_application
from data_loader import DataLoader
from reader import read_districts_file

MODEL_TYPE_TO_CLASS = {
  "linear": LinearRegressionModel,
  "random_forest": RandomForestModel
}

MEASURE_TRAIN_ERROR = False
SAMPLING_FRACTION = 1.0
SAMPLING_SEED = 1234

# Get file paths from arguments
if len(sys.argv) != 6:
  print "Usage: evaluate.py FEATURES_FILE MODEL_FOLDER MODEL_TYPE DISTRICTS_FILE RESULT_PATH"
  print "  where model type one of: %s" % str(MODEL_TYPE_TO_CLASS.keys())
  print "  and the districts file is a text file with lines \"<lat>, <lon>\"."
  sys.exit()
features_file, model_folder, model_type, districts_file, result_path = sys.argv[1:]

model_name = model_folder.split("/")[-1]

ModelClass = MODEL_TYPE_TO_CLASS[model_type]

spark_context, sql_context = create_spark_application("evaluate_%s_regression" % model_type)
data_loader = DataLoader(spark_context, sql_context, features_file)
do_scaling = do_onehot = model_type == "linear"
data_loader.initialize(do_scaling=do_scaling, do_onehot=do_onehot)

results = []

for district in read_districts_file(districts_file):
  print("Evaluating district: %s" % str(district))
  lat, lon = district

  data = data_loader.train_df if MEASURE_TRAIN_ERROR else data_loader.test_df
  if SAMPLING_FRACTION != 1.0:
    data = data.sample(False, SAMPLING_FRACTION, SAMPLING_SEED)

  model = ModelClass.load(spark_context,
                          '%s/model_%s_%s' % (model_folder, str(lat), str(lon)))
  predictions_labels = [(float(model.predict(point.features)), point.label)
                        for point in data_loader.df_to_labeled_points(data, district).collect()]
  print(predictions_labels[:10])

  # Compute Proportional Errors and Squared Proportional Errors
  pes = [abs(pred - label) / (label if label > 0 else 1)
         for pred, label in predictions_labels]
  spes = [pe * pe for pe in pes]
  mspe = np.mean(spes) # means squared proportional error
  mpe = np.mean(pes) # mean proportional error
  rmspe = math.sqrt(mspe) # root mean squared proportional error

  metrics = RegressionMetrics(spark_context.parallelize(predictions_labels))
  mse, rmse = metrics.meanSquaredError, metrics.rootMeanSquaredError
  results.append((district, mse, rmse, mspe, rmspe, mpe))

  print("MSE = %s" % mse)
  print("RMSE = %s" % rmse)
  print("MSPE = %s" % mspe)
  print("RMSPE = %s" % rmspe)
  print("MPE = %s" % mpe)

  # Write predictions_labels CSV
  times = data_loader.get_data_for_district(data, district) \
          .select("Time") \
          .map(lambda row: row.Time) \
          .collect()

  filename = os.path.join(result_path, "%s_%s_%s.csv" % (model_name, str(lat), str(lon)))
  with open(filename, "w") as f:
    f.write("time, prediction, label\n")

    for time, (prediction, label) in zip(times, predictions_labels):
      f.write("%s, %f, %f\n" % (str(time), prediction, label))

# Write Result CSV
filename = os.path.join(result_path, "%s_result.csv" % model_name)

with open(filename, "w") as f:
  f.write("lat, lon, mse, rmse, mspe, rmspe, mpe\n")

  for district, mse, rmse, mspe, rmspe, mpe in results:
    lat, lon = district
    f.write("%s, %s, %f, %f, %f, %f, %f\n" % (str(lat), str(lon), mse, rmse, mspe, rmspe, mpe))
