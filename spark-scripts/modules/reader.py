"""Module to read an parse files."""

def read_districts_file(districts_file):
  with open(districts_file) as f:
    return [tuple([float(x.strip()) for x in line.split(",")])
            for line in f.readlines()]

def read_districts_file_spark(spark_context, districts_file):
  return spark_context.textFile(districts_file) \
         .map(lambda line: tuple([float(x.strip()) for x in line.split(",")])) \
         .collect()
