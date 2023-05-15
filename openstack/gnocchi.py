# Local Imports
from utils.service_logger import create_logger

# Py Packages
import time

# Openstack Packages
import gnocchiclient.v1.client as g_client

class GnocchiHandler:
    def __init__(self, sess, log_level):
        self.__LOGGER = create_logger(__name__, '/var/log/concertim-openstack-service-opt.log', log_level)
        self.client = self.__get_client(sess)

    def __get_client(self, sess):
        start_time = time.time()
        while time.time() - start_time < 30:  # Try for up to 30 seconds
            try:
                client = g_client.Client(session=sess)
                self.__LOGGER.debug("SUCCESS - Gnocchi client connected")
                return client # Exit if client creation is successful
            except Exception as e:
                self.__LOGGER.error(f"Failed to create Gnocchi client: {e}. Retrying...")
                time.sleep(1)  # Wait for a second before retrying

        raise Exception("Failed to create Gnocchi client after multiple attempts.")

    def close(self):
        self.__LOGGER.debug("Closing Gnocchi Client Connection")
        self.client = None