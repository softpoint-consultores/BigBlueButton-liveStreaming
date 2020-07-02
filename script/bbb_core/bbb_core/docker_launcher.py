import docker
import subprocess

from bbb_core import config

from docker.errors import NotFound
from bbb_core.utilities import add_emission_key, remove_emission_key


def launch_streaming(meeting_id, emission_key, bbb_url=config.BBB_URL, bbb_secret=config.BBB_SECRET, download_meeting=False, video_id=''):
    client = docker.from_env()

    container = client.containers.run(
        'facesync/bbb-livestreaming:latest',
        detach=True,
        remove=True,
        environment={
            'BBB_MEETING_ID':meeting_id,
            'BBB_STREAM_URL':'rtmp://a.rtmp.youtube.com/live2/' + emission_key,
            'BBB_URL':bbb_url,
            'BBB_SECRET':bbb_secret,
            'BBB_START_MEETING':True,
            'BBB_ATTENDEE_PASSWORD':'',
            'BBB_MODERATOR_PASSWORD':'',
            'BBB_MEETING_TITLE':'liveStreaming Test',
            'BBB_DOWNLOAD_MEETING':download_meeting,
            'BBB_VIDEO_ID':video_id,
            'BBB_INTRO':False,
            'BBB_BEGIN_INTRO_AT':'04:40',
            'BBB_END_INTRO_AT':'',
            'TZ':'Europe/Vienna',
        }
    )

    add_emission_key(container.id, emission_key)
    return container.id


def stop_streaming(container_id):
    client = docker.from_env()
    client.containers.get(container_id).stop()
    remove_emission_key(container_id)


def still_streaming(container_id):
    client = docker.from_env()
    streaming = True
    try:
        client.containers.get(container_id)
    except NotFound:
        streaming = False

    return streaming


if __name__ == "__main__":
    # This will launch a docker to stream
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument('-m', '--meeting', type=str, help='TargetMeet Meeting ID')
    ap.add_argument('-k', '--key', type=str, help='YouTube emission key')
    args = ap.parse_args()

    launch_streaming(args.meeting, args.key, config.BBB_URL, config.BBB_SECRET)
