"""
Script that trains a random forest model per district using the preprocessing feature dataframe.
All rows until {split_date} are used for training.
The models are stored in the specified {MODEL_FOLDER} using the following file name pattern: model_{LAT}_{LON}

Parameters:
    FEATURES_FILE: the path to the preprocessed feature vector
    MODEL_FOLDER: the path where the models for each district should be stored (hdfs or s3)
    DISTRICTS_FILE: the path to the file specifying the districts that should be trained on (e.g. districts.txt)
"""

import sys
import time
import operator
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
#for the random forest scaling and onehot-encoding are disabled because they better fit to linear regression models
data_loader.initialize(do_scaling=False, do_onehot=False)

#in the case of decision trees categorical features make more sense
maxBins = 32
categorical_features_info = data_loader.get_categorical_features_info()
if categorical_features_info and max(categorical_features_info.values()) > maxBins:
    maxBins = max(categorical_features_info.values())

# train and store a model for each district in the districts file
for lat, lon in read_districts_file(districts_file):
  print("Training District: %f, %f" % (lat, lon))
  start = time.time()
  model = RandomForest.trainRegressor(data_loader.get_train_data((lat, lon)),
                                      categoricalFeaturesInfo=categorical_features_info,
                                      numTrees=5,
                                      maxDepth=15,
                                      maxBins=maxBins)
  #save the model in the specified model_folder
  model.save(spark_context,
             '%s/model_%s_%s' % (model_folder, str(lat), str(lon)))
  print("Done training district. Took %f s." % (time.time() - start))
