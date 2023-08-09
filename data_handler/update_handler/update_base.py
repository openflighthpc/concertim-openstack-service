# Local Imports
from utils.service_logger import create_logger
from data_handler.base import BaseHandler
from concertim.utils.view import ConcertimOpenstackView
from concertim.components.device import ConcertimDevice
from concertim.components.rack import ConcertimRack
from concertim.components.template import ConcertimTemplate
from concertim.components.user import ConcertimUser
from concertim.components.location import Location
# Py Packages
import sys
import pickle
import os

class UpdateHandler(BaseHandler):
    DEFAULT_CLIENTS = ['keystone','nova','heat']
    DATA_DIR = '/var/lib/concertim-openstack-service/data/'
    VIEW_PICKLE_FILE = DATA_DIR + 'view.pickle'
    __DATA = [VIEW_PICKLE_FILE]
    CONCERTIM_STATE_MAP = {
        'DEVICE':{
            'ACTIVE': ['active', 'running'],
            'STOPPED': ['stopped','suspended'],
            'IN_PROGRESS': ['building', 'deleting', 'scheduling', 'networking', 'block_device_mapping', 'spawning'],
            'FAILED': []
        },
        'RACK':{
            'ACTIVE': ['CREATE_COMPLETE','RESUME_COMPLETE'],
            'STOPPED': ['SUSPEND_COMPLETE'],
            'IN_PROGRESS': ['CREATE_IN_PROGRESS','SUSPEND_IN_PROGRESS','DELETE_IN_PROGRESS'],
            'FAILED': ['CREATE_FAILED','DELETE_FAILED']
        }
    }
    def __init__(self, config_obj, log_file, clients=None):
        self.clients = clients if clients else UpdateHandler.DEFAULT_CLIENTS
        super().__init__(config_obj, log_file, self.clients)
        self.__LOGGER = create_logger(__name__, self._LOG_FILE, self._CONFIG['log_level'])
        self.view = ConcertimOpenstackView()
        self._default_rack_height = int(self._CONFIG['concertim']['default_rack_height']) if 'default_rack_height' in self._CONFIG['concertim'] else 42
        self.load_view()

    # Controller method for populating self.view with data from concertim app
    def populate_view(self):
        self.__LOGGER.info(f"Starting - Populating Concertim View")
        self.fetch_concertim_users()
        self.fetch_concertim_templates()
        self.fetch_concertim_racks()
        self.fetch_concertim_devices()
        self.map_view_components()
        self.__LOGGER.info(f"Finished - Populating Concertim View")

    # Map related View component objects
    def map_view_components(self):
        self.__LOGGER.info(f"Starting - Mapping related View components")
        self.map_racks_to_user()
        self.map_devices_to_rack()
        self.__LOGGER.info(f"Finished - Mapping related View components")

    # populate/add new users into self.view.users if they exist in concertim but not in self.view.users
    def fetch_concertim_users(self):
        try:
            self.__LOGGER.debug(f"Starting - Fetching Concertim Users")
            concertim_users = self.concertim_service.list_users()
            # For each non-admin user in concertim, check if they exist in self.view.users
            #   if user does exist - move on
            #   if user does not exist - create new component obj and add component obj to self.view.users[component.id]
            for user in concertim_users:
                if user['login'] == 'admin' or user['id'] in [id_tup[0] for id_tup in self.view.users]:
                    continue
                self.__LOGGER.debug(f"User '{user['id']}' not found in View - creating new ConcertimUser")
                new_user = ConcertimUser(concertim_id=user['id'], 
                                        openstack_id=user['cloud_user_id'], 
                                        concertim_name=user['login'], 
                                        openstack_name=f"CM_{user['login']}", 
                                        full_name=user['fullname'], 
                                        email=None,
                                        openstack_project_id=user['project_id'],
                                        description='')
                self.view.add_user(new_user)
                self.__LOGGER.debug(f"New ConcertimUser created in View : {new_user}")
            self.__LOGGER.debug(f"Finished - Fetching Concertim Users")
        except Exception as e:
            self.__LOGGER.error(f"Failed to fetch Users - {type(e).__name__} - {e} - {sys.exc_info()[2].tb_frame.f_code.co_filename} - {sys.exc_info()[2].tb_lineno}")
            raise e

    # populate/add new templates into self.view.templates if they exist in concertim but not in self.view.templates
    def fetch_concertim_templates(self):
        try:
            self.__LOGGER.debug(f"Starting - Fetching Concertim Templates")
            concertim_templates = self.concertim_service.list_templates()
            # For each template in concertim, check if they exist in self.view.templates
            #   if template does exist - move on
            #   if template does not exist - create new component obj and add component obj to self.view.templates[component.id]
            for template in concertim_templates:
                if template['id'] in [id_tup[0] for id_tup in self.view.templates]:
                    continue
                self.__LOGGER.debug(f"Template '{template['id']}' not found in View - creating new ConcertimTemplate")
                new_template = ConcertimTemplate(concertim_id=template['id'], 
                                        openstack_id=template['foreign_id'], 
                                        concertim_name=template['name'], 
                                        openstack_name=template['name'], 
                                        ram=template['ram'], 
                                        disk=template['disk'],
                                        vcpus=template['vcpus'],
                                        size=template['height'],
                                        description=template['description'])
                self.view.add_template(new_template)
                self.__LOGGER.debug(f"New ConcertimTemplate created in View : {new_template}")
            self.__LOGGER.debug(f"Finished - Fetching Concertim Templates")
        except Exception as e:
            self.__LOGGER.error(f"Failed to fetch Templates - {type(e).__name__} - {e} - {sys.exc_info()[2].tb_frame.f_code.co_filename} - {sys.exc_info()[2].tb_lineno}")
            raise e

    # populate/add new racks into self.view.racks if they exist in concertim but not in self.view.racks
    def fetch_concertim_racks(self):
        try:
            self.__LOGGER.debug(f"Starting - Fetching Concertim Racks")
            concertim_racks = self.concertim_service.list_racks()
            # For each rack in concertim, check if they exist in self.view.racks
            #   if rack does exist - move on
            #   if rack does not exist - create new component obj and add component obj to self.view.racks[component.id]
            for rack in concertim_racks:
                if rack['id'] in [id_tup[0] for id_tup in self.view.racks]:
                    continue
                self.__LOGGER.debug(f"Rack '{rack['id']}' not found in View - creating new ConcertimRack")
                opsk_stack_id = rack['metadata']['openstack_stack_id'] if 'openstack_stack_id' in rack['metadata'] else None
                new_rack = ConcertimRack(concertim_id=rack['id'], 
                                        openstack_id=opsk_stack_id, 
                                        concertim_name=rack['name'], 
                                        openstack_name=rack['name'], 
                                        user_id=rack['owner']['id'], 
                                        height=rack['u_height'], 
                                        description='',
                                        status=rack['status'])
                self.view.add_rack(new_rack)
                self.__LOGGER.debug(f"New ConcertimRack created in View : {new_rack}")                
            self.__LOGGER.debug(f"Finished - Fetching Concertim Racks")
        except Exception as e:
            self.__LOGGER.error(f"Failed to fetch Racks - {type(e).__name__} - {e} - {sys.exc_info()[2].tb_frame.f_code.co_filename} - {sys.exc_info()[2].tb_lineno}")
            raise e

    # populate/add new devices into self.view.devices if they exist in concertim but not in self.view.devices
    def fetch_concertim_devices(self):
        try:
            self.__LOGGER.debug(f"Starting - Fetching Concertim Devices")
            concertim_devices = self.concertim_service.list_devices()
            # For each device in concertim, check if they exist in self.view.devices
            #   if device does exist - move on
            #   if device does not exist - create new component obj and add component obj to self.view.devices[component.id]
            for device in concertim_devices:
                if device['id'] in [id_tup[0] for id_tup in self.view.devices]:
                    continue
                self.__LOGGER.debug(f"Device '{device['id']}' not found in View - creating new ConcertimDevice")
                device_info = self.concertim_service.show_device(ID=device['id'])
                opsk_instance_id = device_info['metadata']['openstack_instance_id'] if 'openstack_instance_id' in device_info['metadata'] else None
                opsk_instance_nm = device_info['metadata']['openstack_instance_name'] if 'openstack_instance_name' in device_info['metadata'] else None
                device_location = Location(device_info['location']['start_u'], device_info['location']['end_u'], device_info['location']['facing'])
                device_template = None
                for template_id_tup in self.view.templates:
                    if device_info['template']['id'] == template_id_tup[0]:
                        device_template = self.view.templates[template_id_tup]
                new_device = ConcertimDevice(concertim_id=device_info['id'], 
                                        openstack_id=opsk_instance_id, 
                                        concertim_name=device_info['name'], 
                                        openstack_name=opsk_instance_nm, 
                                        rack_id=device_info['location']['rack_id'], 
                                        template=device_template, 
                                        location=device_location, 
                                        description=device_info['description'], 
                                        status=device_info['status'])
                self.view.add_device(new_device)
                self.__LOGGER.debug(f"New ConcertimDevice created in View : {new_device}")  
            self.__LOGGER.debug(f"Finished - Fetching Concertim Devices")
        except Exception as e:
            self.__LOGGER.error(f"Failed to fetch Devices - {type(e).__name__} - {e} - {sys.exc_info()[2].tb_frame.f_code.co_filename} - {sys.exc_info()[2].tb_lineno}")
            raise e

    # Map ConcertimRack components in self.view.racks to ConcertimUser.racks for ConcertimUsers in View 
    def map_racks_to_user(self):
        try:
            self.__LOGGER.debug(f"Starting - Mapping Racks in View to their User's racks list")
            # For each ConcertimRack.user_id in self.view.racks check if matching ConcertimUser exists in self.view.users
            #   if matching ConcertimUser does not exist - skip this rack
            #   if matching ConcertimUser does exist - check if matching ConcertimRack is in ConcertimUser.racks
            #       if matching ConcertimRack does exist - go to next rack
            #       if matching ConcertimRack does not exist - add ConcertimRack to ConcertimUser.racks
            for rack_id_tup in self.view.racks:
                rack = self.view.racks[rack_id_tup]
                user_id_tup = None
                for temp_user_id_tup in self.view.users:
                    if temp_user_id_tup[0] == rack.user_id:
                        user_id_tup = temp_user_id_tup
                if not user_id_tup:
                    self.__LOGGER.warning(f"Could not map rack '{rack}' - No User matching '{rack.user_id}' found in View")
                    continue
                rack_exists = False
                for temp_rack_con_id in self.view.users[user_id_tup].racks:
                    if temp_rack_con_id == rack.id[0]:
                        self.__LOGGER.debug(f"Rack 'ID:{rack.id}' already exists for User 'ID:{user_id_tup}' - moving on")
                        rack_exists = True
                        break
                if not rack_exists:
                    self.__LOGGER.debug(f"Mapping rack 'ID:{rack_id_tup}' to user 'ID:{user_id_tup}'")
                    self.view.users[user_id_tup].add_rack(rack.id[0])
            self.__LOGGER.debug(f"Finished - Mapping Racks in View to their User's racks list")
        except Exception as e:
            self.__LOGGER.error(f"Failed to map Racks to Users - {type(e).__name__} - {e} - {sys.exc_info()[2].tb_frame.f_code.co_filename} - {sys.exc_info()[2].tb_lineno}")
            raise e

    # Map ConcertimDevice components in self.view.devices to ConcertimRack.devices for ConcertimRacks in View 
    def map_devices_to_rack(self):
        try:
            self.__LOGGER.debug(f"Starting - Mapping Devices in View to their Racks's device list")
            # For each ConcertimDevice.rack_id in self.view.devices check if matching ConcertimRack exists in self.view.racks
            #   if matching ConcertimRack does not exist - skip this device
            #   if matching ConcertimRack does exist - check if matching ConcertimDevice is in ConcertimRack.devices
            #       if matching ConcertimDevice does exist - go to next rack
            #       if matching ConcertimDevice does not exist - add ConcertimDevice to ConcertimRack.devices
            for device_id_tup in self.view.devices:
                device = self.view.devices[device_id_tup]
                rack_id_tup = None
                for temp_rack_id_tup in self.view.racks:
                    if temp_rack_id_tup[0] == device.rack_id:
                        rack_id_tup = temp_rack_id_tup
                if not rack_id_tup:
                    self.__LOGGER.warning(f"Could not map device '{device}' - No Rack matching '{device.rack_id}' found in View")
                    continue
                device_exists = False
                for temp_device_con_id in self.view.racks[rack_id_tup].devices:
                    if temp_device_con_id == device.id[0]:
                        self.__LOGGER.debug(f"Device 'ID:{device.id}' already exists for Rack 'ID:{rack_id_tup}' - moving on")
                        device_exists = True
                        break
                if not device_exists:
                    self.__LOGGER.debug(f"Mapping device 'ID:{device_id_tup}' to rack 'ID:{rack_id_tup}'")
                    self.view.racks[rack_id_tup].add_device(device.id[0],device.location)
            self.__LOGGER.debug(f"Finished - Mapping Devices in View to their Racks's device list")
        except Exception as e:
            self.__LOGGER.error(f"Failed to map Devices to Racks - {type(e).__name__} - {e} - {sys.exc_info()[2].tb_frame.f_code.co_filename} - {sys.exc_info()[2].tb_lineno}")
            raise e

    def save_view(self):
        self.__LOGGER.info(f"Saving View to '{UpdateHandler.VIEW_PICKLE_FILE}'")
        try:
            with open(UpdateHandler.VIEW_PICKLE_FILE, 'wb') as pkl_file:
                pickle.dump(self.view, pkl_file, protocol=pickle.HIGHEST_PROTOCOL)
            self.__LOGGER.info(f"Success - View saved to '{UpdateHandler.VIEW_PICKLE_FILE}'")
        except Exception as e:
            self.__LOGGER.error(f"Could not save View to '{UpdateHandler.VIEW_PICKLE_FILE}' - {type(e).__name__} - {e}")
            raise e

    def load_view(self):
        self.__LOGGER.info(f"Loading View from '{UpdateHandler.VIEW_PICKLE_FILE}'")
        try:
            with open(UpdateHandler.VIEW_PICKLE_FILE, 'rb') as pkl_file:
                self.view = pickle.load(pkl_file)
            self.__LOGGER.info(f"Success - View loaded from '{UpdateHandler.VIEW_PICKLE_FILE}' and set to self.view")
            return True
        except FileNotFoundError as e:
            self.__LOGGER.warning(f"No pickle file '{UpdateHandler.VIEW_PICKLE_FILE}' found - populating View directly")
            self.populate_view()
            self.save_view()
            return False
        except Exception as e:
            self.__LOGGER.error(f"Could not load View from '{UpdateHandler.VIEW_PICKLE_FILE}' - {type(e).__name__} - {e}")
            raise e

    def disconnect(self):
        self.__LOGGER.info(f"Destroying Updater data - {UpdateHandler.__DATA}")
        fails = []
        for f in UpdateHandler.__DATA:
            try:
                os.remove(f)
            except Exception as e:
                fails.append(f"Could not destroy '{f}' - {type(e).__name__} - {e}")
                continue
        if fails:
            self.__LOGGER.error(f"Failed - Updater Data Destroy - {fails}")
        self.view = None
        super().disconnect()

    

