# Hadoop
#
# Version 1.0.4

FROM ubuntu:latest
MAINTAINER Javier Rey javirey@gmail.com

# Update the APT cache
RUN sed -i.bak 's/main$/main universe/' /etc/apt/sources.list
RUN apt-get update

# Install curl, ssh, dnsmasq, ping, telnet, net-tools (last 3 for debugging)
RUN apt-get install -y curl dnsmasq openssh-server inetutils-ping telnet net-tools dnsutils

# Adding webupd8team ppa
RUN echo "deb http://ppa.launchpad.net/webupd8team/java/ubuntu precise main\ndeb-src http://ppa.launchpad.net/webupd8team/java/ubuntu precise main" >>  /etc/apt/sources.list
RUN apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv EEA14886

RUN apt-key update && apt-get update

# Install Java 6
RUN echo oracle-java6-installer shared/accepted-oracle-license-v1-1 select true | /usr/bin/debconf-set-selections
RUN apt-get install -y curl oracle-java6-installer

RUN addgroup hadoop
RUN adduser --disabled-password --ingroup hadoop --quiet --gecos "" hduser

RUN mkdir -p /var/run/sshd
RUN mkdir -p /home/hduser/.ssh/

# Creating hduser keys (for self ssh login)
RUN ssh-keygen -t rsa -P "" -f /home/hduser/.ssh/id_rsa -C "hduser"
RUN cat /home/hduser/.ssh/id_rsa.pub >> /home/hduser/.ssh/authorized_keys
RUN cat /home/hduser/.ssh/id_rsa.pub >> /home/hduser/.ssh/known_hosts
RUN echo "StrictHostKeyChecking no" >> /home/hduser/.ssh/config

# Import master pub key and append it to authorized_keys for no-password login
ADD keys/master.pub /home/hduser/.ssh/master.pub
RUN cat /home/hduser/.ssh/master.pub >> /home/hduser/.ssh/authorized_keys

# Owning .ssh
RUN chown -R hduser:hadoop /home/hduser/.ssh/

# Now you can sshd into docker with 'ssh hduser@10.0.10.1 -i keys/master -o StrictHostKeyChecking=no'

# Adding Hadoop
ADD hadoop-conf /usr/local/hadoop-conf
ADD hadoop /usr/local/hadoop
RUN cp /usr/local/hadoop-conf/* /usr/local/hadoop/conf
RUN rm -rf /usr/local/hadoop-conf/ && chown -R hduser:hadoop /usr/local/hadoop
RUN mkdir -p /var/local/hadoop/ && chown -R hduser:hadoop /var/local/hadoop/

# Environment variables
# ENV HADOOP_PREFIX /usr/local/hadoop
# ENV JAVA_HOME /usr/lib/jvm/java-6-oracle
# ENV PATH $HADOOP_PREFIX/bin:$PATH

# Hadoop temp dir
RUN mkdir -p /app/hadoop/tmp && chown hduser:hadoop /app/hadoop/tmp && chmod 750 /app/hadoop/tmp

# Downloading Zookeeper
RUN mkdir -p /var/run/zookeeper && echo "1" > /var/run/zookeeper/myid && chown -R hduser:hadoop /var/run/zookeeper
RUN curl http://mirror.sdunix.com/apache/zookeeper/zookeeper-3.4.5/zookeeper-3.4.5.tar.gz -o /usr/local/zookeeper.tar.gz
RUN tar -xzf /usr/local/zookeeper.tar.gz -C /usr/local && mv /usr/local/zookeeper-3.4.5 /usr/local/zookeeper && chown -R hduser:hadoop /usr/local/zookeeper && rm /usr/local/zookeeper.tar.gz && chmod +x /usr/local/zookeeper/bin/zkServer.sh
ADD conf/zoo.cfg /usr/local/zookeeper/conf/zoo.cfg

# Adding cluster hosts file (we need dnsmasq because /etc/hosts in read-only)
RUN echo 'listen-address=127.0.0.1\nresolv-file=/etc/resolv.dnsmasq.conf\nconf-dir=/etc/dnsmasq.d\naddn-hosts=/etc/dnsmasq.d/0hosts\n' >> /etc/dnsmasq.conf
ADD conf/0hosts /etc/dnsmasq.d/
# Google DNS
RUN echo 'nameserver 8.8.8.8\nnameserver 8.8.4.4' >> /etc/resolv.dnsmasq.conf

CMD export JAVA_OPTS='-Djava.net.preferIPv4Stack=true'; /etc/init.d/dnsmasq start; /usr/sbin/sshd -D
