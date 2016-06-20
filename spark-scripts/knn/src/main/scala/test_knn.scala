import org.apache.spark.ml.classification.KNNRegression
import org.apache.spark.ml.knn.KNN
import org.apache.spark.mllib.util.MLUtils
import org.apache.spark.sql.types._
import org.apache.spark.sql.{DataFrame, Row, SQLContext}
import org.apache.spark.{Logging, SparkConf, SparkContext}


object Main {
  def main(args: Array[String]): Unit = {

	val conf = new SparkConf().setAppName("Test KNN")
	val sc = new SparkContext(conf)
	//read in raw label and features

	val dataDF = MLUtils.loadLibSVMFile(sc, "hdfs://tenemhead2/data/mmds16/taxi/		features").toDF()
	val trainingDF = dataDF.where("Time.year < 2015")
	val testingDF = dataDF.where("Time.year > 2014")

	val knn = new KNNRegression()
	  .setTopTreeSize(training.count().toInt / 500)
	  .setK(10)

	val knnModel = knn.fit(trainingDF)

	val predicted = knn.transform(testingDF)

	sc.stop()
   }
}
