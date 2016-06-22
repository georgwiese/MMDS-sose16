"""
Script that evaluates a given model.
"""

import sys
from pyspark.mllib.regression import LinearRegressionModel
from pyspark.mllib.evaluation import RegressionMetrics

from spark_application import create_spark_application
from data_loader import DataLoader

# Get file paths from arguments
if len(sys.argv) != 3:
  print "Usage: linear_regression.py FEATURES_FILE MODEL_FOLDER"
  sys.exit()
features_file = sys.argv[1]
model_folder = sys.argv[2]

spark_context, sql_context = create_spark_application("evaluate_linear_regression")
data_loader = DataLoader(spark_context, sql_context, features_file)
data_loader.initialize()

district = (40.75, -73.83)
lat, lon = district

model = LinearRegressionModel.load(spark_context,
                                   '%s/model_%s_%s' % (model_folder, str(lat), str(lon)))

predictions_labels = data_loader.get_test_data(district) \
                     .map(lambda point: (float(model.predict(point.features)),
                                         point.label))

metrics = RegressionMetrics(predictions_labels)

print("MSE = %s" % metrics.meanSquaredError)
print("RMSE = %s" % metrics.rootMeanSquaredError)
