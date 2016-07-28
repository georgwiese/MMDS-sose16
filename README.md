# MMDS-sose16

As part of the "Mining Massive Datasets" Seminar of the [HPI](http://hpi.de/), this project implements a prediction system for taxi pickups in New York City.
We used the [TLC Trip Record Data](http://www.nyc.gov/html/tlc/html/about/trip_record_data.shtml), as well as weather and event datasets, to train regression models using [Apache Spark](http://spark.apache.org/).

In this document, we will describe the datasets we used, our implementation, and our results.
If you simply want to get started, skip to the [Getting Started](#getting_started) section of this document.

## Datasets

In this section, we present the dataset used for training hour system.

### TLC Trip Record Data

The [TLC Trip Record Dataset](http://www.nyc.gov/html/tlc/html/about/trip_record_data.shtml) contains the taxi rides in NYC from 2009 to 2015.
The provided information includes the start & end times as well as start & end locations.

You can find some basic statistics in our Taxi data notebook (TODO: Link).
Furthermore, we plotted heatmaps of the pickup frequencies using our [Heatmap Visualizer](heatmap-visualizer).
The following shows a heatmap of the average pickup frequency by hour:

![Pickups by hour heatmap](images/heatmaps/pickups_by_hour.gif)

### Weather Dataset

TODO: Name & Link to the dataset

The dataset includes daily weather summaries of 11 station, distributed around NYC as follows:

![Map of weather stations](images/weather_stations.png)

The information includes:

- Precipitation
- Min/Max temperature
- Wind speed

You can find visualisations of basic statistics of this dataset in our Notebook (TODO: Link).

### Event Dataset

TODO

## Implementation

Our training pipeline consists of several stages, illustrated in the following graphic:

![Training Pipeline](images/pipeline.png)

We'll to into detail about all the stages in the following sections.

### Preprocessing

### Feature Extraction

### Training

### Evaluation Pipeline

## Results

Our evaluation consists of two parts:
First, we evaluate the model quality.
Second, we evaluate the scalability of our approach.

### Model Evaluation

### Scale-out Experiments

The first point we would like to make wih regard to scalability ist that we think of our approach as inherently scalable:
Since we train one model per district and all models can be trained independently of one another, we can achieve a linear scale-up simply by training hundreds of models in parallel.
Nevertheless, we tested the scalability of our random forest training by doing scale-out experiments.

For this, we used [Amazon Web Services](https://aws.amazon.com/) EC2 in conjunction with the [spark-ec2](http://spark.apache.org/docs/latest/ec2-scripts.html) script to spin up the machines and provision the cluster.
We used the *r3.large* instance type, which has two cores and around 15GB of main memory.

By varying the number of executors and measuring the training time for one model (i.e., one district), we obtained the following runtime chart:

![Runtime chart](images/scale_out/runtime.png)

In the speedup chart (all runtimes divided by the runtime of five nodes), we observe that our speedup is superlinear initially and then flattens:

![Speedup chart](images/scale_out/speedup.png)

We conclude that optimal number of executors for hour task is between 10 and 20 nodes.

## <a name="getting_started"></a> Getting Started

```bash
pip install -r requirements.txt
```
