from os.path import join

import json
import logging
import sys

PRODUCTION_MODE = False
DEBUG_LVL = logging.ERROR

# File System Configuration
FS_HOME = '<path>/bbb-livestreaming/bbb-api' # dif <---
FS_SCRIPT = join(FS_HOME, 'script')
FS_SCRIPT_LOGS = join(FS_SCRIPT,'logs')

########### PYTHON SMTP CONFIG ##############
ALERT_RECEIVERS = [""] # dif <---
ALERT_SENDER = "" # dif <---
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = "" # dif <---
SMTP_PASS = "" # dif <---
#############################################

# BBB Configuration
BBB_URL = ''
BBB_SECRET = ''