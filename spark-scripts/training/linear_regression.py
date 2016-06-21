"""
Script that trains a linear regression model per district using the preprocessing feature dataframe.
All rows until {split_date} are used for training.
The models are stored in the specified {MODEL_FOLDER} using the following file name pattern: model_{LAT}_{LON}
"""

import sys
from pyspark.mllib.regression import LinearRegressionWithSGD

from data_loader import DataLoader

# Get file paths from arguments
if len(sys.argv) != 3:
  print "Usage: linear_regression.py FEATURES_FILE MODEL_FOLDER"
  sys.exit()
features_file = sys.argv[1]
model_folder = sys.argv[2]

data_loader = DataLoader("train_linear_regression", features_file)
data_loader.initialize()

for lat, lon, _ in data_loader.districts_with_counts:
  print("Training District: %f, %f" % (lat, lon))
  model = LinearRegressionWithSGD.train(data_loader.get_train_data((lat, lon)),
                                        iterations=100,
                                        step=0.00000001)
  model.save(data_loader.spark_context,
             '%s/model_%s_%s' % (model_folder, str(lat), str(lon)))
