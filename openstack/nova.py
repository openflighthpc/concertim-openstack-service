from utils.service_logger import create_logger
import novaclient.client as n_client
import time

class NovaHandler:
    def __init__(self, sess):
        self._LOGGER = create_logger(__name__, '/var/log/concertim-openstack-service-opt.log', 'DEBUG')
        self.client = self._get_client(sess)

    def _get_client(self, sess):
        start_time = time.time()
        while time.time() - start_time < 30:  # Try for up to 30 seconds
            try:
                client = n_client.Client(version='2', session=sess)
                self._LOGGER.debug("SUCCESS - Nova client connected")
                return client# Exit if client creation is successful
            except Exception as e:
                self._LOGGER.error(f"Failed to create Nova client: {e}. Retrying...")
                time.sleep(1)  # Wait for a second before retrying

        raise Exception("Failed to create Nova client after multiple attempts.")

    def close(self):
        self._LOGGER.debug("Closing Nova Client Connection")
        self.client = None