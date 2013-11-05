from flask import Blueprint
from flask import current_app
from flask import render_template
import docker

dashboard_app = Blueprint('dashboard_app', __name__,
        template_folder='templates',
        static_folder='static',
        )


@dashboard_app.before_app_first_request
def setup_docker_conn():
    print('setup_docker_conn')
    docker_url = 'unix://var/run/docker.sock'
    docker_version = '0.6.5'
    if current_app.config.get('DOCKER_URL'):
        docker_url = current_app.config.get('DOCKER_URL')
    if current_app.config.get('DOCKER_VERSION'):
        docker_version = current_app.config.get('DOCKER_VERSION')
    print('Se setea la conexion.')
    try:
        current_app.docker_conn = docker.Client(base_url=docker_url, version=docker_version)
    except e:
        print e

@dashboard_app.route('/')
def overview():
    running = current_app.docker_conn.containers(quiet=False, all=False, trunc=True, latest=False, since=None, before=None, limit=-1)
    return render_template('main.html', running=running)

@dashboard_app.route('/inspect/<container_id>')
def inspect(container_id):
    container = current_app.docker_conn.inspect_container(container_id)
    return render_template('detail.html', container=container)