from flask import Blueprint
from flask import current_app, request
from flask import render_template, jsonify, redirect, url_for
from functools import wraps
import docker
from cluster import Cluster, InvalidContainer
import json

dashboard_app = Blueprint('dashboard_app', __name__,
        template_folder='templates',
        static_folder='static',)


@dashboard_app.before_app_first_request
def setup_cluster():
    docker_url = 'unix://var/run/docker.sock'
    docker_version = '1.10'
    db_name = 'db_cluster.db'
    if current_app.config.get('DOCKER_URL'):
        docker_url = current_app.config.get('DOCKER_URL')
    if current_app.config.get('DOCKER_VERSION'):
        docker_version = current_app.config.get('DOCKER_VERSION')
    if current_app.config.get('DB_NAME'):
        db_name = current_app.config.get('DB_NAME')
    try:
        current_app.cluster = Cluster(docker_url, docker_version, db_name)
    except Exception as e:
        print e

@dashboard_app.route('/', methods=['GET'])
def overview():
    return render_template('main.html')

@dashboard_app.route('/json/cluster')
def get_cluster():
    cluster = current_app.cluster.list_cluster()
    return jsonify({"nodes": cluster})

@dashboard_app.route('/json/cluster/start', methods=['POST'])
def start_cluster():
    cluster = json.loads(request.data)
    nodes_started = 0
    for node_started in current_app.cluster.start_cluster(cluster):
        nodes_started += 1
    return jsonify({"nodes_started": nodes_started})

@dashboard_app.route('/json/cluster/kill', methods=['POST'])
def stop_cluster():
    current_app.cluster.kill_cluster()
    return jsonify(dict(response='Cluster killed', status=200))

@dashboard_app.route('/json/cluster/update_services', methods=['POST'])
def update_services():
    current_app.cluster.update_java_services()
    return jsonify(dict(response='Services updated', status=200))

@dashboard_app.route('/json/container/<container_id>')
def inspect_json(container_id):
    container = current_app.cluster.container_detail(container_id)
    return jsonify(container)

@dashboard_app.route('/json/container/<container_id>/kill', methods=['POST'])
def kill(container_id):
    try:
        resp = current_app.cluster.kill_container(container_id)
        return jsonify(dict(response='Container %s killed' % container_id, status=200))
    except docker.APIError as e:
        print("Docker APIError: %s" % e)
        return jsonify(dict(response='Container %s not found' % container_id, status=404)), 404

@dashboard_app.route('/json/container/<container_id>/stop', methods=['POST'])
def stop(container_id):
    try:
        resp = current_app.cluster.stop_container(container_id)
        return jsonify(dict(response='Container %s stopped' % container_id, status=200))
    except docker.APIError as e:
        print("Docker APIError: %s" % e)
        return jsonify(dict(response='Container %s not found' % container_id, status=404)), 404

@dashboard_app.route('/json/container/<container_id>/start', methods=['POST'])
def start(container_id):
    try:
        resp = current_app.cluster.start_container(container_id)
        return jsonify(dict(response='Container %s started' % container_id, status=200))
    except docker.APIError as e:
        print("Docker APIError: %s" % e)
        return jsonify(dict(response='Container %s not found' % container_id, status=404)), 404

@dashboard_app.route('/json/container/<container_id>/<service>/logs', methods=['GET'])
def get_logs(container_id, service):
    try:
        lines = request.args.get('lines', '500')
        log = current_app.cluster.get_log(container_id, service, lines)
        return jsonify({"logs": log})
    except InvalidContainer as e:
        print "Invalid container error: %e" % e
    except docker.APIError as e:
        print("Docker APIError: %s" % e)
        return jsonify(dict(response='Container %s not found' % container_id, status=404)), 404
