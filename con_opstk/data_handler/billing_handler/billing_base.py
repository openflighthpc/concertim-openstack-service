# Local Imports
from con_opstk.utils.service_logger import create_logger
from con_opstk.data_handler.base import BaseHandler
from con_opstk.data_handler.exceptions import ViewNotFound

import con_opstk.app_definitions as app_paths
# Py Packages
import sys
import pickle
import time
from dateutil.parser import parse as dt_parse

class BillingHandler(BaseHandler):
    DEFAULT_CLIENTS = ['keystone','cloudkitty','heat','nova']
    DEFAULT_CREDIT_THRESHOLD = 24
    def __init__(self, config_obj, log_file, clients=None):
        self.clients = clients if clients else BillingHandler.DEFAULT_CLIENTS
        super().__init__(config_obj, log_file, self.clients, enable_concertim=True, billing_enabled=True)
        self.__LOGGER = create_logger(__name__, self._LOG_FILE, self._CONFIG['log_level'])
        if 'credit_threshold' in self._CONFIG and self._CONFIG['credit_threshold']:
            self._credit_threshold = float(self._CONFIG['credit_threshold'])
        else:
            self._credit_threshold = float(BillingHandler.DEFAULT_CREDIT_THRESHOLD)


    def update_cost(self, type, amt):
        pass
        
    def update_team_cost_concertim(self, openstack_project_id, begin, end, billing_account_id):
        self.__LOGGER.info("\n\n********************************************\n\n")
        self.__LOGGER.info ("*** Updating Team cost %s (%s, %s) ***", openstack_project_id, begin, end)
        
        user_found = False
        user = None
        for tup in self.view.teams:
            team = self.view.teams[tup]
            # Checking for existence of associated openstack project id
            if team.openstack_project_id == openstack_project_id:
                team_found = True
                break
        if team_found == False or user == None:
            return 0

        # Obtain usage details from cloudkitty
        rating_summary = self.openstack_service.get_ratings_project(team.openstack_project_id, begin=begin, end=end)

        project_cost = 0

        for type_res in rating_summary:
            project_cost  = project_cost + float(rating_summary[type_res])

        # Obtaining Account Credits
        account_credits = self.billing_service.get_credits(billing_account_id)['data']
        remaining_credits = float(account_credits) - project_cost

        if remaining_credits <= self._credit_threshold:
            self._account_shutdown(user.id)

        # Update Team Cost in Concertim
        try:
            self.concertim_service.update_team(ID=team.id[0], variables_dict ={'cost' : project_cost, 'billing_period_start' : begin, 'billing_period_end' : end, 'credits' : remaining_credits})
        except Exception as e:
            self.__LOGGER.debug(f" Exception Occurred : {type(e).__name__} - {e} - {sys.exc_info()[2].tb_frame.f_code.co_filename} - {sys.exc_info()[2].tb_lineno}")

        # Update Rack Cost
        for tup in self.view.racks:
            rack = self.view.racks[tup]
            if rack.team_id == team.id[0]:
                self.update_rack_cost_concertim(concertim_rack_id = rack.id[0], begin=begin, end=end)

    
    # Update Rack Cost in Concertim
    def update_rack_cost_concertim(self, concertim_rack_id, begin, end ):
        self.__LOGGER.info("\n\n********************************************\n\n")
        self.__LOGGER.info ("*** Updating Rack cost %s (%s, %s) ***", concertim_rack_id, begin, end)
        #rack_obj = self.update_handler.search_view('racks', 'concertim',        concertim_rack_id)
        #self.__LOGGER.info(f"{rack_obj}") 
        for tup in self.view.racks:
            rack = self.view.racks[tup]
            self.__LOGGER.info(f"{rack}")

            # Checking for existence of Openstack stack id
            if rack.id[0] == None or rack.id[1] == None:
                continue

            rack_cost = 0
            for device_id in rack.devices:
                device_cost = self.update_device_cost_concertim(concertim_device_id = device_id, begin=begin, end=end)
                rack_cost = rack_cost + device_cost 

            # Updating Rack Cost in Concertim
            try:
                self.concertim_service.update_rack(ID=rack.id[0], variables_dict ={'cost' : rack_cost})
            except Exception as e:
                self.__LOGGER.debug(f" Exception Occurred : {type(e).__name__} - {e} - {sys.exc_info()[2].tb_frame.f_code.co_filename} - {sys.exc_info()[2].tb_lineno}")
                

    # Update Device Cost in Concertim
    def update_device_cost_concertim(self, concertim_device_id, begin, end):
        self.__LOGGER.info("\n\n********************************************\n\n")
        self.__LOGGER.info ("*** Updating Device concertim_device_id %s (%s, %s) ***", concertim_device_id, begin, end)
        
        #device_obj = self.update_handler.search_view('devices', 'concertim',        concertim_device_id)
        #self.__LOGGER.info(f"{device_obj}")

        device_found = False
        device = False
        for tup in self.view.devices:
            device = self.view.devices[tup]
            self.__LOGGER.info(f"{device}")
            # Checking for existence of Openstack device id
            if device.id[0] == concertim_device_id and device.id[1] != None:
                device_found = True
                break
            
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
            self.concertim_service.update_device(ID=concertim_device_id, variables_dict ={'cost' : device_cost})
        except Exception as e:
            self.__LOGGER.debug(f" Exception Occurred : {type(e).__name__} - {e} - {sys.exc_info()[2].tb_frame.f_code.co_filename} - {sys.exc_info()[2].tb_lineno}")
        return device_cost

    def _convert_date(self, datetime_str):
        return dt_parse(datetime_str).strftime('%Y-%m-%d')

    def _account_shutdown(self, user_id_tup):
        self.__LOGGER.info(f"User <ID:{user_id_tup}> has crossed the allowed credit threshold - starting shutdown procedure for User's racks")
        for rack_concertim_id in self.view.users[user_id_tup].racks:
            for rack_id_tup in self.view.racks:
                if rack_concertim_id == rack_id_tup[0]:
                    self.openstack_service.update_stack_status(rack_id_tup[1], 'suspend')
        self.__LOGGER.debug(f"Shutdown procedure completed.")
        return True

    def disconnect(self):
        self.__LOGGER.info(f"Disconnecting Billing base connections")
        self.view = None
        super().disconnect()
            

