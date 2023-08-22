# Using setup.cfg
from setuptools import setup, find_packages
setup()

'''
from setuptools import setup, find_packages

setup(
    name='con-opstk-service',
    version='0.1.2',
    packages=find_packages(exclude=['tests*', 'Dockerfiles*', 'docs*', 'etc*']),
    url='https://github.com/alces-flight/concertim-openstack-service',
    install_requires=[
        'gnocchiclient==7.0.7',
        'keystoneauth1==4.5.0',
        'python-keystoneclient==4.4.0',
        'python-heatclient==2.5.1',
        'python-ceilometerclient==2.9.0',
        'python-openstackclient==5.8.0',
        'Flask==2.0.3',
        'pika==1.3.1'
    ],
    #setup_requires=['pytest-runner', 'flake8'],
    #tests_require=['pytest'],
    entry_points={
        'console_scripts': ['con-opstk=shell:main']
    }
)
'''
