# Hadoop
#
# Version 1.0.4

FROM ubuntu:latest
MAINTAINER Javier Rey javirey@gmail.com

# Update the APT cache
RUN sed -i.bak 's/main$/main universe/' /etc/apt/sources.list
RUN apt-get update

# Install curl
RUN apt-get install -y curl

# Adding webupd8team ppa
RUN echo "deb http://ppa.launchpad.net/webupd8team/java/ubuntu precise main\ndeb-src http://ppa.launchpad.net/webupd8team/java/ubuntu precise main" >>  /etc/apt/sources.list
RUN apt-key adv --keyserver keyserver.ubuntu.com --recv EEA14886

RUN apt-get update

# Install Java 6
RUN echo oracle-java6-installer shared/accepted-oracle-license-v1-1 select true | /usr/bin/debconf-set-selections
RUN apt-get install -y curl openssh-server oracle-java6-installer

RUN addgroup hadoop
RUN adduser --disabled-password --ingroup hadoop --quiet --gecos "" hduser

RUN mkdir -p /var/run/sshd
RUN mkdir -p /home/hduser/.ssh/

# Creating hduser keys (for self ssh login)
RUN ssh-keygen -t rsa -P "" -f /home/hduser/.ssh/id_rsa -C "hduser"
RUN cat /home/hduser/.ssh/id_rsa.pub >> /home/hduser/.ssh/authorized_keys
RUN cat /home/hduser/.ssh/id_rsa.pub >> /home/hduser/.ssh/known_hosts
RUN echo "StrictHostKeyChecking no" >> /home/hduser/.ssh/config
RUN chown -R hduser:hadoop /home/hduser/.ssh/

# Import master pub key and append it to authorized_keys for no-password login
ADD keys/master.pub /home/hduser/.ssh/master.pub
RUN cat /home/hduser/.ssh/master.pub >> /home/hduser/.ssh/authorized_keys

# Now you can sshd into docker with 'ssh hduser@10.0.10.1 -i keys/master -o StrictHostKeyChecking=no'

# Adding Hadoop
ADD conf /usr/local/hadoop-conf
ADD hadoop /usr/local/hadoop
RUN cp /usr/local/hadoop-conf/* /usr/local/hadoop/conf
RUN rm -rf /usr/local/hadoop-conf/
RUN chown -R hduser:hadoop /usr/local/hadoop
RUN mkdir -p /var/local/hadoop/
RUN chown -R hduser:hadoop /var/local/hadoop/

# Environment variables
ENV HADOOP_PREFIX /usr/local/hadoop
ENV JAVA_HOME /usr/lib/jvm/java-6-oracle
ENV PATH $HADOOP_PREFIX/bin:$PATH

# Hadoop temp dir
RUN mkdir -p /app/hadoop/tmp
RUN chown hduser:hadoop /app/hadoop/tmp
RUN chmod 750 /app/hadoop/tmp

# Locales
RUN locale-gen en_US en_US.UTF-8

# 50300 : JobTracker
# 1004
# 1006
# 50070
# 8025
# 50470
EXPOSE 22 54311


CMD /usr/sbin/sshd -D
