# docker-hadoop

This is a [Docker](http://docker.io) project to bring up a local
Hadoop cluster (tested with v1.0.4). In addition, the
[Pipework](https://github.com/jpetazzo/pipework) project is used to connect
containers to each other. This is heavily based on [@hectcastro](https://github.com/hectcastro)'s [docker-riak](https://github.com/hectcastro/docker-riak).

## Installation

### Install dependencies

Once you're on a Ubuntu machine, install the following dependencies:

```bash
$ sudo apt-get install -y git curl make
```

You will also need Hadoop (I'm using Hadoop v1.0.4).

## Running

### Clone repository

```bash
$ git clone https://github.com/vierja/docker-hadoop.git
$ cd docker-hadoop
$ make
```

Before building the image you need to copy (or move) the Hadoop folder inside `docker-hadoop` and rename it to `hadoop`.

To customize the Hadoop configuration you have to save it to hadoop-conf, try to mimick the already working config and take special care with the `core-site.xml`, `mapred-site.xml` values.

Where everything is ready you can build the container using

```
$ make hadoop-container
```

### Launch cluster

```bash
$ make start-cluster
```

### Tear down cluster

```bash
$ make stop-cluster
```

## Testing

You can use ssh into any machine from the Ubuntu machine connecting to any for the nodes:
```
$ ssh hduser@10.0.10.5 -i keys/master -o StrictHostKeyChecking=no -q
```

Inside a node you can ssh simply by doing:
```
$ ssh hadoop8
```

Inside you can use the hadoop command line tool.

```
/usr/local/hadoop/bin/hadoop dfs -ls /
```

## Default configuration

Every node is named hadoop${num} (e.g. hadoop6). The first 3 are used for the JobTracker, NameNode and SecondaryNameNode respectively.

If you want to modify the number of nodes in the cluster you have to modify:

`hadoop-conf/slaves` and `bin/start-cluster.sh`

Private and public keys are pre-built for managing the cluster, you should create your own.

