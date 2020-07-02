import boto3
import subprocess

from bbb_core import config

from bbb_core.exceptions import NotEnoughResourcesError
from bbb_core.utilities import add_emission_key, remove_emission_key


def create_task(family='bbb-stream-task', container='bbb-stream-task', bbb_url=config.BBB_URL, bbb_secret=config.BBB_SECRET, image_version='1.0'):
    client = boto3.client('ecs')

    env_vars = {
        'BBB_ATTENDEE_PASSWORD': 'IVLHwOBSVmYP',
        'BBB_BEGIN_INTRO_AT': '04:40',
        'BBB_DOWNLOAD_MEETING': 'false',
        'BBB_END_INTRO_AT': '',
        'BBB_INTRO': 'false',
        'BBB_MEETING_TITLE': 'LiveStreaming Test',
        'BBB_MODERATOR_PASSWORD': '',
        'BBB_SECRET': bbb_secret,
        'BBB_START_MEETING': 'true',
        'BBB_URL': bbb_url,
        'TZ': 'Europe/Vienna'
    }

    env_vars = [{'name': k, 'value': v} for k, v in env_vars.items()]

    response = client.register_task_definition(
        executionRoleArn = "", # <-- diff
        containerDefinitions = [ {
            "portMappings": [],
            "cpu": 0,
            "environment": env_vars,
            "mountPoints": [],
            "volumesFrom": [],
            "image": "", # <-- diff
            "name": "bbb-livestream-container"
        }],
        placementConstraints = [],
        memory = "384",
        taskRoleArn = "", # <-- diff
        family = family,
        requiresCompatibilities = ["EC2"],
        cpu = "1024",
        volumes = []
    )

    return response


def launch_streaming(meeting_id, emission_key, cluster_arn='bbb-cluster', bbb_url=config.BBB_URL, bbb_secret=config.BBB_SECRET):
    client = boto3.client('ecs')

    task = create_task()

    env_vars = {
        'BBB_MEETING_ID': meeting_id,
        'BBB_STREAM_URL': emission_key,
        'BBB_URL': bbb_url,
        'BBB_SECRET': bbb_secret
    }

    env_vars = [{'name': k, 'value': v} for k, v in env_vars.items()]

    response = client.run_task(
        cluster = cluster_arn,
        startedBy = 'Python API',
        count = 1,
        launchType = 'EC2',
        overrides = {
            'containerOverrides': [
                {
                    'name': 'bbb-livestream-container',
                    'environment': env_vars
                },
            ]
        },
        tags = [
            {
                'key': 'Meeting ID',
                'value': meeting_id
            },
        ],
        taskDefinition = task['taskDefinition']['taskDefinitionArn']
    )

    #add_emission_key(container.id, emission_key)
    if not response['tasks']:
        raise NotEnoughResourcesError(
            errors=['Not enough resources on AWS cluster to launch streaming'] + response['failures']
        )

    return response['tasks'][0]['taskArn'], task['taskDefinition']['taskDefinitionArn']


def stop_streaming(task_arn, task_definition_arn, cluster_arn='bbb-cluster'):
    client = boto3.client('ecs')

    # Stop task
    response = client.stop_task(
        cluster = cluster_arn,
        task = task_arn,
        reason = 'Streaming stopped from Python API'
    )

    # Deregister task
    client.deregister_task_definition(
        taskDefinition = task_definition_arn
    )

    return response


def still_streaming(task_arn, cluster_arn='bbb-cluster'):
    client = boto3.client('ecs')
    response = client.describe_tasks(
        cluster = cluster_arn,
        tasks = [task_arn]
    )

    last_status = 'STOPPED'
    tasks = response['tasks']

    if tasks:
        containers = tasks[0]['containers']

        if containers:
            last_status = containers[0]['lastStatus']

    return False if last_status == 'STOPPED' else True


if __name__ == "__main__":
    import argparse
    from time import sleep
    
    ap = argparse.ArgumentParser()
    ap.add_argument('-m', '--meeting', type=str, help='TargetMeet Meeting ID')
    ap.add_argument('-k', '--key', type=str, help='YouTube emission key')
    ap.add_argument('-s', '--secondsToStop', default=0, type=int, help='Seconds to stop (default 0, no stop)')
    args = ap.parse_args()

    cluster_arn = 'arn:aws:ecs:eu-west-3:650238427884:cluster/bbb-cluster' # arn:aws:ecs:eu-west-3:650238427884:cluster/

    task_arn, task_definition_arn = launch_streaming(args.meeting, args.key, cluster_arn, config.BBB_URL, config.BBB_SECRET)

    print('Task arn: {}'.format(task_arn))
    print('Task def: {}'.format(task_definition_arn))

    if args.secondsToStop > 0:
        print('Sleeping for', args.secondsToStop, 'seconds...')
        print(still_streaming(task_arn, cluster_arn=cluster_arn))
        sleep(args.secondsToStop)
        stop_streaming(task_arn, task_definition_arn)

    print('Streaming stopped.')
    while still_streaming(task_arn, cluster_arn=cluster_arn):
        print('Not yet...')
        sleep(1)
