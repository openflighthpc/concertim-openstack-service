# Local Imports
from con_opstk.utils.service_logger import create_logger
import os
from con_opstk.data_handler.base import BaseHandler

# Parent Class for all Billing Services
class BillingService:
    def __init__(self, config_obj, log_file):
        self._CONFIG = config_obj
        self._LOG_FILE = log_file
        self.__LOGGER = create_logger(__name__, self._LOG_FILE, self._CONFIG['log_level'])

    def trigger_driver(self):
        pass

    def get_status(self):
        pass
