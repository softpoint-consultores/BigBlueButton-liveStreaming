import arrow
import logging
import os
import redis
import time


bbb_redis = redis.Redis(host='localhost', port=6379, db=1, decode_responses=True)


def setup_logger(logger_level, file_name=os.path.basename(__file__), extra_name='', log=None, day_folder=True):
    file_name = file_name.split('.')[0]
    if not log:
        logger = logging.getLogger(file_name+str(extra_name))
        logger.setLevel(logging.DEBUG)
    else:
        logger = log

    if day_folder:
        directory = os.path.join(config.FS_SCRIPT_LOGS, arrow.utcnow().format('YYYY-MM-DD'))
        if not os.path.isdir(directory):
            os.mkdir(directory)

    else:
        directory = config.FS_SCRIPT_LOGS

    fh = logging.FileHandler(os.path.join(directory,'{}{}_logger.log'.format( file_name, extra_name)))
    fh.setLevel(logger_level)

    logging.Formatter.converter = time.gmtime #set utc time
    formatter = logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s')

    fh.setFormatter(formatter)

    for hdlr in logger.handlers[:]:  # remove all old handlers
        logger.removeHandler(hdlr)

    logger.addHandler(fh) #set new handler

    return logger


def is_emitting(emission_key):
    container_id = bbb_redis.hget('yt_to_container', emission_key)
    return bool(container_id)


def add_emission_key(container_id, emission_key):
    bbb_redis.hset('container_to_yt', container_id, emission_key)
    bbb_redis.hset('yt_to_container', emission_key, container_id)


def remove_emission_key(container_id):
    emission_key = bbb_redis.hget('container_to_yt', container_id)
    bbb_redis.hdel('container_to_yt', container_id)
    bbb_redis.hdel('yt_to_container', emission_key)

def get_id_by_emission_key(emission_key):
    container_id = bbb_redis.hget('yt_to_container', emission_key)
    return container_id

