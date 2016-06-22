"""
Script that evaluates a given model.
"""

import sys
from pyspark.mllib.regression import LinearRegressionModel
from pyspark.mllib.evaluation import RegressionMetrics

from spark_application import create_spark_application
from data_loader import DataLoader

MODEL_TYPE_TO_CLASS = {
  "linear": LinearRegressionModel
}

# Get file paths from arguments
if len(sys.argv) != 5:
  print "Usage: linear_regression.py FEATURES_FILE MODEL_FOLDER MODEL_TYPE DISTRICTS_FILE"
  print "  where model type one of: %s" % str(MODEL_TYPE_TO_CLASS.keys())
  print "  and the districts file is a text file with lines \"<lat>, <lon>\"."
  sys.exit()
features_file, model_folder, model_type, districts_file = sys.argv[1:]

ModelClass = MODEL_TYPE_TO_CLASS[model_type]

spark_context, sql_context = create_spark_application("evaluate_linear_regression")
data_loader = DataLoader(spark_context, sql_context, features_file)
data_loader.initialize()

# Read Districts file
districts = spark_context.textFile(districts_file) \
            .map(lambda line: tuple([float(x.strip()) for x in line.split(",")])) \
            .collect()

for district in districts:
  print("Evaluating district: %s" % str(district))
  lat, lon = district

  model = ModelClass.load(spark_context,
                          '%s/model_%s_%s' % (model_folder, str(lat), str(lon)))

  predictions_labels = data_loader.get_test_data(district) \
                       .map(lambda point: (float(model.predict(point.features)),
                                           point.label))

  metrics = RegressionMetrics(predictions_labels)

  print("MSE = %s" % metrics.meanSquaredError)
  print("RMSE = %s" % metrics.rootMeanSquaredError)
