import sys

from pyspark import SparkContext
from pyspark import SparkConf
from pyspark.sql import SQLContext
from pyspark.mllib.regression import LabeledPoint
from pyspark.mllib.tree import RandomForest


# Get file paths from arguments
if len(sys.argv) != 3:
    print "Usage: random_forrest.py FEATURES_FILE MODEL_FOLDER"
    sys.exit()
features_file = sys.argv[1]
model_folder = sys.argv[2]

# Configure Spark
conf = (SparkConf().setAppName('train_random_forrest'))
sc = SparkContext(conf=conf)
sql_context = SQLContext(sc)

# Read feature dataframe
features_df = sql_context.read.parquet(features_file)

# Create feature vector for each district
def create_point(row):
    feature_dict = row.asDict()
    for column in ['Time', 'Lat', 'Lon', 'Pickup_Count']:
        del feature_dict[column]

    return LabeledPoint(row.Pickup_Count, list(feature_dict.values()))

points_per_district = features_df.map(lambda row: ((row.Lat, row.Lon), create_point(row))).groupByKey()

# Train model per district and save model
for district_points in points_per_district.collect():
    coords = district_points[0]
    points = district_points[1]

    model = RandomForest.trainRegressor(sc.parallelize(points), categoricalFeaturesInfo={},
                                        numTrees=3, featureSubsetStrategy="auto",
                                        impurity='variance', maxDepth=4, maxBins=32)
    model.save(sc, '%s/model_%s_%s' % (model_folder, str(coords[0]), str(coords[1])))