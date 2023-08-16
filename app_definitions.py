import os

# Calculated paths
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(ROOT_DIR, '/var/log/')
DATA_DIR = os.path.join(ROOT_DIR, '/var/data/')

# Absolute paths
CONFIG_DIR = '/etc/concertim-openstack-service/'
CONFIG_FILE = CONFIG_DIR + 'config.yaml'