# Local Imports
from utils.service_logger import create_logger

# Py Packages
import time

# Openstack Packages
import gnocchiclient.v1.client as g_client

class GnocchiHandler:
    def __init__(self, sess, log_file, log_level):
        self.__LOGGER = create_logger(__name__, log_file, log_level)
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

    def search_resource(self, query, resource_type=None,details=True):
        if resource_type:
            return self.client.resource.search(resource_type=resource_type, query=query, details=details)
        return self.client.resource.search(query=query, details=details)

    def get_aggregate(self, op, start, stop):
        tup = self.client.aggregates.fetch(operations=op, start=start,stop=stop)['measures']['aggregated'][0]
        return tup

    def get_metric_measure(self, metric, start, stop):
        tup = self.client.metric.get_measures(metric=metric, start=start, stop=stop)[0]
        return tup

    def close(self):
        self.__LOGGER.debug("Closing Gnocchi Client Connection")
        self.client = None