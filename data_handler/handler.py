from utils.service_logger import create_logger

class DataHandler(object):
    def __init__(self, openstack, concertim, config_obj):
        self._LOGGER = create_logger(__name__, '/var/log/concertim-openstack-service-opt.log', config_obj['log_level'])
        self.openstack = openstack
        self.concertim = concertim

    def start(self):
        print("IN HANDLER" + str(self.openstack.keystone.client.projects.list()))
        self._LOGGER.info(str(self.openstack.keystone.client.projects.list()))

    def stop(self):
        self._LOGGER.info("Stopping all other services")