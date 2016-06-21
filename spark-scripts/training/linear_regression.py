"""
Script that trains a linear regression model per district using the preprocessing feature dataframe.
All rows until {split_date} are used for training.
The models are stored in the specified {MODEL_FOLDER} using the following file name pattern: model_{LAT}_{LON}
"""

import sys
from pyspark.mllib.regression import LinearRegressionWithSGD

from train import AbstractDistrictTrainer

class LinearRegressionTrainer(AbstractDistrictTrainer):

  def train(self, district):

    return LinearRegressionWithSGD.train(self.get_train_data(district),
                                         iterations=100,
                                         step=0.00000001)

# Get file paths from arguments
if len(sys.argv) != 3:
  print "Usage: linear_regression.py FEATURES_FILE MODEL_FOLDER"
  sys.exit()
features_file = sys.argv[1]
model_folder = sys.argv[2]

trainer = LinearRegressionTrainer("train_linear_regression", features_file)
trainer.initialize()

for lat, lon, _ in trainer.districts_with_counts:
  print("Training District: %f, %f" % (lat, lon))
  model = trainer.train((lat, lon))
  model.save(trainer.spark_context,
             '%s/model_%s_%s' % (model_folder, str(lat), str(lon)))
