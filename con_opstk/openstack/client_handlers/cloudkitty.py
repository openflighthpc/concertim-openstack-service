# Local Imports
from con_opstk.utils.service_logger import create_logger
from con_opstk.openstack.client_handlers.client_base import ClientHandler
# Py Packages
import sys
import time
import logging
# Openstack Packages
from cloudkittyclient import client as ck_client

    
class CloudkittyHandler(ClientHandler):

    def __init__(self, sess, log_file, log_level):
        super().__init__(sess, log_file, log_level)
        self.__LOGGER = create_logger(__name__, self._LOG_FILE, self._LOG_LEVEL)
        self.cloudkitty_client = self.__get_client(self._SESSION)

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


    def get_rating_summary(self, **kwargs):
        self.__LOGGER.info(f"Getting rating summary - Extra Args: {kwargs.items()}")
        try:
            summary = self.client.summary.get_summary(**kwargs)
            return summary
        except Exception as e:
            self.__LOGGER.error(f"An unexpected error : {type(e).__name__} - {e}")
            raise e


    # Function to get the detailed summary (openstack rating summary get) for each tenant in one dictionary
    def get_rating_summary_all(self, tenants):
        self.__LOGGER.info("Getting rating summary for " + str(len(tenants)) + " tenants")
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
            sys.exit(1)

    # Function to get the detailed summary (openstack rating summary get) for each tenant in one dictionary
    def get_rating_summary_project(self, project_id, begin, end):
        if project_id:
            self.__LOGGER.info("Getting rating summary for project " + project_id)
        else:
            self.__LOGGER.info("Empty resource id passed to get_rating_summary_project")
            return {}

        project_rating_summary = {}

        try:
            rating_summary_dict = self.cloudkitty_client.summary.get_summary(
                filters = {'project_id' : project_id}, \
                groupby=['project_id', 'type'], begin=begin, end=end
            )
            self.__LOGGER.debug("rating_summary_dict: %s", rating_summary_dict)

            rate_index = rating_summary_dict["columns"].index('rate')
            type_index = rating_summary_dict["columns"].index('type')

            if not(rate_index >=0 and type_index >=0):
                return {}
                #raise Exception("rate and type not present in summary result")

            for result in rating_summary_dict["results"]:
                project_rating_summary[result[type_index]] = result[rate_index]

            self.__LOGGER.debug("Project rating summary: %s", project_rating_summary)
            return project_rating_summary

        except ValueError:
            self.__LOGGER.error("Cloudkitty rating empty for project %s", project_id)
        except Exception as e:
            self.__LOGGER.error("Error getting rating summary: %s", e)
        return {}

    def get_rating_summary_resource(self, resource_id, begin, end, resource_type):

        if len(resource_id) >= 1:
            self.__LOGGER.info("Getting rating summary for resource " + resource_id)
        else:
            self.__LOGGER.info("Empty resource id passed to get_rating_summary_resource")
            return {}


        resource_rating_summary = {}

        try:
            rating_summary_dict = self.cloudkitty_client.summary.get_summary(
                filters = {'id' : resource_id, 'type' : resource_type}, \
                groupby=['id', 'type'], begin=begin, end=end
            )

            self.__LOGGER.debug("rating_summary_dict: %s", rating_summary_dict)


            rate_index = rating_summary_dict["columns"].index('rate')
            type_index = rating_summary_dict["columns"].index('type')

            if not(rate_index >=0 and type_index >=0) :
                return {}
                #raise Exception("rate and type not present in summary result")

            for result in rating_summary_dict["results"]:
                resource_rating_summary[result[type_index]] = result[rate_index]

            self.__LOGGER.debug("Resource rating summary: %s", resource_rating_summary)

            return resource_rating_summary

        except ValueError:
            self.__LOGGER.error("Cloudkitty rating empty for resource %s", resource_id)
        except Exception as e:
            self.__LOGGER.error("Error getting rating summary: %s", e)

        return {}
    

    def close(self):
        self.__LOGGER.debug("Closing CloudKitty Client Connection")
        self.client = None
        super().close()