# Local Imports
from conser.utils.service_logger import create_logger
from conser.modules.clients.cloud.openstack.components.base import OpstkBaseComponent
# Py Packages
import sys
import time
import logging
# Openstack Packages
from cloudkittyclient import client as ck_client

    
class CloudkittyComponent(OpstkBaseComponent):

    def __init__(self, sess, log_file, log_level):
        super().__init__(sess, log_file, log_level)
        self.__LOGGER = create_logger(__name__, self._LOG_FILE, self._LOG_LEVEL)
        self.__LOGGER.info("CREATING CLOUDKITTY COMPONENT")
        self.cloudkitty_client = self.get_connection_obj(self._SESSION)

    def get_connection_obj(self, sess):
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

    # Function to get the detailed summary (openstack rating summary get) for each tenant in one dictionary
    def get_rating_summary_all(self, tenants):
        self.__LOGGER.debug("Getting rating summary for " + str(len(tenants)) + " tenants")
        all_tenants_rating_summary = {}

        try:
            rating_summary_dict = self.cloudkitty_client.summary.get_summary(
                all_tenants=True, groupby=["tenant_id", "res_type"]
            )["summary"]
            self.__LOGGER.debug("rating_summary_dict: %s", rating_summary_dict)
            for tenant in tenants:
                for usage in rating_summary_dict:
                    if usage["tenant_id"] == str(tenant):
                        self.__LOGGER.debug(
                            "building usage: %s for tenant: %s", usage, str(tenant)
                        )
                        if str(tenant) in all_tenants_rating_summary:
                            all_tenants_rating_summary[str(tenant)].append(usage)
                        else:
                            all_tenants_rating_summary[str(tenant)] = [usage]
            self.__LOGGER.debug("all_tenants_rating_summary: %s", all_tenants_rating_summary)
            return all_tenants_rating_summary
        except Exception as e:
            self.__LOGGER.error("Error getting rating summary: %s", e)
            raise e

    def get_rating_summary(self, obj_id_field, obj_id, begin, end):
        if obj_id:
            self.__LOGGER.debug("Getting rating summary for resource " + obj_id)
        else:
            self.__LOGGER.warning("Empty obj_id passed to get_rating_summary")
            return {}

        resource_rating_summary = {}
        try:
            rating_summary_dict = self.cloudkitty_client.summary.get_summary(
                filters = {obj_id_field:obj_id,}, \
                groupby=[obj_id_field, 'type'], begin=begin, end=end
            )
            self.__LOGGER.debug("rating_summary_dict: %s", rating_summary_dict)

            rate_index = rating_summary_dict["columns"].index('rate')
            type_index = rating_summary_dict["columns"].index('type')
            if not(rate_index >=0 and type_index >=0) :
                return {}

            for result in rating_summary_dict["results"]:
                resource_rating_summary[result[type_index]] = result[rate_index]

            self.__LOGGER.debug("Object rating summary: %s", resource_rating_summary)
            return resource_rating_summary
        except ValueError as ve:
            self.__LOGGER.error("Cloudkitty rating empty for object %s", obj_id)
            raise ve
        except Exception as e:
            self.__LOGGER.error("Error getting rating summary: %s", e)
            raise e

    def disconnect(self):
        self.__LOGGER.debug("Disconnecting CloudKitty Component Connection")
        self.client = None
        super().disconnect()