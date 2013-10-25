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

# Import master pub key and append it to authorized_keys for no-password login
ADD keys/master.pub /home/hduser/.ssh/master.pub
RUN cat /home/hduser/.ssh/master.pub >> /home/hduser/.ssh/authorized_keys

# Now you can sshd into docker with 'ssh -i /home/hduser/.ssh/master hduser@localhost'

# Adding Hadoop
ADD conf /usr/local/hadoop-conf
ADD hadoop /usr/local/
RUN cp /usr/local/hadoop-conf/* /usr/local/hadoop/
RUN chown -R hduser:hadoop /usr/local/hadoop

# Environment variables
ENV HADOOP_HOME /usr/local/hadoop
ENV JAVA_HOME /usr/lib/jvm/java-6-oracle
ENV PATH $HADOOP_HOME/bin:$PATH

# Hadoop temp dir
RUN mkdir -p /app/hadoop/tmp
RUN locale-gen en_US en_US.UTF-8


EXPOSE 22

CMD /usr/sbin/sshd -D
