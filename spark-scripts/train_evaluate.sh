if [  $# -lt 6 ]
then
  echo "Usage: $0 <model type> <feature file> <model folder> <districs file> <result path> <(aws|tenem)>"
  exit 1
fi

model_type=$1
features_file=$2
model_folder=$3
districts_file=$4
result_path=$5
cluster=$6

if [ "$model_type" == "linear" ]
then
  py_training_file="training/linear_regression.py"
elif [ "$model_type" == "random_forest" ]
then
  py_training_file="training/random_forest.py"
else
  echo "Unrecognized model type"
  exit 1
fi

py_evaluation_file="evaluation/evaluate.py"

echo "Train model"
./spark_submit_${cluster}.sh $py_training_file $features_file $model_folder $districts_file

echo "Evaluate model"
./spark_submit_${cluster}.sh $py_evaluation_file $features_file $model_folder $model_type $districts_file $result_path
