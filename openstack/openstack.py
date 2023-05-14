# Local Imports
from utils.service_logger import create_logger
from openstack.opstk_auth import OpenStackAuth
from openstack.keystone import KeystoneHandler
from openstack.nova import NovaHandler
from openstack.gnocchi import GnocchiHandler


class OpenstackService(object):
    def __init__(self, config_obj):
        self.__CONFIG = config_obj
        self.__LOGGER = create_logger(__name__, '/var/log/concertim-openstack-service-opt.log', self.__CONFIG['log_level'])
        self.__OPSTK_AUTH = OpenStackAuth(self.__CONFIG['openstack'])
        self.keystone = KeystoneHandler(self.__OPSTK_AUTH.get_session())
        self.gnocchi = GnocchiHandler(self.__OPSTK_AUTH.get_session())
        self.nova = NovaHandler(self.__OPSTK_AUTH.get_session())

    def disconnect(self):
        self.__LOGGER.info("Disconnecting Openstack Services")
        self.__OPSTK_AUTH = None
        self.keystone.close()
        self.gnocchi.close()
        self.nova.close()