#! /bin/bash

set -e

NUM_NODES=15

if sudo docker ps | grep "vierja/hadoop" >/dev/null; then
  echo ""
  echo "It looks like you already have some containers running."
  echo "Please take them down before attempting to bring up another"
  echo "cluster with the following command:"
  echo ""
  echo "  make stop-cluster"
  echo ""

  exit 1
fi

for index in `seq ${NUM_NODES}`;
do
  CONTAINER_ID=$(sudo docker run -d -i \
    -dns 127.0.0.1 \
    -h "hadoop${index}" \
    -e "HADOOP_NODE_NUM=${index}" \
    -t "vierja/hadoop")

  hadoop_cluster[index]=$CONTAINER_ID
  echo "Created container [hadoop${index}] = ${CONTAINER_ID}"
  # echo "hadoop_cluster: ${hadoop_cluster[@]}"

  sleep 1

  sudo ./bin/pipework br1 ${CONTAINER_ID} "10.0.10.${index}/24"

  echo "Started [hadoop${index}] and assigned it the IP [10.0.10.${index}]"

  if [ "$index" -eq "1" ] ; then
    sudo ifconfig br1 10.0.10.254
    #sudo ip addr add 10.0.10.254/24 dev br1
    echo "Created interface for host"
    sleep 1
  fi
done

JOB_TRACKER_ID=${hadoop_cluster[1]}
NAMENODE_ID=${hadoop_cluster[2]}

echo "Starting NameNode[${NAMENODE_ID}]"
ssh hduser@10.0.10.2 -i keys/master -o StrictHostKeyChecking=no -q /usr/local/hadoop/bin/hadoop namenode -format
ssh hduser@10.0.10.2 -i keys/master -o StrictHostKeyChecking=no -q /usr/local/hadoop/bin/stop-dfs.sh
ssh hduser@10.0.10.2 -i keys/master -o StrictHostKeyChecking=no -q /usr/local/hadoop/bin/start-dfs.sh
echo "NameNode started."

echo "Starting JobTracker[${JOB_TRACKER_ID}]"
ssh hduser@10.0.10.1 -i keys/master -o StrictHostKeyChecking=no -q /usr/local/hadoop/bin/start-mapred.sh
echo "JobTracker started."


sleep 1

