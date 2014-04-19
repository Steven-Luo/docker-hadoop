# Hadoop
#
# Version 1.0.4

FROM ubuntu:precise
MAINTAINER Javier Rey javirey@gmail.com

# Update the APT cache
RUN sed -i.bak 's/main$/main universe/' /etc/apt/sources.list

# Adding webupd8team ppa
RUN echo "deb http://ppa.launchpad.net/webupd8team/java/ubuntu precise main\ndeb-src http://ppa.launchpad.net/webupd8team/java/ubuntu precise main" >>  /etc/apt/sources.list
RUN apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv EEA14886

RUN apt-key update && apt-get -y update

# Install curl, ssh, dnsmasq
RUN apt-get install --force-yes -y --fix-missing curl iputils-ping openssh-server

# Install Java 6
RUN echo oracle-java6-installer shared/accepted-oracle-license-v1-1 select true | /usr/bin/debconf-set-selections
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y --force-yes oracle-java6-installer

RUN addgroup hadoop
RUN adduser --disabled-password --ingroup hadoop --quiet --gecos "" hduser

RUN mkdir -p /home/hduser/.ssh/

# Creating hduser keys (for self ssh login)
RUN ssh-keygen -t rsa -P "" -f /home/hduser/.ssh/id_rsa -C "hduser"
RUN cat /home/hduser/.ssh/id_rsa.pub >> /home/hduser/.ssh/authorized_keys
RUN cat /home/hduser/.ssh/id_rsa.pub >> /home/hduser/.ssh/known_hosts
RUN echo "StrictHostKeyChecking no" >> /home/hduser/.ssh/config
RUN mkdir /var/run/sshd
RUN chmod 0755 /var/run/sshd

# Import master pub key and append it to authorized_keys for no-password login
ADD keys/master.pub /home/hduser/.ssh/master.pub
RUN cat /home/hduser/.ssh/master.pub >> /home/hduser/.ssh/authorized_keys

# Owning .ssh
RUN chown -R hduser:hadoop /home/hduser/.ssh/

# Now you can sshd into docker with 'ssh hduser@10.0.10.1 -i keys/master -o StrictHostKeyChecking=no'

# Creating Hadoop folders and setting permissions + temp dir
RUN chown -R hduser:hadoop /usr/local/
RUN mkdir -p /var/local/hadoop/ && chown -R hduser:hadoop /var/local/hadoop/
RUN mkdir -p /app/hadoop/tmp && chown hduser:hadoop /app/hadoop/tmp && chmod 750 /app/hadoop/tmp

# Downloading Zookeeper
RUN mkdir -p /var/run/zookeeper && echo "1" > /var/run/zookeeper/myid && chown -R hduser:hadoop /var/run/zookeeper
RUN curl http://mirror.sdunix.com/apache/zookeeper/zookeeper-3.4.5/zookeeper-3.4.5.tar.gz -o /usr/local/zookeeper.tar.gz
RUN tar -xzf /usr/local/zookeeper.tar.gz -C /usr/local && mv /usr/local/zookeeper-3.4.5 /usr/local/zookeeper && chown -R hduser:hadoop /usr/local/zookeeper && rm /usr/local/zookeeper.tar.gz && chmod +x /usr/local/zookeeper/bin/zkServer.sh
ADD conf/zoo.cfg /usr/local/zookeeper/conf/zoo.cfg

# Annoying hack by halfaleague
ADD conf/hadoop.hosts_2 /tmp/hosts
RUN mkdir -p -- /lib-override && cp /lib/x86_64-linux-gnu/libnss_files.so.2 /lib-override
RUN perl -pi -e 's:/etc/hosts:/tmp/hosts:g' /lib/x86_64-linux-gnu/libnss_files.so.2

CMD /usr/sbin/sshd -D
