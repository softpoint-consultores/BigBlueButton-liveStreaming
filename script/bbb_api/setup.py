from setuptools import setup

setup(
    name='bbb_api',
    version='1.0',
    packages=[
        'bbb_api',
        'bbb_api.views'
    ],
    include_package_data=True,
    install_requires=[
        'flask',
        'Flask-HTTPAuth',
        'flask_session',
        'flask-cors',
        'pymysql',
        'arrow',
    ],
)
