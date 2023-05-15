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
        self.keystone = KeystoneHandler(self.__OPSTK_AUTH.get_session(), self.__CONFIG['log_level'])
        self.gnocchi = GnocchiHandler(self.__OPSTK_AUTH.get_session(), self.__CONFIG['log_level'])
        self.nova = NovaHandler(self.__OPSTK_AUTH.get_session(), self.__CONFIG['log_level'])
    
    # Returns a list of project ID that the openstack concertim user is a member of
    def get_concertim_projects(self):
        projects = self.keystone.get_projects(user=self.keystone._concertim_user)
        id_list = []
        for project in projects:
            id_list.append(project.id)
        return id_list

    def get_instances(self, project_id):
        instances = self.nova.list_servers(project_id)
        return instances

    def get_flavors(self):
        self.__LOGGER.debug("Getting Openstack flavors")
        flavor_details = {}
        os_flavors = self.nova.list_flavors()
        for flavor in os_flavors:
            flavor_details[str(flavor.name)] = flavor._info
        return flavor_details

    def disconnect(self):
        self.__LOGGER.info("Disconnecting Openstack Services")
        self.__OPSTK_AUTH = None
        self.keystone.close()
        self.gnocchi.close()
        self.nova.close()