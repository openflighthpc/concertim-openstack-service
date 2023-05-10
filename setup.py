from setuptools import setup, find_packages

setup(
    name='concertim_openstack_service',
    version='0.1.0',
    packages=find_packages(exclude=['tests*']),
    url='https://github.com/alces-flight/concertim-openstack-service',
    entry_points={
        'console_scripts': [
            'concertim_openstack_service=driver:main',
        ],
    },
)