from flask import Flask
import os

from dashboard_app import dashboard_app

class Dashboard(object):
    def __init__(self, app=None, url_prefix='/', auth_handler=None):
        self.url_prefix = url_prefix
        if app is not None:
            self.app = app
            self.init_app(app)
        else:
            self.app = None
        self.auth_handler = auth_handler
        self.docker_conn = None

    def init_app(self, app):
        app.register_blueprint(dashboard_app, url_prefix=self.url_prefix)
        app.extensions['dashboard_app'] = self

app = Flask(__name__)

if os.getenv('DASHBOARD_SETTINGS'):
    app.config.from_envvar('DASHBOARD_SETTINGS')

Dashboard(app, '')