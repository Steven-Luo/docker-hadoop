ssh-keygen -f master -t rsa -N ''
ssh hduser@10.0.10.1 -i keys/master -o StrictHostKeyChecking=no -q

# Copy test files to machine.
scp -i /vagrant/keys/master -o StrictHostKeyChecking=no /vagrant/test-files/* hduser@10.0.10.10:~/


# Create directory and add files.
bin/hadoop fs -mkdir /test-files
bin/hadoop fs -mkdir /test-files/input
bin/hadoop fs -put ~/fileA* /test-files/input

# Run WordCount job
bin/hadoop jar ~/wordcount.jar org.myorg.WordCount /test-files/input /test-files/output