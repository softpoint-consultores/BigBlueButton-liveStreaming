import json
import random
import string
import traceback
import os
from threading import Thread


from flask import Flask, request, jsonify, Blueprint

from functools import wraps

from bbb_api.authentication import auth
from bbb_api import filters
from bbb_core import docker_launcher
from bbb_core import config as core_config, utilities
from bbb_core.exceptions import *

base_api = Blueprint('base_api', __name__)

def safe_run(func):
    @wraps(func)
    def func_wrapper(*args, **kwargs):
        try:
            response = func(*args, **kwargs)
            response['ok'] = True
            return jsonify(response)

        except InvalidFilterError as e:
            return jsonify({'ok': False, 'error': e.errors, 'error_code': 2001})

        except StreamAlreadyRunningError as e:
            return jsonify({'ok': False, 'error': e.errors, 'error_code': 2002, 'id': e.id})

        except Exception as e:
            return jsonify({'ok': False, 'error':str(e), 'traceback': traceback.format_exc(), 'error_code': 5555})
    return func_wrapper


@base_api.route('/', methods=['GET'])
@safe_run
def index():
    msg = {
        'msg': "Welcome to bbb API",
        'ip': filters.get_remote_ip(),
    }

    return msg


@base_api.route('/start_stream', methods=['POST'])
@auth.login_required
@safe_run
def start_stream():
    data = filters.get_start_stream(['meeting_id', 'emission_key'], optional_params=['bbb_url', 'bbb_secret', 'bbb_download_meeting'])

    video_id = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(32))

    container_id = docker_launcher.launch_streaming(
        data['meeting_id'], data['emission_key'],
        data.get('bbb_url', core_config.BBB_URL),
        data.get('bbb_secret', core_config.BBB_SECRET),
        data.get('bbb_download_meeting', False),
        video_id
    )

    response = {
        'id':container_id,
    }

    if data.get('bbb_download_meeting', False):
        response['video_id'] = video_id

    return response


@base_api.route('/stop_stream', methods=['POST'])
@auth.login_required
@safe_run
def stop_stream():
    data = filters.get_data_params(['container_id'])
    msg = 'Stopping stream'
    if docker_launcher.still_streaming(data['container_id']):
        #docker_launcher.stop_streaming(data['container_id'])
        Thread(target=docker_launcher.stop_streaming, args=(data['container_id'],)).start()
    
    else:
        msg = 'Stream has not been launched'
        utilities.remove_emission_key(data['container_id'])

    return {'msg': msg}


@base_api.route('/still_stream', methods=['POST'])
@auth.login_required
@safe_run
def still_stream():
    data = filters.get_data_params(['container_id'])
    state = docker_launcher.still_streaming(data['container_id'])
    return {'streaming_state': 'Up' if state else 'Down', 'status': state}