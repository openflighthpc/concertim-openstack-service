from openstack.service import OpenstackService
from concertim.service import ConcertimService
from data_handler.handler import DataHandler

import logging
import signal
import yaml

# The main entry point of the program
if __name__ == "__main__":
    config = load_config('/etc/concertim-openstack-service/config.json')
    logger = create_logger('/var/log/concertim-openstack-service.log')
    openstack = OpenstackService()
    concertim = ConcertimService()
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
        handler.logger.exception("Unhandled exception occurred: %s", e)
        handler.stop()
        openstack.disconnect()
        concertim.disconnect()


def load_config(config_file):
    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)
    return config

def create_logger(log_file):
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        if not os.path.exists(self._LOG_FILE):
            open(self._LOG_FILE, 'w').close()
        fh = logging.FileHandler(log_file)
        fh.setFormatter(formatter)
        logger.addHandler(fh)
        return logger