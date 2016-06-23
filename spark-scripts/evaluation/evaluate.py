"""
Script that evaluates a given model.
"""

import sys
import os
from pyspark.mllib.regression import LinearRegressionModel
from pyspark.mllib.evaluation import RegressionMetrics

from spark_application import create_spark_application
from data_loader import DataLoader
from reader import read_districts_file

MODEL_TYPE_TO_CLASS = {
  "linear": LinearRegressionModel
}

# Get file paths from arguments
if len(sys.argv) != 6:
  print "Usage: linear_regression.py FEATURES_FILE MODEL_FOLDER MODEL_TYPE DISTRICTS_FILE RESULT_PATH"
  print "  where model type one of: %s" % str(MODEL_TYPE_TO_CLASS.keys())
  print "  and the districts file is a text file with lines \"<lat>, <lon>\"."
  sys.exit()
features_file, model_folder, model_type, districts_file, result_path = sys.argv[1:]

ModelClass = MODEL_TYPE_TO_CLASS[model_type]

spark_context, sql_context = create_spark_application("evaluate_linear_regression")
data_loader = DataLoader(spark_context, sql_context, features_file)
data_loader.initialize()

results = []

for district in read_districts_file(districts_file):
  print("Evaluating district: %s" % str(district))
  lat, lon = district

  model = ModelClass.load(spark_context,
                          '%s/model_%s_%s' % (model_folder, str(lat), str(lon)))

  predictions_labels = data_loader.get_test_data(district) \
                       .map(lambda point: (float(model.predict(point.features)),
                                           point.label)).cache()
  print(predictions_labels.take(10))

  metrics = RegressionMetrics(predictions_labels)
  mse, rmse = metrics.meanSquaredError, metrics.rootMeanSquaredError
  results.append((district, mse, rmse))

  print("MSE = %s" % mse)
  print("RMSE = %s" % rmse)

# Write Result CSV
model_name = model_folder.split("/")[-1]
filename = os.path.join(result_path, "%s_result.csv" % model_name)

with open(filename, "w") as f:
  f.write("lat, lon, mse, rmse\n")

  for district, mse, rmse in results:
    lat, lon = district
    f.write("%s, %s, %f, %f\n" % (str(lat), str(lon), mse, rmse))

