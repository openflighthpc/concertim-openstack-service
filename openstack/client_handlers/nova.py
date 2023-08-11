# Local Imports
from utils.service_logger import create_logger
from openstack.client_handlers.client_base import ClientHandler
# Py Packages
import sys
import time
# Openstack Packages
import novaclient.client as n_client
#import novaclient.exceptions

class NovaHandler(ClientHandler):
    def __init__(self, sess, log_file, log_level):
        super().__init__(sess, log_file, log_level)
        self.__LOGGER = create_logger(__name__, self._LOG_FILE, self._LOG_LEVEL)
        self.client = self.__get_client(self._SESSION)

    def __get_client(self, sess):
        start_time = time.time()
        error = None
        while time.time() - start_time < 30:  # Try for up to 30 seconds
            try:
                client = n_client.Client(version='2', session=sess)
                self.__LOGGER.debug("SUCCESS - Nova client connected")
                return client # Exit if client creation is successful
            except Exception as e:
                self.__LOGGER.warning(f"Failed to create Nova client: {type(e).__name__} - {e} - Retrying...")
                error = e
                time.sleep(1)  # Wait for a second before retrying
        self.__LOGGER.error(f"Failed to create Nova client after multiple attempts : {type(error).__name__} - {error}")
        raise error

    def list_flavors(self):
        try:
            os_flavors = self.client.flavors.list(detailed=True)
            return os_flavors
        except Exception as e:
            self.__LOGGER.error(f"An unexpected error : {type(e).__name__} - {e}")
            raise e

    def list_servers(self, project_id=None, state=None):
        state_filter = state if state else 'ACTIVE'
        try:
            if project_id:
                self.__LOGGER.debug(f"Fetching servers for project : {project_id}")
                return self.client.servers.list(detailed=True, search_opts={'all_tenants':1, 'vm_state': state_filter, 'project_id': project_id})
            self.__LOGGER.debug("Fetching servers for all projects")
            return self.client.servers.list(detailed=True, search_opts={'all_tenants':1, 'vm_state': state_filter})
        except Exception as e:
            self.__LOGGER.error(f"An unexpected error : {type(e).__name__} - {e}")
            raise e

    def get_server(self, instance_id):
        try:
            return self.client.servers.get(instance_id)
        except Exception as e:
            self.__LOGGER.error(f"An unexpected error : {type(e).__name__} - {e}")
            raise e

    def get_server_group(self, group_id):
        try:
            return self.client.server_groups.get(group_id)
        except Exception as e:
            self.__LOGGER.error(f"An unexpected error : {type(e).__name__} - {e}")
            raise e

    #### DEL
    def server_exists(self, instance_id):
        try:
            ret = self.get_server(instance_id)
        except Exception as e:
            self.__LOGGER.debug(f"Server return exception : {e}")
            return False
        
        self.__LOGGER.debug(f"Server return status : {ret}")
        return True
    ####

    def switch_off_device(self, device_id):
        # testing
        device_id = "c763d503-0c40-4208-9b17-786fd1ce6d99"
        try:
            instances = self.client.servers.list()
            instance = self.get_server(device_id)
            result = self.client.servers.stop(instance)
            return result
        except Exception as e:
            self.__LOGGER.error(f"An unexpected error : {type(e).__name__} - {e}")
            raise e

    def close(self):
        self.__LOGGER.debug("Closing Nova Client Connection")
        self.client = None
        super().close()
