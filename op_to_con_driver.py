# Local Imports
from openstack.openstack import OpenstackService
from concertim.concertim import ConcertimService
from data_handler.handler import DataHandler
from utils.service_logger import create_logger

# Py Packages
import signal
import sys
import yaml

# The main logic of the driver
def main(args):
    config = load_config('/etc/concertim-openstack-service/config.yaml')
    logger = create_logger(__name__, '/var/log/concertim-openstack-service-opt.log', config['log_level'])

    logger.info("START - CONNECTING SERVICES")
    openstack = OpenstackService(config)
    concertim = ConcertimService(config)
    handler = DataHandler(openstack,concertim,config)

    # Set up a signal handler to stop the service gracefully
    def signal_handler(sig, frame):
        stop()
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


    try:
        logger.info("BEGINNING COMMUNICATION")
        handler.start()
    except Exception as e:
        logger.exception("Unhandled exception occurred: %s", e)
        raise e

    # Set up a stop process for when the service is over
    def stop():
        logger.info("STOPPING PROCESS")
        openstack.disconnect()
        concertim.disconnect()
        handler.stop()
        logger.info("EXITING PROCESS\n")
        raise SystemExit

    stop()

def load_config(config_file):
    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)
    return config

# The main entry point of the package
if __name__ == "__main__":
    main(sys.argv[1:])
