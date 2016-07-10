# Preconditions
To run the scripts, add this directory's `modules` folder to your `PYTHONPATH`:

```bash
export PYTHONPATH=$PYTHONPATH:/path/to/MMDS-sose16/spark-scripts/modules
```

# Setup on AWS

Startup Cluster, for example:

```bash
spark-ec2 --instance-type=t2.medium --copy-aws-credentials --region=eu-west-1 -k awskey -i ~/Google\ Drive/mmds/AWS\ mmds-taxi\ user/awskey.pem -s 10 launch cluster
```

Then, login and execute:
```bash
screen

git clone https://github.com/georgwiese/MMDS-sose16.git
cd MMDS-sose16/spark-scripts

export PYTHONPATH=$PYTHONPATH:~/MMDS-sose16/spark-scripts/modules

# Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY

./setup_aws.sh
```

Now, you can start a training, like so:

```bash
./train_evaluate.sh random_forest s3n://mmds-taxi-ireland/no_onehot s3n://mmds-taxi-ireland/models/random_forest evaluation/districts.txt random_forest aws
```

# Starting Spark Scripts
Spark scripts can be executed using the following command:
```sh
spark-submit [SPARK_PARAMETERS] SCRIPT_FILE [SCRIPT_PARAMETERS]
```

## Spark Parameters
Spark parameters can be set either by passing them as command line arguments when starting an application or in the code when instantiating the `SparkContext`. Note, that some parameters can be only set as command line argument and others only in code.

### Setting Parameters in Code
```py
conf = (SparkConf().set(PARAMETER_NAME, VALUE))
sc = SparkContext(conf=conf)
```

### Overview about most important Parameters
| Name / Command Line Argument                  | Default Value                                                             | Description                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       |
|-----------------------------------------------|---------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| spark.master<br> `--master`                   | local[*]                                                                  | The cluster manager to connect to. See the list of [allowed master URL's](http://spark.apache.org/docs/latest/submitting-applications.html#master-urls).                                                                                                                                                                                                                                                                                                                                                          |
| spark.driver. cores<br> `--driver-cores`      | 1                                                                         | Number of cores to use for the driver process, only in cluster mode.                                                                                                                                                                                                                                                                                                                                                                                                                                              |
| spark.driver.memory<br> `--driver-memory`     | 1g                                                                        | Amount of memory to use for the driver process, i.e. where `SparkContext` is initialized. (e.g. 1g, 2g). *Note*: In client mode, this config must not be set through the `SparkConf` directly in your application, because the driver JVM has already started at that point. Instead, please set this through the command line option or in your default properties file.                                                                                                                                         |
| spark.executor.cores<br> `--executor-cores`   | 1 in YARN mode, all the available cores on the worker in standalone mode. | The number of cores to use on each executor. For YARN and standalone mode only. In standalone mode, setting this parameter allows an application to run multiple executors on the same worker, provided that there are enough cores on that worker. Otherwise, only one executor per application will run on each worker.                                                                                                                                                                                         |
| spark.executor.memory<br> `--executor-memory` | 1g                                                                        | Amount of memory to use per executor process (e.g. 2g, 8g).                                                                                                                                                                                                                                                                                                                                                                                                                                                       |
| spark.python.profile                          | false                                                                     | Enable profiling in Python worker, the profile result will show up by `sc.show_profiles()`, or it will be displayed before the driver exiting. It also can be dumped into disk by `sc.dump_profiles(path)`. If some of the profile results had been displayed manually, they will not be displayed automatically before driver exiting. By default the `pyspark.profiler.BasicProfiler` will be used, but this can be overridden by passing a profiler class in as a parameter to the `SparkContext` constructor. |
| spark.python.worker.memory                    | 512m                                                                      | Amount of memory to use per python worker process during aggregation, in the same format as JVM memory strings (e.g. 512m, 2g). If the memory used during aggregation goes above this amount, it will spill the data into disks.                                                                                                                                                                                                                                                                                  |
