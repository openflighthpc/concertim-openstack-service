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

    def get_aggregate(self, operations, granularity=None, start=None, stop=None):
        try:
            args = {'operations':operations, 'granularity':granularity, 'start':start, 'stop':stop}
            not_none_args = {k:v for k,v in args.items() if v is not None}
            self.__LOGGER.debug(f"Getting aggregates: [{not_none_args}]")
            aggregates = self.client.aggregates.fetch(**not_none_args)['measures']['aggregated']
            return aggregates
        except Exception as e:
            self.__LOGGER.error(f"FAILED - attempt : [{not_none_args}]")
            self.__LOGGER.error(f"An unexpected error occured during the above metric call : {e}")
            self.__LOGGER.warning(f"Returning empty list due to error")
            return []

    def get_metric_measure(self, metric, granularity=None, aggregation=None, refresh=True, start=None, stop=None, limit=None):
        try:
            args = {'metric':metric, 'granularity':granularity, 'aggregation':aggregation, 'refresh':refresh, 'start':start, 'stop':stop, 'limit':limit}
            not_none_args = {k:v for k,v in args.items() if v is not None}
            self.__LOGGER.debug(f"Getting measures: [{not_none_args}]")
            measures = self.client.metric.get_measures(**not_none_args)
            return measures
        except Exception as e:
            self.__LOGGER.error(f"FAILED - attempt : [{not_none_args}]")
            self.__LOGGER.error(f"An unexpected error occured during the above metric call : {e}")
            self.__LOGGER.warning(f"Returning empty list due to error")
            return []

    def get_metric_aggregate(self, metric, granularity=None, aggregation=None, refresh=True, start=None, stop=None, limit=None):
        try:
            args = {'metric':metric, 'granularity':granularity, 'aggregation':aggregation, 'refresh':refresh, 'start':start, 'stop':stop, 'limit':limit}
            not_none_args = {k:v for k,v in args.items() if v is not None}
            self.__LOGGER.debug(f"Getting aggregation: [{not_none_args}]")
            measures = self.client.metric.aggregation(**not_none_args)
            return measures
        except Exception as e:
            self.__LOGGER.error(f"FAILED - attempt : [{not_none_args}]")
            self.__LOGGER.error(f"An unexpected error occured during the above metric call : {e}")
            self.__LOGGER.warning(f"Returning empty list due to error")
            return []

    def close(self):
        self.__LOGGER.debug("Closing Gnocchi Client Connection")
        self.client = None