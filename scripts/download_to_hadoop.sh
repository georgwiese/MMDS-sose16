#! /bin/bash

for path in $(cat filelist.txt)
do
  filename=${path:5}
  url="https://storage.googleapis.com/tlc-trip-data/$path"

  wget $url
  $HADOOP_HOME/bin/hadoop fs -put $filename hdfs://tenemhead2/data/mmds16/taxi/yellow
  rm $filename
done
