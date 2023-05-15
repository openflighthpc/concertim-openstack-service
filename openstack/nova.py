# Local Imports
from utils.service_logger import create_logger

# Py Packages
import time

# Openstack Packages
import novaclient.client as n_client

class NovaHandler:
    def __init__(self, sess, log_level):
        self.__LOGGER = create_logger(__name__, '/var/log/concertim-openstack-service-opt.log', log_level)
        self.client = self.__get_client(sess)

    def __get_client(self, sess):
        start_time = time.time()
        while time.time() - start_time < 30:  # Try for up to 30 seconds
            try:
                client = n_client.Client(version='2', session=sess)
                self.__LOGGER.debug("SUCCESS - Nova client connected")
                return client# Exit if client creation is successful
            except Exception as e:
                self.__LOGGER.error(f"Failed to create Nova client: {e}. Retrying...")
                time.sleep(1)  # Wait for a second before retrying

        raise Exception("Failed to create Nova client after multiple attempts.")

    def list_flavors(self):
        os_flavors = self.client.flavors.list(detailed=True)
        return os_flavors

    def list_servers(self, project_id=None):
        if project_id:
            self.__LOGGER.debug(f"Fetching servers for project : {project_id}")
            return self.client.servers.list(detailed=True, search_opts={'all_tenants':1, 'vm_state': 'ACTIVE', 'project_id': project_id})
        self.__LOGGER.debug("Fetching servers for all projects")
        return self.client.servers.list(detailed=True, search_opts={'all_tenants':1, 'vm_state': 'ACTIVE'})

    def close(self):
        self.__LOGGER.debug("Closing Nova Client Connection")
        self.client = None