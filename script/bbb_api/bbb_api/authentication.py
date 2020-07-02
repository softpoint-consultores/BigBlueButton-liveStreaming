from flask_httpauth import HTTPBasicAuth
from bbb_api import config

auth = HTTPBasicAuth()

@auth.get_password
def get_pw(username):
    """"
    Checks HTTP basic authentication through upper user dict.

    :params username: username
    :returns: boolean -- Response None or password hash.
    """
    return config.API_USERS.get(username)
