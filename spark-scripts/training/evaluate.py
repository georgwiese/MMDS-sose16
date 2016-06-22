"""
Script that evaluates a given model.
"""

import sys
from pyspark.mllib.regression import LinearRegressionModel
from pyspark.mllib.evaluation import RegressionMetrics

from data_loader import DataLoader

# Get file paths from arguments
if len(sys.argv) != 3:
  print "Usage: linear_regression.py FEATURES_FILE MODEL_FOLDER"
  sys.exit()
features_file = sys.argv[1]
model_folder = sys.argv[2]

data_loader = DataLoader("train_linear_regression", features_file)
data_loader.initialize()

district = (40.75, -73.83)
lat, lon = district

model = LinearRegressionModel.load(data_loader.spark_context,
                                   '%s/model_%s_%s' % (model_folder, str(lat), str(lon)))

predictions_labels = data_loader.get_test_data(district) \
                     .map(lambda point: (float(model.predict(point.features)),
                                         point.label))

metrics = RegressionMetrics(predictions_labels)

print("MSE = %s" % metrics.meanSquaredError)
print("RMSE = %s" % metrics.rootMeanSquaredError)
