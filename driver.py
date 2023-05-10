from openstack.service import OpenstackService
from concertim.service import ConcertimService
from data_handler.handler import DataHandler
from utils.service_logger import create_logger

import logging
import signal
import sys
import yaml

# The main logic of the driver
def main(args):
    config = load_config('/etc/concertim-openstack-service/config.yaml')
    logger = create_logger('/var/log/concertim-openstack-service-opt.log', config['log_level'])
    openstack = OpenstackService(config['openstack'])
    concertim = ConcertimService(config['concertim'])
    handler = DataHandler(openstack,concertim)

    # Set up a signal handler to stop the service gracefully
    def signal_handler(sig, frame):
        handler.stop()
        openstack.disconnect()
        concertim.disconnect()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        handler.start()
    except Exception as e:
        logger.exception("Unhandled exception occurred: %s", e)
        handler.stop()
        openstack.disconnect()
        concertim.disconnect()

def load_config(config_file):
    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)
    return config

# The main entry point of the package
if __name__ == "__main__":
    main(sys.argv[1:])