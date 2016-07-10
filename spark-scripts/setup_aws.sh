export PYTHONPATH=$PYTHONPATH:~/MMDS-sose16/spark-scripts/modules

mv /usr/bin/python /usr/bin/python26
cp /usr/bin/python27 /usr/bin/python

wget http://pypi.python.org/packages/source/p/pip/pip-1.1.tar.gz#md5=62a9f08dd5dc69d76734568a6c040508
tar -xvf pip*.gz
cd pip*
sudo python setup.py install
pip install --upgrade pip

yum install python27-devel
pip install numpy
