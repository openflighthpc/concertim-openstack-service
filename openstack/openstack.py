from utils.service_logger import create_logger
from openstack.opstk_auth import OpenStackAuth
from openstack.keystone import KeystoneHandler
from openstack.nova import NovaHandler
from openstack.gnocchi import GnocchiHandler


class OpenstackService(object):
    def __init__(self, config_obj):
        self._CONFIG = config_obj
        self._LOGGER = create_logger(__name__, '/var/log/concertim-openstack-service-opt.log', self._CONFIG['log_level'])
        self._OPSTK_AUTH = OpenStackAuth(self._CONFIG['openstack'])
        self.keystone = KeystoneHandler(self._OPSTK_AUTH.get_session())
        self.gnocchi = GnocchiHandler(self._OPSTK_AUTH.get_session())
        self.nova = NovaHandler(self._OPSTK_AUTH.get_session())

    def disconnect(self):
        self._LOGGER.info("Disconnecting Openstack Services")
        self._OPSTK_AUTH = None
        self.keystone.close()
        self.gnocchi.close()
        self.nova.close()