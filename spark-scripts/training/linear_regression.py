"""
Script that trains a linear regression model per district using the preprocessing feature dataframe.
All rows until {split_date} are used for training.
The models are stored in the specified {MODEL_FOLDER} using the following file name pattern: model_{LAT}_{LON}

Parameters:
    FEATURES_FILE: the path to the preprocessed feature vector
    MODEL_FOLDER: the path where the models for each district should be stored (hdfs or s3)
    DISTRICTS_FILE: the path to the file specifying the districts that should be trained on (e.g. districts.txt)
"""

import sys
from pyspark.mllib.regression import LinearRegressionWithSGD

from spark_application import create_spark_application
from data_loader import DataLoader
from reader import read_districts_file

# Get file paths from arguments
if len(sys.argv) != 4:
  print "Usage: linear_regression.py FEATURES_FILE MODEL_FOLDER DISTRICTS_FILE"
  sys.exit()
features_file, model_folder, districts_file = sys.argv[1:]

spark_context, sql_context = create_spark_application("train_linear_regression")
data_loader = DataLoader(spark_context, sql_context, features_file)
data_loader.initialize()

# train and store a model for each district in the districts file
for lat, lon in read_districts_file(districts_file):
  print("Training District: %f, %f" % (lat, lon))
  model = LinearRegressionWithSGD.train(data_loader.get_train_data((lat, lon)),
                                        iterations=1000,
                                        step=1e-1)
  # save the model in the specified model_folder
  model.save(spark_context,
             '%s/model_%s_%s' % (model_folder, str(lat), str(lon)))
