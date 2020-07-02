from setuptools import setup

setup(
    name='bbb_core',
    version='1.0',
    packages=[
        'bbb_core'
    ],
    include_package_data=True,
    install_requires=[
        'flask',
        'Flask-HTTPAuth',
        'arrow',
        'docker',
        'redis',
    ],
)
