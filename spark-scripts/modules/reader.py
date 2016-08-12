"""Module to read and parse files."""

# read districts file and return array of tuples with lon and lat
def read_districts_file(districts_file):
  with open(districts_file) as f:
    return [tuple([float(x.strip()) for x in line.split(",")])
            for line in f.readlines()]

# read districts file and return tuples with lon and lat in spark
def read_districts_file_spark(spark_context, districts_file):
  return spark_context.textFile(districts_file) \
         .map(lambda line: tuple([float(x.strip()) for x in line.split(",")])) \
         .collect()
