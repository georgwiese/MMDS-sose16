# Use Python 2.7
echo 'export PYSPARK_PYTHON=python27' >> /root/spark/conf/spark-env.sh
~/spark-ec2/copy-dir /root/spark/conf/spark-env.sh


# Install PIP & numpy
wget https://bootstrap.pypa.io/get-pip.py
python27 get-pip.py
yes | yum install python27-devel
pip2.7 install numpy

~/spark-ec2/copy-dir /usr/local/lib64/python2.7/site-packages/numpy

# Update AWS CLI
pip install --upgrade awscli
