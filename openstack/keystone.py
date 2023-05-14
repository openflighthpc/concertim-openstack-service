# Local Imports
from utils.service_logger import create_logger

# Py Packages
import time

# Openstack Packages
import keystoneclient.v3.client as ks_client

class KeystoneHandler:
    def __init__(self, sess):
        self.__LOGGER = create_logger(__name__, '/var/log/concertim-openstack-service-opt.log', 'DEBUG')
        self.client = self.__get_client(sess)

    def __get_client(self, sess):
        start_time = time.time()
        while time.time() - start_time < 30:  # Try for up to 30 seconds
            try:
                client = ks_client.Client(session=sess)
                self.__LOGGER.debug("SUCCESS - Keystone client connected")
                return client # Exit if client creation is successful
            except Exception as e:
                self.__LOGGER.error(f"Failed to create Keystone client: {e}. Retrying...")
                time.sleep(1)  # Wait for a second before retrying

        raise Exception("Failed to create Keystone client after multiple attempts.")
    
    def close(self):
        self.__LOGGER.debug("Closing Keystone Client Connection")
        self.client = None

    def get_projects(self):
        return self.client.projects.list()