The scripts folder mainly contains scripts that were used in the proof-of-concept phase for retrieving events data and to create samples from the taxi data.
The sampling was only needed for the proof-of-concept but the csv file created from the event data retrieval process (event-data-retrieval/*) is imported by the ../spark-scripts/preprocessing/events.py script

The dowload_to_hadoop.sh was used to quickly load the taxi data to the HDFS of tenem from a google storage. 
This was the quickest approach instead of uploading them from a machine with slow network.
filelist.txt contains file names of all relevant files containing the taxi data
