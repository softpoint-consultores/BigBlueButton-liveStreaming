import arrow
import os
import re
import redis
import zlib

from flask import request, session
from bbb_core.exceptions import InvalidFilterError, StreamAlreadyRunningError
from bbb_core.utilities import is_emitting, get_id_by_emission_key

ip_pattern = re.compile("^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$")

bbb_redis = redis.Redis(host='localhost', port=6379, db=1, decode_responses=True)

def get_remote_ip():
    ''' Get public ip
    '''
    proxy_forward = request.headers.getlist("X-Forwarded-For")
    if len(proxy_forward) > 0:
        ip = proxy_forward[0].rpartition(' ')[-1]
        if ip_pattern.match(ip):
            return ip
    return request.remote_addr


def test_required_params(data, params):
    return ['Parameter <{}> is required'.format(param) for param in params if param not in data]


def get_data_params(required_params, optional_params=[]):
    """
    Basic method to get params for each api endpoint.
    """
    data = request.json
    errors = test_required_params(data, required_params)
    if errors:
        raise InvalidFilterError(errors=errors)

    # Read all required params
    result = {k:data[k] for k in required_params}

    # Add optional params
    for optional in optional_params:
        if optional in data:
            result[optional] = data[optional]

    return result


def get_start_stream(required_params, optional_params=[]):

    result = get_data_params(required_params, optional_params=optional_params)

    if result['emission_key'] and is_emitting(result['emission_key']):
        container_id = get_id_by_emission_key(result['emission_key'])
        raise StreamAlreadyRunningError(errors=['YouTube key is being used'], id=container_id)

    return result


# Deprecated
def get_stop_stream():
    data = request.json

    required_params = ['container_id']
    errors = test_required_params(data, required_params)

    if errors:
        raise InvalidFilterError(errors=errors)

    # Read all required params
    result = {k:data[k] for k in required_params}

    return result
