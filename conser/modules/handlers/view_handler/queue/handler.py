# Local Imports
from conser.utils.service_logger import create_logger
from conser.factory.abs_classes.handlers import AbsViewHandler
import conser.exceptions as EXCP
import conser.utils.common as UTILS

# Py Packages
import time

class QueueHandler(AbsViewHandler):
    """
    The Queue Handler's main purpose is to listen to the message queue of the configured
    cloud and intercept incoming messages for specific events. 

    This is done utilizing the cloud client's mq component functions

    Valid Message Queues as of v1.2.0 are:
    Openstack -> Rabbit MQ
    """
    ############
    # DEFAULTS #
    ############

    ########
    # INIT #
    ########
    def __init__(self, clients_dict, log_file, log_level):
        self._LOG_LEVEL = log_level
        self._LOG_FILE = log_file
        self.__LOGGER = create_logger(__name__, self._LOG_FILE, self._LOG_LEVEL)
        self.clients = clients_dict

    def run_process(self):
        """
        The main running loop of the Handler.
        """
        if 'cloud' not in self.clients or not self.clients['cloud']:
            raise EXCP.NoClientFound('cloud')

        self.__LOGGER.info("Starting - Message Queue listening")
        self.clients['cloud'].start_message_queue()

    def disconnect(self):
        """
        Function for disconnecting all clients before garbage collection.
        """
        self.__LOGGER.info("Disconnecting Queue Clients and Components")
        for name, client in self.clients.items():
            client.disconnect()
        self.clients = None