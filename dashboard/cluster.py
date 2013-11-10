import docker as _docker
import envoy
import dataset


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
        self.db = dataset.connect('sqlite:///' + db)

    def start_cluster(self, cluster):
        """
        cluster is a list of a dict like:
        {'image': 'vierja/hadoop','hostname': 'hadoop1', 'ip': '10.0.1.9', 'services': ['JOBTRACKER', 'NAMENODE']}
        """
        table = db['node']

        check_valid_cluster(cluster) # Raises InvalidCluster

        for node in cluster:
            try:
                res = docker.create_container(node['image'], hostname=node['hostname'], dns=['127.0.0.1'], detach=True)
                container_id = res['Id']
                command = 'sudo ./bin/pipework br1 ' + container_id + ' "' + node['ip'] + '/24"'
                res = envoy.run(command)
                assert r.status_code == 0
            except:
                print "Failed to start the cluster."
                self.stop_and_clean()
                break

    def check_valid_cluster(self, cluster):
        """
        We check if the data sent is valid:
            - every dict has the necessary fields
            - hostname and ip uniqueness
            - docker image exists
            - services are valid
        """
        VALID_SERVICES = ['JOBTRACKER', 'NAMENODE', 'SECONDARYNAMENODE', 'TASKTRACKER', 'DATANODE']

        ip_list = []
        hostname_list = []

        images_list = []

        for node in cluster:
            # All required field
            if not ('image' in node and 'ip' in node and 'hostname' in node and 'services' in node):
                raise InvalidCluster("Missing field in cluster setup")

            # The image exists (maintain list for only checking once)
            if not node['image'] in images_list:
                images_res = self.docker.images(name=node['image'])
                if len(images_res) == 0:
                    raise InvalidCluster("Image " + node['image'] + " doesn't exists.")
                images_list.add(node['image'])

            # IP is not already defined.
            if node['ip'] in ip_list:
                raise InvalidCluster("Duplicate IP: " + node['ip'])
            ip_list.add(node['ip'])

            # Hostname is not already defined.
            if node['hostname'] in hostname_list:
                raise InvalidCluster("Duplicate Hostname: " + node['hostname'])
            hostname_list.add(node['hostname'])

            # At least one service in list.
            if len(node['services'] == 0):
                raise InvalidCluster("Missing service")

            # All service listed belong to the VALID_SERVICES
            if not all(service in VALID_SERVICES for service in node['services']):
                raise InvalidCluster("Invalid service in list: " + node['services'])

    def stop_and_clean(self):
        pass
