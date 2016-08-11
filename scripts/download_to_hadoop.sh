# this script is running through all taxi data files given in the filelist.txt,
#     creates google storage urls from the filenames and
#     copies those files from the google storage to the tenem Hadoop File System under hdfs://tenemhead2/data/mmds16/taxi/yellow

#! /bin/bash

for path in $(cat filelist.txt)
do
  filename=${path:5}
  url="https://storage.googleapis.com/tlc-trip-data/$path"

  wget $url
  $HADOOP_HOME/bin/hdfs dfs -Ddfs.replication=2 -put $filename hdfs://tenemhead2/data/mmds16/taxi/yellow
  rm $filename
done
