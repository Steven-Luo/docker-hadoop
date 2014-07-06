import docker as _docker
import envoy
import dataset
import times
import time
import iptools
import sys, traceback
from threading import Thread


class InvalidCluster(Exception):
    pass

class InvalidContainer(Exception):
    pass


class Cluster(object):
    """
    For creating a managing a cluster
    """

    def __init__(self, base_url, version, db_name):
        super(Cluster, self).__init__()
        self.base_url = base_url
        self.version = version
        self.db_name = db_name

        self.docker = _docker.Client(base_url=self.base_url, version=self.version)
        self.db = dataset.connect('sqlite:///' + self.db_name)

        self.host_ip = None

    def list_cluster(self):
        running_docker = self.docker.containers(quiet=False, all=True, trunc=True, latest=False, since=None, before=None, limit=-1)
        nodes = []

        for running in running_docker:
            node = self.db['node'].find_one(container_id=running['Id'][:12])
            if node is not None:
                running['ip'] = node['ip']
                running['services'] = node['services']
                running['node_status'] = node['status']
                nodes.append(running)

        return nodes

    def container_detail(self, container_id):
        container = self.docker.inspect_container(container_id)
        node = self.db['node'].find_one(container_id=container_id)
        if node is not None:
            container['ip'] = node['ip']
            container['services'] = node['services']
        return container

    # Start a paused container
    def start_container(self, container_id):
        node = self.db['node'].find_one(container_id=container_id)
        resp = self.docker.start(container_id, binds={
                    '/vagrant/hadoop': '/usr/local/hadoop',
                    '/vagrant/tmp/' + node['hostname'] + '-logs': '/var/local/hadoop/logs'
                }, privileged=True)
        self.db['node'].update(dict(container_id=container_id, status='running'), ['container_id'])
        return resp

    # Stop a running container (Send SIGTERM, and then SIGKILL after grace period)
    def stop_container(self, container_id):
        resp = self.docker.stop(container_id)
        self.db['node'].update(dict(container_id=container_id, status='stopped'), ['container_id'])
        return resp

    # Kill a running container (send SIGKILL, or specified signal)
    def kill_container(self, container_id):
        resp = self.docker.kill(container_id)
        self.db['node'].delete(container_id=container_id)
        return resp

    def kill_cluster(self):
        for node in self.db['node']:
            resp = self.docker.kill(node['container_id'])

        self.db['node'].delete() # Delete all just in case.

    def start_cluster(self, cluster):
        """
        cluster is a list of a dict like:
        {'image': 'vierja/hadoop','hostname': 'hadoop1', 'ip': '10.0.1.9', 'services': ['JOBTRACKER', 'NAMENODE']}
        """
        node_table = self.db['node']

        self.check_valid_cluster(cluster) # Raises InvalidCluster

        for pos, node in enumerate(cluster):
            try:
                # Create and run docker
                res = self.docker.create_container(node['image'], hostname=node['hostname'], dns=['127.0.0.1'], volumes=['/usr/local/hadoop', '/var/local/hadoop/logs'], detach=True)
                print "Created container", res['Id']
                container_id = res['Id'][:12]
                result = self.docker.start(res['Id'], binds={
                    '/vagrant/hadoop': '/usr/local/hadoop',
                    '/vagrant/tmp/' + node['hostname'] + '-logs': '/var/local/hadoop/logs'
                }, privileged=True)

                # Sleeping 1 sec before setting ip
                time.sleep(1)

                # Setting IP
                command = 'sudo ./bin/pipework br1 ' + container_id + ' "' + node['ip'] + '/24"'
                res = envoy.run(command)
                if res.status_code != 0:
                    print "Error with command: '" + command + "'"
                    print res.std_out
                    print res.std_err
                    assert False

                # Adding to DB
                node_table.insert(dict(container_id=container_id, image=node['image'], hostname=node['hostname'], ip=node['ip'], services=','.join(node['services']), created_date=times.format(times.now(), 'UTC'), status='starting'))

                # Setting host if not already
                if self.host_ip is None:
                    # Set the host_ip as the last IP in the subnet used.
                    self.host_ip = self.set_host_ip(node['ip'])

                thr = Thread(target = self.start_service, args = [container_id, node['ip'], node['services'], pos + 1])
                thr.start()

                # Yielding
                yield node['hostname']

            except Exception as e:
                print "Failed to start the cluster.", e
                traceback.print_exc()
                self.kill_cluster()
                break

    def check_valid_cluster(self, cluster):
        """
        We check if the data sent is valid:
            - every dict has the necessary fields
            - hostname and ip uniqueness
            - docker image exists
            - services are valid
            - same subnet in all ips
        """
        VALID_SERVICES = ['JOBTRACKER', 'NAMENODE', 'SECONDARYNAMENODE', 'TASKTRACKER', 'DATANODE']

        ip_range_list = None

        ip_list = []
        hostname_list = []

        images_list = []

        jobtracker_defined = False
        namenode_defined = False
        secondarynamenode_defined = False

        for node in cluster:
            # All required field
            if not ('image' in node and 'ip' in node and 'hostname' in node and 'services' in node):
                raise InvalidCluster("Missing field in cluster setup")

            # The image exists (maintain list for only checking once)
            if not node['image'] in images_list:
                images_res = self.docker.images(name=node['image'])
                if len(images_res) == 0:
                    raise InvalidCluster("Image " + node['image'] + " doesn't exists.")
                images_list.append(node['image'])

            if ip_range_list is None:
                ip_range_list = iptools.IpRangeList(node['ip'] + '/24')

            if not node['ip'] in ip_range_list:
                raise InvalidCluster("IPs from different /24 subnets used.")

            # IP is not already defined.
            if node['ip'] in ip_list:
                raise InvalidCluster("Duplicate IP: " + node['ip'])
            ip_list.append(node['ip'])

            # Hostname is not already defined.
            if node['hostname'] in hostname_list:
                raise InvalidCluster("Duplicate Hostname: " + node['hostname'])
            hostname_list.append(node['hostname'])

            # At least one service in list.
            if len(node['services']) == 0:
                raise InvalidCluster("Missing service")

            if 'JOBTRACKER' in node['services']:
                if jobtracker_defined:
                    raise InvalidCluster("Multiple JobTrackers defined")
                jobtracker_defined = True

            if 'NAMENODE' in node['services']:
                if namenode_defined:
                    raise InvalidCluster("Multiple NameNodes defined")
                namenode_defined = True

            if 'SECONDARYNAMENODE' in node['services']:
                if secondarynamenode_defined:
                    raise InvalidCluster("Multiple SecondaryNameNodes defined")
                secondarynamenode_defined = True

            # All service listed belong to the VALID_SERVICES
            if not all(service in VALID_SERVICES for service in node['services']):
                raise InvalidCluster("Invalid service in list: " + node['services'])

        if not namenode_defined:
            raise InvalidCluster("Missing NameNode")

        if not jobtracker_defined:
            raise InvalidCluster("Missing JobTracker")

    def set_host_ip(self, node_ip):
        r = iptools.IpRangeList(node_ip + '/24')
        host_ip = list(r.__iter__())[-2]
        # sudo ifconfig br1 10.0.10.254
        command = 'sudo ifconfig br1 ' + host_ip
        res = envoy.run(command)
        assert res.status_code == 0
        return host_ip

    def start_service(self, container_id, node_ip, services, zookeeper_id):
        """
        Start services (list) in node_ip using SSH.
        """
        command = self.get_ssh("hduser", node_ip)

        # Sleep 1 seconds before starting.
        time.sleep(4)

        if zookeeper_id < 6:
            print "Starting ZooKeeper on", node_ip
            zookeeper_command = command + "export JAVA_OPTS='-Djava.net.preferIPv4Stack=true' && echo " + str(zookeeper_id) + " > /var/run/zookeeper/myid && /usr/local/zookeeper/bin/zkServer.sh start"
            res = envoy.run(zookeeper_command)
            if res.status_code != 0:
                print "Error starting zookeeper:", node_ip
                print res.std_out
                print res.std_err
            time.sleep(5)
        else:
            print "ZooKeeperId is", zookeeper_id, "not starting ZooKeeper service on this node."

        print "Starting services:", services, "on", node_ip
        for service in services:
            if service == 'NAMENODE':
                run_command = command + '/usr/local/hadoop/bin/hadoop namenode -format'
                res = envoy.run(run_command)
                assert res.status_code == 0

            run_command = command + '/usr/local/hadoop/bin/hadoop-daemon.sh start ' + service.lower()
            res = envoy.run(run_command)
            if res.status_code != 0:
                print "Error starting:", node_ip
                print res.std_out
                print res.std_err

            assert res.status_code == 0

        self.db['node'].update(dict(container_id=container_id, status='running'), ['container_id'])
        print "Started services:", ', '.join(services).lower(), "and zooKeeper on", node_ip

    def create_network_conditions(self, container_id, conditions):
        """
        Type of network conditions possibles:

        """
        pass

    def get_ssh(self, user, node_ip):
        return 'ssh ' + user + '@' + node_ip + ' -i ../docker/keys/master -o StrictHostKeyChecking=no '

    def get_log(self, container_id, service, num_lines):

        node = self.db['node'].find_one(container_id=container_id)
        if node is None:
            raise InvalidContainer("Container does not exists")

        command = "tail -n " + str(num_lines) + " /vagrant/tmp/" + node['hostname'] + "-logs/hadoop-hduser-" + service.lower() + "-" + node['hostname'] + ".log"

        print "Command is " + command
        res = envoy.run(command)
        return res.std_out

    def get_java_service(self, ip):
        command = self.get_ssh('hduser', ip) + "jps"
        res = envoy.run(command)
        services = ""
        if res.status_code != 0:
            print "Error updating services for ", ip
        elif res.std_out:
            services = ','.join([service.split(' ')[1] for service in res.std_out.split("\n") if len(service) > 0 and service.split(' ')[1] != "Jps"]).upper().replace("QUORUMPEERMAIN", "ZOOKEEPER")

            print "Services for " + ip + " = " + services
        return services

    def update_java_services(self):
        """
        Updates the services running on each node.
        """
        nodes = self.db['node'].all()  # The .all is for allowing updates in the loop
        for node in nodes:
            services = self.get_java_service(node['ip'])
            if len(services) > 0:
                self.db['node'].update(dict(ip=node['ip'], services=services), ['ip'])
                print "DB updated"

