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

<img src="images/weather_stations.png" alt="Map weather stations" style="width: 250px;"/>

The information includes:

- Precipitation
- Min/Max temperature
- Wind speed

You can find visualisations of basic statistics of this dataset in our Notebook (TODO: Link).

### Event Dataset

## Implementation

TODO: Pipeline overview

### Preprocessing

### Feature Extraction

### Training

### Evaluation Pipeline

## Results

### Model Evaluation

### Scale-out Experiments

## <a name="getting_started"></a> Getting Started

```bash
pip install -r requirements.txt
```
