# Local Imports
from con_opstk.utils.service_logger import create_logger

# Py Packages
import sys
import json
# Disable insecure warnings  
import requests
requests.packages.urllib3.disable_warnings() 

class HostbillService(object):
    def __init__(self, config_obj, log_file):
        self._CONFIG = config_obj
        self._LOG_FILE = log_file
        self.__LOGGER = create_logger(__name__, self._LOG_FILE, self._CONFIG['log_level'])

    # TODO: add hostbill helper stuff