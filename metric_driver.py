# Local Imports
from openstack.openstack import OpenstackService, MissingOpenstackObject
from concertim.concertim import ConcertimService
from data_handler.metric import MetricHandler
from utils.service_logger import create_logger

# Py Packages
import signal
import sys
import yaml
import time

# The main logic of the driver
def main(args):
    # Setup a local start process to loop the metric sending
    def start(i):
        try:
            #'''
            while True:
                handler.send_metrics()
                time.sleep(i)
            #'''
            #handler.send_metrics()
        except Exception as e:
            raise e
    # Setup a local stop process for when the service is over
    def stop():
        logger.info("STOPPING PROCESS")
        openstack.disconnect()
        concertim.disconnect()
        handler.stop()
        logger.info("EXITING PROCESS")
        logger.info("------- END -------\n")
        raise SystemExit
    # Setup a signal handler to stop the service gracefully
    def signal_handler(sig, frame):
        stop()
        
    log_file = '/var/log/concertim-openstack-service/metrics.log'
    config = load_config('/etc/concertim-openstack-service/config.yaml')
    logger = create_logger(__name__, log_file, config['log_level'])
    logger.info("------- START -------")
    logger.info("CONNECTING SERVICES")
    openstack = OpenstackService(config, log_file)
    concertim = ConcertimService(config, log_file)
    # Interval currently set to match concertim MRD ganglia rate
    interval = 15
    #
    handler = MetricHandler(openstack, concertim, config, log_file, interval)
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    try:
        logger.info("BEGINNING COMMUNICATION")
        start(interval)
    except Exception as e:
        logger.error(f"Unhandled exception occurred: {e}")
    finally:
        stop()

def load_config(config_file):
    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)
    return config

# The main entry point of the package
if __name__ == "__main__":
    main(sys.argv[1:])
