# Use Python 2.7
mv /usr/bin/python /usr/bin/python26
cp /usr/bin/python27 /usr/bin/python

# Install PIP
wget http://pypi.python.org/packages/source/p/pip/pip-1.1.tar.gz#md5=62a9f08dd5dc69d76734568a6c040508
tar -xvf pip*.gz
cd pip*
sudo python setup.py install
pip install --upgrade pip

# Install Numpy
yes | yum install python27-devel
pip install numpy
