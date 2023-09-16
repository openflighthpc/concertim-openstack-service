# Local Imports
from con_opstk.utils.service_logger import create_logger
from con_opstk.openstack.client_handlers.client_base import ClientHandler
# Py Packages
import sys
import time
# Openstack Packages
from cloudkittyclient import client as ck_client

class CloudkittyHandler(ClientHandler):
    def __init__(self, sess, log_file, log_level):
        super().__init__(sess, log_file, log_level)
        self.__LOGGER = create_logger(__name__, self._LOG_FILE, self._LOG_LEVEL)
        self.client = self.__get_client(self._SESSION)

    def __get_client(self, sess):
        start_time = time.time()
        error = None
        while time.time() - start_time < 30:  # Try for up to 30 seconds
            try:
                client = ck_client.Client(version='2', session=sess)
                self.__LOGGER.debug("SUCCESS - CloudKitty client connected")
                return client # Exit if client creation is successful
            except Exception as e:
                self.__LOGGER.warning(f"Failed to create CloudKitty client: {type(e).__name__} - {e} - Retrying...")
                error = e
                time.sleep(1)  # Wait for a second before retrying
        self.__LOGGER.error(f"Failed to create CloudKitty client after multiple attempts : {type(error).__name__} - {error}")
        raise error

    def get_rating_summary(self, kwargs**):
        try:
            summary = self.client.summary.get_summary(kwargs**)
            return summary
        except Exception as e:
            self.__LOGGER.error(f"An unexpected error : {type(e).__name__} - {e}")
            raise e 

    def close(self):
        self.__LOGGER.debug("Closing CloudKitty Client Connection")
        self.client = None
        super().close()
