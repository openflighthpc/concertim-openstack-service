# Local Imports
from con_opstk.utils.service_logger import create_logger
from con_opstk.data_handler.billing_handler.billing_base import BillingHandler
from con_opstk.billing.killbill.killbill import KillbillService
# Py Packages
import sys
import json

class KillbillHandler(BillingHandler):
    def __init__(self, config_obj, log_file, clients=None):
        self.clients = clients if clients else BillingHandler.DEFAULT_CLIENTS
        super().__init__(config_obj, log_file, self.clients)
        self.__LOGGER = create_logger(__name__, self._LOG_FILE, self._CONFIG['log_level'])
        self.killbill = KillbillService(self._CONFIG, self._LOG_FILE)

    #TODO: actual killbill 'run' logic