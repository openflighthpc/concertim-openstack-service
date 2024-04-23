# Local Imports
from conser.utils.service_logger import create_logger
from conser.modules.clients.cloud.openstack.components.base import OpstkBaseComponent
import conser.exceptions as EXCP
# Py Packages
import time
# Openstack Packages
from cinderclient import client as c_client
from cinderclient.exceptions import NotFound as NotFound
#import heatclient.exceptions

class CinderComponent(OpstkBaseComponent):
    def __init__(self, sess, log_file, log_level):
        super().__init__(sess, log_file, log_level)
        self.__LOGGER = create_logger(__name__, self._LOG_FILE, self._LOG_LEVEL)
        self.__LOGGER.info("CREATING CINDER COMPONENT")
        self.client = self.get_connection_obj(self._SESSION)

    def get_connection_obj(self, sess):
        start_time = time.time()
        error = None
        while time.time() - start_time < 30:  # Try for up to 30 seconds
            try:
                client = c_client.Client(version='3', session=sess)
                self.__LOGGER.debug("SUCCESS - Cinder client connected")
                return client # Exit if client creation is successful
            except Exception as e:
                self.__LOGGER.warning(f"Failed to create Cinder client: {type(e).__name__} - {e} - Retrying...")
                error = e
                time.sleep(1)  # Wait for a second before retrying
        self.__LOGGER.error(f"Failed to create Cinder client after multiple attempts : {type(error).__name__} - {error}")
        raise error

    def get_volume(self, volume_id):
        try:
            return self.client.volumes.get(volume_id)
        except NotFound as e:
            raise EXCP.MissingCloudObject(f"{volume_id}")

    def get_project_quotas(self, project_id):
        try:
            return self.client.quotas.get(project_id)
        except Exception as e:
            self.__LOGGER.error(f"An unexpected error : {type(e).__name__} - {e}")
            raise e
