from flask import Flask

from os.path import join

from bbb_api.views.base import base_api
from bbb_api import config
from bbb_core import config as core_config



def create_app():
    """
    Creates Flask app, adds all views registering via blueprint on '/' route
    """

    app = Flask(__name__)
    app.config.from_pyfile('config.py')
    app.register_blueprint(base_api)
    return app


if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=6699, debug=True)