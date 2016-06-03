# Configuration of Spark

## Configure PySpark for Jupyter Notebooks
In order to use PySpark packages in Jupyter Notebooks, you have to adopt the `PYTHONPATH` environment variable.
Make sure, that `SPARK_HOME` is the path to your local spark installation.
```sh
export PYTHONPATH=$SPARK_HOME/python/:$PYTHONPATH
export PYTHONPATH=$SPARK_HOME/python/lib/py4j-0.8.2.1-src.zip:$PYTHONPATH
```

## Use spark-csv in PySpark
To use spark-csv in PySpark, set the following environment variables (e.g. in your `.bash_profile`).
```sh
export PACKAGES="com.databricks:spark-csv_2.11:1.4.0"
export PYSPARK_SUBMIT_ARGS="--packages ${PACKAGES} pyspark-shell"
```
