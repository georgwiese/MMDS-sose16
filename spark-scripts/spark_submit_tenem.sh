#! /bin/bash
#
# Runs spark-submit with our default args and the python file that is passed to
# this script. Stores the output in a timestamped logfile.

if [  $# -lt 1 ]
then
  echo "Usage: $0 <spark python script> [optional arguments]"
  exit 1
fi

py_file=$1
shift
script_args=$@

filename=$(basename "$py_file")
scriptname="${filename%.*}"
timestamp=$(date +"%m_%d-%H_%M_%S")
logfile="${scriptname}-${timestamp}.log"

# Default spark arguments
spark_packages="com.databricks:spark-csv_2.11:1.4.0"
spark_memory="3G"
spark_master="spark://172.16.21.111:7077"

mkdir -p logs

spark-submit\
  --master $spark_master\
  --executor-memory $spark_memory\
  --driver-memory $spark_memory\
  --packages $spark_packages\
  $py_file $script_args &> logs/$logfile
