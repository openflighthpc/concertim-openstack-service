# Local Imports
from con_opstk.utils.service_logger import create_logger
from con_opstk.data_handler.base import BaseHandler
from con_opstk.data_handler.exceptions import ViewNotFound
import con_opstk.app_definitions as app_paths
# Py Packages
import sys
import pickle
import os
import datetime

class BillingHandler(BaseHandler):
    DEFAULT_CLIENTS = ['keystone','cloudkitty']
    VIEW_PICKLE_FILE = app_paths.DATA_DIR + 'view.pickle'

    def __init__(self, config_obj, log_file, clients=None):
        self.clients = clients if clients else BillingHandler.DEFAULT_CLIENTS
        super().__init__(config_obj, log_file, self.clients)
        self.__LOGGER = create_logger(__name__, self._LOG_FILE, self._CONFIG['log_level'])
        self.view = None

    def update_cost(self, type, amt):
        #TODO
        # type - rack, user, device
        # amt - cost

    def read_view(self):
        self.__LOGGER.debug(f"Loading View from '{BillingHandler.VIEW_PICKLE_FILE}'")
        found = False
        attempts = 0
        view = None
        while not found:
            view = self.__load_view()
            if view:
                found = True
                break
            elif attempts > 10:
                self.__LOGGER.error(f"Could not load '{BillingHandler.VIEW_PICKLE_FILE}'")
                raise ViewNotFound(f"Max attempts exceeded")
            else:
                self.__LOGGER.debug(f"....")
                attempts += 1
                time.sleep(3)
                continue
        if found and view:
            self.view = view
        else:
            self.__LOGGER.error(f"Could not load View from '{BillingHandler.VIEW_PICKLE_FILE}' - {type(e).__name__} - {e} - {type(e).__name__} - {e} - {sys.exc_info()[2].tb_frame.f_code.co_filename} - {sys.exc_info()[2].tb_lineno}")
            raise ViewNotFound(f"Could not load View from '{BillingHandler.VIEW_PICKLE_FILE}'")

    def __load_view(self):
        try:
            with open(BillingHandler.VIEW_PICKLE_FILE, 'rb') as pkl_file:
                self.view = pickle.load(pkl_file)
            self.__LOGGER.debug(f"Success - View loaded from '{BillingHandler.VIEW_PICKLE_FILE}' and set to self.view")
            return True
        except FileNotFoundError as e:
            self.__LOGGER.warning(f"No pickle file '{BillingHandler.VIEW_PICKLE_FILE}' found")
            return False
        except Exception as e:
            self.__LOGGER.error(f"Could not load View from '{BillingHandler.VIEW_PICKLE_FILE}' - {type(e).__name__} - {e} - {type(e).__name__} - {e} - {sys.exc_info()[2].tb_frame.f_code.co_filename} - {sys.exc_info()[2].tb_lineno}")
            raise e