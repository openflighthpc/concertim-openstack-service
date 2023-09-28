# Local Imports
from con_opstk.utils.service_logger import create_logger
from con_opstk.data_handler.base import BaseHandler
from con_opstk.data_handler.exceptions import ViewNotFound
from con_opstk.data_handler.update_handler.update_base import UpdateHandler.search_view

import con_opstk.app_definitions as app_paths
# Py Packages
import sys
import pickle
import time
import logging

class BillingHandler(BaseHandler):
    DEFAULT_CLIENTS = ['keystone','cloudkitty']
    VIEW_PICKLE_FILE = app_paths.DATA_DIR + 'view.pickle'

    def __init__(self, config_obj, log_file, clients=None):
        self.clients = clients if clients else BillingHandler.DEFAULT_CLIENTS
        super().__init__(config_obj, log_file, self.clients, enable_concertim=True)
        self.__LOGGER = create_logger(__name__, self._LOG_FILE, self._CONFIG['log_level'])
        self.view = None

        


    def update_cost(self, type, amt):
        pass

    def read_view(self):
        self.__LOGGER.debug(f"Loading View from '{BillingHandler.VIEW_PICKLE_FILE}'")
        found = False
        attempts = 0

        while not found:
            ret = self.__load_view()
            if ret == True:
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
        if found == True:
            self.__LOGGER.info(f" View Loaded Successfully {self.view}")
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
        
    def update_user_cost_concertim(self, openstack_project_id, begin, end):
        logging.info("\n\n********************************************\n\n")
        logging.info ("*** Updating User cost %s (%s, %s) ***", openstack_project_id, begin, end)
        
        user_found = False
        user = None
        for tup in self.view.users:

            user = self.view.users[tup]

            # Checking for existence of associated openstack project id
            if user.openstack_project_id == openstack_project_id:
                user_found = True
                break

        if user_found == False or user == None:
            return 0

        # Obtain usage details from cloudkitty
        rating_summary = self.openstack_service.handlers['cloudkitty'].get_rating_summary_project(user.openstack_project_id, begin, end)

        project_cost = 0

        for type_res  in rating_summary:
            project_cost  = project_cost + float(rating_summary[type_res])


        # Update User Cost in Concertim
        try:
            self.update_handler.concertim_service.update_user(ID=user.id[0], variables_dict ={'cost' : project_cost, 'billing_period_start' : begin, 'billing_period_end' : end})

        except Exception as e:
            logging.debug(f" Exception Occurred : {type(e).__name__} - {e} - {sys.exc_info()[2].tb_frame.f_code.co_filename} - {sys.exc_info()[2].tb_lineno}")


        # Update Rack Cost
        for tup in self.view.racks:
            rack = self.view.racks[tup]

            if rack.user_id == user.id[0]:
                self.update_rack_cost_concertim(concertim_rack_id = rack.id[0], begin=begin, end=end)

    
    # Update Rack Cost in Concertim
    def update_rack_cost_concertim(self, concertim_rack_id, begin, end ):
        logging.info("\n\n********************************************\n\n")
        logging.info ("*** Updating Rack cost %s (%s, %s) ***", concertim_rack_id, begin, end)
        #rack_obj = self.update_handler.search_view('racks', 'concertim',        concertim_rack_id)
        
        #logging.info(f"{rack_obj}") 


        for tup in self.view.racks:
            rack = self.view.racks[tup]

            logging.info(f"{rack}")

            # Checking for existence of Openstack stack id
            if rack.id[0] == None or rack.id[1] == None:
                continue

            rack_cost = 0
            for device_id in rack.devices:
                
                device_cost = self.update_device_cost_concertim(concertim_device_id = device_id, begin=begin, end=end)
        
                rack_cost = rack_cost + device_cost 

            # Updating Rack Cost in Concertim
            try:
                self.update_handler.concertim_service.update_rack(ID=rack.id[0], variables_dict ={'cost' : rack_cost})

            except Exception as e:
                logging.debug(f" Exception Occurred : {type(e).__name__} - {e} - {sys.exc_info()[2].tb_frame.f_code.co_filename} - {sys.exc_info()[2].tb_lineno}")
                

    # Update Device Cost in Concertim
    def update_device_cost_concertim(self, concertim_device_id, begin, end):
        logging.info("\n\n********************************************\n\n")
        logging.info ("*** Updating Device concertim_device_id %s (%s, %s) ***", concertim_device_id, begin, end)
        
        #device_obj = self.update_handler.search_view('devices', 'concertim',        concertim_device_id)
        
        #logging.info(f"{device_obj}")

        device_found = False
        device = False

        for tup in self.view.devices:
            device = self.view.devices[tup]
            
            logging.info(f"{device}")

            # Checking for existence of Openstack device id
            if device.id[0] == concertim_device_id and device.id[1] != None:
                device_found = True
        
        if device_found == False or device == None:
            return 0

        openstack_instance_id = device.id[1]

        # Obtain usage details from cloudkitty
        rating_summary = self.openstack_service.handlers['cloudkitty'].get_rating_summary_resource(openstack_instance_id, begin, end, resource_type='instance' )

        device_cost = 0
        for type_res in rating_summary:
            device_cost = device_cost + float(rating_summary[type_res])
        

        # Updating Device Cost in Concertim
        try:
            self.update_handler.concertim_service.update_device(ID=concertim_device_id, variables_dict ={'cost' : device_cost})
        except Exception as e:
            logging.debug(f" Exception Occurred : {type(e).__name__} - {e} - {sys.exc_info()[2].tb_frame.f_code.co_filename} - {sys.exc_info()[2].tb_lineno}")


        return device_cost
            

