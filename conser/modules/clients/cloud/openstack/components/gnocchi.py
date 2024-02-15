# Local Imports
from conser.utils.service_logger import create_logger
from conser.modules.clients.cloud.openstack.components.base import OpstkBaseComponent
# Py Packages
import sys
import time
# Openstack Packages
import gnocchiclient.v1.client as g_client
#import gnocchiclient.exceptions

class GnocchiComponent(OpstkBaseComponent):
    def __init__(self, sess, log_file, log_level):
        super().__init__(sess, log_file, log_level)
        self.__LOGGER = create_logger(__name__, self._LOG_FILE, self._LOG_LEVEL)
        self.__LOGGER.info("CREATING GNOCCHI COMPONENT")
        self.client = self.get_connection_obj(self._SESSION)

    def get_connection_obj(self, sess):
        start_time = time.time()
        error = None
        while time.time() - start_time < 30:  # Try for up to 30 seconds
            try:
                client = g_client.Client(session=sess)
                self.__LOGGER.debug("SUCCESS - Gnocchi client connected")
                return client # Exit if client creation is successful
            except Exception as e:
                self.__LOGGER.warning(f"Failed to create Gnocchi client : {type(e).__name__} - {e} - Retrying...")
                error = e
                time.sleep(1)  # Wait for a second before retrying
        self.__LOGGER.error(f"Failed to create Gnocchi client after multiple attempts : {type(error).__name__} - {error}")
        raise error

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
            self.__LOGGER.error(f"An unexpected error occured during the above metric call : {type(e).__name__} - {e}")
            self.__LOGGER.warning(f"Returning empty list due to [{type(e).__name__}]")
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
            self.__LOGGER.error(f"An unexpected error occured during the above metric call : {type(e).__name__} - {e}")
            self.__LOGGER.warning(f"Returning empty list due to [{type(e).__name__}]")
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
            self.__LOGGER.error(f"An unexpected error occured during the above metric call : {type(e).__name__} - {e}")
            self.__LOGGER.warning(f"Returning empty list due to [{type(e).__name__}]")
            return []

    def disconnect(self):
        self.__LOGGER.debug("Disconnecting Gnocchi Component Connection")
        self.client = None
        super().disconnect()