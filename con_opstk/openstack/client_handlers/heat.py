# Local Imports
from con_opstk.utils.service_logger import create_logger
from con_opstk.openstack.client_handlers.client_base import ClientHandler
# Py Packages
import sys
import time
# Openstack Packages
from heatclient import client as h_client
#import heatclient.exceptions

class HeatHandler(ClientHandler):
    def __init__(self, sess, log_file, log_level):
        super().__init__(sess, log_file, log_level)
        self.__LOGGER = create_logger(__name__, self._LOG_FILE, self._LOG_LEVEL)
        self.client = self.__get_client(self._SESSION)

    def __get_client(self, sess):
        start_time = time.time()
        error = None
        while time.time() - start_time < 30:  # Try for up to 30 seconds
            try:
                client = h_client.Client(version='1', session=sess)
                self.__LOGGER.debug("SUCCESS - Heat client connected")
                return client # Exit if client creation is successful
            except Exception as e:
                self.__LOGGER.warning(f"Failed to create Heat client: {type(e).__name__} - {e} - Retrying...")
                error = e
                time.sleep(1)  # Wait for a second before retrying
        self.__LOGGER.error(f"Failed to create Heat client after multiple attempts : {type(error).__name__} - {error}")
        raise error

    def list_stacks(self, **kwargs):
        try:
            self.__LOGGER.debug(f"Getting stacks list - Extra Args: {kwargs.items()}")
            stacks = self.client.stacks.list(**kwargs)
            return stacks
        except Exception as e:
            self.__LOGGER.error(f"An unexpected error : {type(e).__name__} - {e}")
            raise e

    def get_stack(self, stack_id):
        try:
            self.__LOGGER.debug(f"Getting stack : {stack_id}")
            stack = self.client.stacks.get(stack_id=stack_id)
            return stack
        except Exception as e:
            self.__LOGGER.error(f"An unexpected error : {type(e).__name__} - {e}")
            raise e

    def list_stack_resources(self, stack_id, **kwargs):
        try:
            self.__LOGGER.debug(f"Getting resource(s) for stack : {stack_id} - Extra Args: {kwargs.items()}")
            stack_resource = self.client.resources.list(stack_id=stack_id, **kwargs)
            return stack_resource
        except Exception as e:
            self.__LOGGER.error(f"An unexpected error : {type(e).__name__} - {e}")
            raise e

    def list_stack_output(self,stack_id):
        try:
            self.__LOGGER.debug(f"Getting output list for stack : {stack_id}")
            stack_outputs_list = self.client.stacks.output_list(stack_id)
            return stack_outputs_list['outputs']
        except Exception as e:
            self.__LOGGER.error(f"An unexpected error : {type(e).__name__} - {e}")
            raise e

    def show_output(self,stack_id,output_key):
        try:
            stack_output_details = self.client.stacks.output_show(stack_id,output_key)
            return stack_output_details['output']
        except Exception as e:
            self.__LOGGER.error(f"An unexpected error : {type(e).__name__} - {e}")
            raise e

    def destroy_stack(self, stack_id):
        try:
            return self.client.stacks.delete(stack_id)
        except Exception as e:
            self.__LOGGER.error(f"An unexpected error : {type(e).__name__} - {e}")
            raise e

#     heat client doesn't wait to see if successful, so an error is not captured in the normal
#     update status workflow.
#     def suspend_stack(self, stack_id):
#         try:
#             self.client.actions.suspend(stack_id)
#             return True
#         # TODO: put in exceptions that match the failing from instance mismatch status
#         #except <heat exception> as e:
#         #    self.__LOGGER.warning(f"An unexpected instance conflict caused suspend of stack {stack_id} to fail")
#         #    return e
#         except Exception as e:
#             self.__LOGGER.error(f"An unexpected error : {type(e).__name__} - {e}")
#             raise e

    def close(self):
        self.__LOGGER.debug("Closing Heat Client Connection")
        self.client = None
        super().close()
