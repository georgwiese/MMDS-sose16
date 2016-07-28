# Jupyter Notebooks
We used Jupyter Notebooks for explorating the original datasets and analyzing and evaluating the trained models. You can look at the static rendered notebooks directly on GitHub. If you want to use them interactively, you have to install [Jupyter](http://jupyter.readthedocs.io/en/latest/install.html) and [(Py)Spark](http://spark.apache.org/docs/latest/), which is used in some notebooks. 

## Configure PySpark for Jupyter Notebooks
In order to use the PySpark packages in Jupyter Notebooks, you have to adopt the `PYTHONPATH` environment variable.
Make sure, that `SPARK_HOME` is the path to your local spark installation.
```sh
export PYTHONPATH=$SPARK_HOME/python/:$PYTHONPATH
export PYTHONPATH=$SPARK_HOME/python/lib/py4j-0.8.2.1-src.zip:$PYTHONPATH
```
