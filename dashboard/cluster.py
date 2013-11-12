import docker as _docker
import envoy
import dataset
import times
import time
import iptools


class InvalidCluster(Exception):
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

        self.docker = _docker.Client(base_url='unix://var/run/docker.sock', version='0.6.5')
        self.db = dataset.connect('sqlite:///' + db_name)

        self.host_ip = None

    def list_cluster(self):
        running_docker = self.docker.containers(quiet=False, all=False, trunc=True, latest=False, since=None, before=None, limit=-1)
        nodes = []

        for running in running_docker:
            node = self.db['node'].find_one(container_id=running['Id'][:12])
            if node is not None:
                running['ip'] = node['ip']
                nodes.append(running)

        return nodes

    def container_detail(self, container_id):
        container = self.docker.inspect_container(container_id)
        node = self.db['node'].find_one(container_id=container_id)
        if node is not None:
            container['ip'] = node['ip']
        return container

    def start_container(self, container_id):
        resp = self.docker.start(container_id)
        db['node'].update(dict(container_id=container_id, status='running'), ['container_id'])
        return resp

    def stop_container(self, container_id):
        resp = self.docker.stop(container_id, timeout=5)
        db['node'].update(dict(container_id=container_id, status='stopped'), ['container_id'])
        return resp

    def kill_container(self, container_id):
        resp = self.docker.kill(container_id)
        db['node'].delete(container_id=container_id)
        return resp

    def stop_cluster(self):
        pass

    def start_cluster(self, cluster):
        """
        cluster is a list of a dict like:
        {'image': 'vierja/hadoop','hostname': 'hadoop1', 'ip': '10.0.1.9', 'services': ['JOBTRACKER', 'NAMENODE']}
        """
        node_table = self.db['node']

        self.check_valid_cluster(cluster) # Raises InvalidCluster

        for node in cluster:
            try:
                # Create and run docker
                res = self.docker.create_container(node['image'], hostname=node['hostname'], dns=['127.0.0.1'], detach=True)
                container_id = res['Id']
                self.docker.start(container_id)

                # Sleeping 1 sec before setting ip
                time.sleep(1)

                # Setting IP
                command = 'sudo ./bin/pipework br1 ' + container_id + ' "' + node['ip'] + '/24"'
                res = envoy.run(command)
                assert res.status_code == 0

                # Adding to DB
                node_table.insert(dict(container_id=container_id, image=node['image'], hostname=node['hostname'], ip=node['ip'], services=','.join(node['services']), created_date=times.now(), status='running'))

                # Setting host if not already
                if self.host_ip is None:
                    # Set the host_ip as the last IP in the subnet used.
                    self.host_ip = self.set_host_ip(node['ip'])

                self.start_service(node['ip'], node['services'])

                # Yielding
                yield node['hostname']

            except Exception as e:
                print "Failed to start the cluster.", e
                self.stop_cluster()
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

    def start_service(self, node_ip, services):
        """
        Start services (list) in node_ip using SSH.
        """
        command = 'ssh hduser@' + node_ip + ' -i ../keys/master -o StrictHostKeyChecking=no -q /usr/local/hadoop/bin/'
        for service in services:
            if service == 'NAMENODE':
                run_command = command + 'hadoop namenode -format'
                res = envoy.run(run_command)
                assert res.status_code == 0

            run_command = command + 'hadoop-daemon.sh start ' + service.lower()
            res = envoy.run(run_command)
            assert res.status_code == 0
