# Local Imports
from con_opstk.utils.service_logger import create_logger
from con_opstk.openstack.openstack import OpenstackService
from con_opstk.concertim.concertim import ConcertimService
from con_opstk.openstack.exceptions import FailureToScrub, UnsupportedObject
import con_opstk.app_definitions as app_paths
# Py Packages
import sys
import importlib
import pickle

class BaseHandler(object):
    BILLING_SERVICES = {'killbill': 'KillbillService', 'hostbill': 'HostbillService'}
    BILLING_IMPORT_PATH = {'killbill': 'con_opstk.billing.killbill.killbill', 'hostbill': 'con_opstk.billing.hostbill.hostbill'}
    VIEW_PICKLE_FILE = app_paths.DATA_DIR + 'view.pickle'
    def __init__(self, config_obj, log_file, openstack_client_list, enable_concertim=True, billing_enabled=False):
        self._CONFIG = config_obj
        self._LOG_FILE = log_file
        self.__LOGGER = create_logger(__name__, self._LOG_FILE, self._CONFIG['log_level'])
        self.billing_service = self.__get_billing_service() if billing_enabled else None
        self.openstack_service = OpenstackService(self._CONFIG, self._LOG_FILE, client_list=openstack_client_list, billing_enabled=billing_enabled)
        self.concertim_service = ConcertimService(self._CONFIG, self._LOG_FILE) if enable_concertim else None
        self.view = None

    # Delete objects that were created before encountering an error ('orphans')
    # 'orphans' - Openstack objects to remove
    def __scrub(self, *orphans):
        try:
            self.__LOGGER.debug(f"Scrubbing orphaned objects")
            failed = []
            grouped_orphans = {'errors1':[],'errors2':[]}

            self.__LOGGER.debug(f"Grouping orphans by handler")
            for orphan in orphans:
                orphan_tree = getattr(orphan, '__module__', None)
                orphan_root = orphan_tree.split('.')[0] if orphan_tree else None
                if not orphan_root:
                    self.__LOGGER.warning(f"Failed to get root module for '{orphan}' - adding to errors list")
                    grouped_orphans['errors1'].append(f"[Orphan:{orphan}, Error: Root Module is None]")
                    continue
                orphan_client_name = orphan_root.replace("client","")
                if orphan_client_name in self.openstack_service._handlers_key_map:
                    if orphan_client_name in grouped_orphans:
                        grouped_orphans[orphan_client_name].append(orphan)
                    else:
                        grouped_orphans[orphan_client_name] = [].append(orphan)
                else:
                    self.__LOGGER.warning(f"Failed to locate handler for '{orphan}' - adding to errors list")
                    grouped_orphans['errors2'].append(f"[Orphan:{orphan}, Error: Handler not found, Details: Module={orphan_tree},ClientType={orphan_client_name}]")
            if grouped_orphans['errors1'] or grouped_orphans['errors2']:
                err_list = grouped_orphans['errors1'] + grouped_orphans['errors2']
                err_msg = f"Some orphans could not be grouped : {err_list}"
                if grouped_orphans['errors2']:
                    err_msg += f" - Available handlers at runtime : {self.openstack_service._handlers_key_map}"
                self.__LOGGER.error(err_msg)
                raise FailureToScrub(f"Grouping Failed - {err_list}")

            self.__LOGGER.debug(f"Deleting groupped orphans")
            for client_name in (x for x in grouped_orphans if x not in ['errors1','errors2']):
                handler = self.openstack_service.handlers[self.openstack_service._handlers_key_map[client_name]]
                try:
                    successful = handler.delete(*grouped_orphans[client_name])
                    if not successful:
                        failed.append(f"[Handler:{client_name}, Reason:General - check warnings for details]")
                except UnsupportedObject as e:
                    failed.append(f"[Handler:{client_name}, Reason:UnsupportedObject - {e}]")
                    continue
            
            if failed:
                self.__LOGGER.error(f"Some handlers failed to delete all objects - {failed}")
                raise FailureToScrub(f"Deleting failed - {failed}")
            else:
                self.__LOGGER.debug(f"Successfully Scrubbed orphaned objects")
                return True
        except Exception as e:
            self.__LOGGER.error(f"{type(e).__name__} - {e} - {sys.exc_info()[2].tb_frame.f_code.co_filename} - {sys.exc_info()[2].tb_lineno}")
            raise e

    def read_view(self):
        self.__LOGGER.debug(f"Loading View from '{BaseHandler.VIEW_PICKLE_FILE}'")
        found = False
        attempts = 0
        while not found:
            ret = self.__load_view()
            if ret == True:
                found = True
                break
            elif attempts > 10:
                self.__LOGGER.error(f"Could not load '{BaseHandler.VIEW_PICKLE_FILE}'")
                raise ViewNotFound(f"Max attempts exceeded")
            else:
                self.__LOGGER.debug(f"....")
                attempts += 1
                time.sleep(3)
                continue
        if found == True:
            self.__LOGGER.info(f" View Loaded Successfully {self.view}")
        else:
            self.__LOGGER.error(f"Could not load View from '{BaseHandler.VIEW_PICKLE_FILE}' - {type(e).__name__} - {e} - {type(e).__name__} - {e} - {sys.exc_info()[2].tb_frame.f_code.co_filename} - {sys.exc_info()[2].tb_lineno}")
            raise ViewNotFound(f"Could not load View from '{BaseHandler.VIEW_PICKLE_FILE}'")

    def __load_view(self):
        try:
            with open(BaseHandler.VIEW_PICKLE_FILE, 'rb') as pkl_file:
                self.view = pickle.load(pkl_file)
            self.__LOGGER.debug(f"Success - View loaded from '{BaseHandler.VIEW_PICKLE_FILE}' and set to self.view")
            return True
        except FileNotFoundError as e:
            self.__LOGGER.warning(f"No pickle file '{BaseHandler.VIEW_PICKLE_FILE}' found")
            return False
        except Exception as e:
            self.__LOGGER.error(f"Could not load View from '{BaseHandler.VIEW_PICKLE_FILE}' - {type(e).__name__} - {e} - {type(e).__name__} - {e} - {sys.exc_info()[2].tb_frame.f_code.co_filename} - {sys.exc_info()[2].tb_lineno}")
            raise e

    def __get_billing_service(self):
        self.__LOGGER.debug("Creating configured billing service")
        billing_app = self._CONFIG['billing_platform']
        ImportedService = getattr(importlib.import_module(BaseHandler.BILLING_IMPORT_PATH[billing_app]), BaseHandler.BILLING_SERVICES[billing_app])
        billing_service = ImportedService(self._CONFIG, self._LOG_FILE)
        return billing_service

    def disconnect(self):
        self.__LOGGER.info("Disconnecting and destroying all base services")
        self.openstack_service.disconnect()
        if self.concertim_service:
            self.concertim_service.disconnect()
        self.openstack_service = None
        self.concertim_service = None
        self.__LOGGER.info("Disconnect complete\n")
