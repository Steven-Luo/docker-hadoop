ssh-keygen -f master -t rsa -N ''
ssh hduser@10.0.10.1 -i keys/master -o StrictHostKeyChecking=no -q

# Copy test files to machine.
scp -i /vagrant/keys/master -o StrictHostKeyChecking=no /vagrant/test-files/* hduser@10.0.10.10:~/


# Create directory and add files.
/usr/local/hadoop/bin/hadoop fs -mkdir /test-files
/usr/local/hadoop/bin/hadoop fs -mkdir /test-files/input
/usr/local/hadoop/bin/hadoop fs -put /usr/local/hadoop/pruebas/all_in_one.txt /test-files/input

# Run WordCount job
/usr/local/hadoop/bin/hadoop jar /usr/local/hadoop/pruebas/WordCount/wordcount.jar org.myorg.WordCount /test-files/input /test-files/output

/usr/local/hadoop/bin/hadoop fs -ls /test-files/output
/usr/local/hadoop/bin/hadoop fs -rmr /test-files/output


/usr/local/hadoop/bin/hadoop fs -mkdir /test-files;/usr/local/hadoop/bin/hadoop fs -mkdir /test-files/input;/usr/local/hadoop/bin/hadoop fs -put /usr/local/hadoop/pruebas/all_in_one.txt /test-files/input; /usr/local/hadoop/bin/hadoop jar /usr/local/hadoop/pruebas/WordCount/wordcount.jar org.myorg.WordCount /test-files/input /test-files/output

