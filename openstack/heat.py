# Local Imports
from utils.service_logger import create_logger

# Py Packages
import time

# Openstack Packages
from heatclient import client as  h_client

class HeatHandler:
    def __init__(self, sess, log_level):
        self.__LOGGER = create_logger(__name__, '/var/log/concertim-openstack-service-opt.log', log_level)
        self.client = self.__get_client(sess)

    def __get_client(self, sess):
        start_time = time.time()
        while time.time() - start_time < 30:  # Try for up to 30 seconds
            try:
                client = h_client.Client(version='1', session=sess)
                self.__LOGGER.debug("SUCCESS - Heat client connected")
                return client# Exit if client creation is successful
            except Exception as e:
                self.__LOGGER.error(f"Failed to create Heat client: {e}. Retrying...")
                time.sleep(1)  # Wait for a second before retrying

        raise Exception("Failed to create Heat client after multiple attempts.")


    def list_stacks(self, project_id=None):

        self.__LOGGER.debug(f"Getting all stacks")

        stacks = self.client.stacks.list()

        self.__LOGGER.debug(f"stacks : {stacks}")

        return stacks

        
    def get_stack(self, stack_id):

        self.__LOGGER.debug(f"Getting stack id {stack_id}")

        stack = self.client.stacks.get(stack_id=stack_id)

        #self.__LOGGER.debug(f"stack  : {stack}")

        return stack

    def list_stack_resources(self, stack_id, **kwargs):

        stack_resource = self.client.resources.list(stack_id=stack_id, **kwargs)
        return stack_resource

    
    def close(self):
        self.__LOGGER.debug("Closing Heat Client Connection")
        self.client = None