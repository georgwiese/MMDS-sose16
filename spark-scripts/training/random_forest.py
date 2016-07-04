"""
Script that trains a random forest model per district using the preprocessing feature dataframe.
All rows until {split_date} are used for training.
The models are stored in the specified {MODEL_FOLDER} using the following file name pattern: model_{LAT}_{LON}
"""

import sys
from pyspark.mllib.tree import RandomForest

from spark_application import create_spark_application
from data_loader import DataLoader
from reader import read_districts_file

# Get file paths from arguments
if len(sys.argv) != 4:
  print "Usage: random_forest.py FEATURES_FILE MODEL_FOLDER DISTRICTS_FILE"
  sys.exit()
features_file, model_folder, districts_file = sys.argv[1:]

spark_context, sql_context = create_spark_application("train_random_forest")
data_loader = DataLoader(spark_context, sql_context, features_file)
data_loader.initialize(do_scaling=False, do_onehot=False)

categorical_features_info = data_loader.get_categorical_features_info()
for lat, lon in read_districts_file(districts_file):
  print("Training District: %f, %f" % (lat, lon))
  model = RandomForest.trainRegressor(data_loader.get_train_data((lat, lon)),
                                      categoricalFeaturesInfo=categorical_features_info,
                                      numTrees=5,
                                      maxDepth=15)
  model.save(spark_context,
             '%s/model_%s_%s' % (model_folder, str(lat), str(lon)))
