""" Module provides create_spark_application function to create Spark & SQL contexts."""

from pyspark import SparkContext
from pyspark import SparkConf
from pyspark.sql import SQLContext

def create_spark_application(app_name):
  """Creates and returns a Spark & SQL Context."""

  conf = (SparkConf().setAppName(app_name))
  spark_context = SparkContext(conf=conf)
  spark_context.setLogLevel('WARN')
  sql_context = SQLContext(spark_context)

  return (spark_context, sql_context)
