# Local Imports
from utils.service_logger import create_logger
# concertim component objects
from concertim.components.device import ConcertimDevice
from concertim.components.rack import ConcertimRack
from concertim.components.template import ConcertimTemplate
from concertim.components.user import ConcertimUser

# Py Packages
import time
from datetime import datetime, timedelta

class DataHandler(object):
    def __init__(self, openstack, concertim, config_obj):
        self.__LOGGER = create_logger(__name__, '/var/log/concertim-openstack-service-opt.log', config_obj['log_level'])
        self.openstack = openstack
        self.concertim = concertim

    def start(self):
        """
        while True:
            self.update_concertim()
            time.sleep(5)
            self.send_metrics()
            time.sleep(5)
        """
        print(self.concertim.list_devices())


    def update_concertim(self):
        self.__LOGGER.info('Updating Concertim')

    def send_metrics(self):
        self.__LOGGER.info('Sending Metrics!')

    def stop(self):
        self.__LOGGER.info("Stopping all other services")
        self.openstack = None
        self.concertim = None