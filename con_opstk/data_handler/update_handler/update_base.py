# Local Imports
from con_opstk.utils.service_logger import create_logger
from con_opstk.data_handler.base import BaseHandler
from con_opstk.concertim.utils.view import ConcertimOpenstackView
from con_opstk.concertim.components.device import ConcertimDevice
from con_opstk.concertim.components.rack import ConcertimRack
from con_opstk.concertim.components.template import ConcertimTemplate
from con_opstk.concertim.components.user import ConcertimUser
from con_opstk.concertim.components.location import Location
from con_opstk.data_handler.exceptions import InvalidSearchAttempt
import con_opstk.app_definitions as app_paths
# Py Packages
import sys
import pickle
import os

class UpdateHandler(BaseHandler):
    DEFAULT_CLIENTS = ['keystone','nova','heat']
    VIEW_PICKLE_FILE = app_paths.DATA_DIR + 'view.pickle'
    __DATA = [VIEW_PICKLE_FILE]
    CONCERTIM_STATE_MAP = {
        'DEVICE':{
            'ACTIVE': ['active', 'running'],
            'STOPPED': ['stopped'],
            'SUSPENDED': ['suspended'],
            'IN_PROGRESS': ['building', 'deleting', 'scheduling', 'networking', 'block_device_mapping', 'spawning', 'deleted', 'powering-on', 'powering-off', 'suspending'],
            'FAILED': []
        },
        'RACK':{
            'ACTIVE': ['CREATE_COMPLETE','RESUME_COMPLETE'],
            'STOPPED': ['SUSPEND_COMPLETE'],
            'IN_PROGRESS': ['CREATE_IN_PROGRESS','SUSPEND_IN_PROGRESS','DELETE_IN_PROGRESS', 'DELETE_COMPLETE'],
            'FAILED': ['CREATE_FAILED','DELETE_FAILED']
        }
    }
    def __init__(self, config_obj, log_file, clients=None, billing_enabled=False):
        self.clients = clients if clients else UpdateHandler.DEFAULT_CLIENTS
        super().__init__(config_obj, log_file, self.clients, billing_enabled=billing_enabled)
        self.__LOGGER = create_logger(__name__, self._LOG_FILE, self._CONFIG['log_level'])
        self.view = ConcertimOpenstackView()
        self._default_rack_height = int(self._CONFIG['concertim']['default_rack_height']) if 'default_rack_height' in self._CONFIG['concertim'] else 42

    # Controller method for populating self.view with data from concertim app
    def populate_view(self):
        self.__LOGGER.info(f"Starting - Populating Concertim View")
        self.fetch_concertim_users()
        self.fetch_concertim_templates()
        self.fetch_concertim_racks()
        self.fetch_concertim_devices()
        self.map_view_components()
        self.__LOGGER.info(f"Finished - Populating Concertim View\n")

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
                if not user['cloud_user_id']:
                    self.__LOGGER.debug(f"User '{user['id']}' has no Cloud ID - Skipping")
                    continue
                self.__LOGGER.debug(f"User '{user['id']}' not found in View - creating new ConcertimUser")
                new_user = ConcertimUser(concertim_id=user['id'], 
                                        openstack_id=user['cloud_user_id'], 
                                        concertim_name=user['login'], 
                                        openstack_name=f"CM_{user['login']}", 
                                        full_name=user['fullname'], 
                                        email=user['email'],
                                        openstack_project_id=user['project_id'],
                                        description='',
                                        billing_acct_id=user['billing_acct_id'])
                new_user.cost = float(user['cost'] if 'cost' in user and user['cost'] else 0.0)
                new_user.billing_period_start = user['billing_period_start'] if 'billing_period_start' in user and user['billing_period_start'] else ''
                new_user.billing_period_end = user['billing_period_end'] if 'billing_period_end' in user and user['billing_period_end'] else ''
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
                opsk_stack_id = rack['metadata']['openstack_stack_id'] if 'openstack_stack_id' in rack['metadata'] else ''
                new_rack = ConcertimRack(concertim_id=rack['id'], 
                                        openstack_id=opsk_stack_id, 
                                        concertim_name=rack['name'], 
                                        openstack_name=None, 
                                        user_id=rack['owner']['id'], 
                                        height=rack['u_height'], 
                                        description='Stack in Openstack',
                                        status=rack['status'],
                                        order_id=rack['order_id'])
                for k,v in rack['metadata'].items():
                    if k != 'openstack_stack_id':
                        new_rack.metadata[k] = v
                if 'network_details' in rack and rack['network_details']:
                    new_rack.network_details = rack['network_details']
                if 'creation_output' in rack and rack['creation_output']:
                    new_rack._creation_output = rack['creation_output']
                new_rack.cost = float(rack['cost'] if 'cost' in rack and rack['cost'] else 0.0)
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
                opsk_instance_id = device['metadata']['openstack_instance_id'] if 'openstack_instance_id' in device['metadata'] else ''
                device_location = Location(device['location']['start_u'], device['location']['end_u'], device['location']['facing'])
                device_template = None
                for template_id_tup in self.view.templates:
                    if device['template_id'] == template_id_tup[0]:
                        device_template = self.view.templates[template_id_tup]
                new_device = ConcertimDevice(concertim_id=device['id'], 
                                        openstack_id=opsk_instance_id, 
                                        concertim_name=device['name'], 
                                        openstack_name=None, 
                                        rack_id=device['location']['rack_id'], 
                                        template=device_template, 
                                        location=device_location, 
                                        description=device['description'], 
                                        status=device['status'])
                new_device.ips = device['metadata']['net_interfaces'] if 'net_interfaces' in device['metadata'] and device['metadata']['net_interfaces'] else []
                new_device.ssh_key = device['ssh_key'] if 'ssh_key' in device and device['ssh_key'] else ''
                new_device.volume_details = device['volume_details'] if 'volume_details' in device and device['volume_details'] else {}
                new_device.public_ips = device['public_ips'] if 'public_ips' in device and device['public_ips'] else ''
                new_device.private_ips = device['private_ips'] if 'private_ips' in device and device['private_ips'] else ''
                new_device.login_user = device['login_user'] if 'login_user' in device and device['login_user'] else ''
                new_device.cost = float(device['cost'] if 'cost' in device and device['cost'] else 0.0)
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

    # Method to search the view for an object that has a matching id
    # Returns a dict of the matching {id_tup:component} in the view, returns empty dict if none found
    # The matching ID tuple(s) are the keys in the view object
    def search_view(self, list_type, service, id_to_find):
        '''
        'list_type'     - the view list of objects to search in 
                        ("racks", "devices", "users", "templates")
        'service'       - the service that the ID is coming from 
                        ("openstack","concertim")
        'id_to_find'    - id of the object in the service
        '''
        __valid_list_types = ['racks','devices','users','templates']
        __valid_services = ['openstack', 'concertim']
        if list_type.lower() not in __valid_list_types:
            raise InvalidSearchAttempt(f"Invalid list type - '{list_type.lower()}' - valid options {__valid_list_types}")
        if service.lower() not in __valid_services:
            raise InvalidSearchAttempt(f"Invalid service name - '{service.lower()}' - valid options {__valid_services}")
        tup_index = 0 if service.lower() == 'concertim' else 1 
        list_to_search = getattr(self.view, list_type)
        return {id_tup:comp for (id_tup,comp) in list_to_search.items() if id_tup[tup_index] == id_to_find}
        

    def save_view(self):
        self.__LOGGER.info(f"Saving View to '{UpdateHandler.VIEW_PICKLE_FILE}'")
        try:
            if not os.path.exists(UpdateHandler.VIEW_PICKLE_FILE):
                os.mknod(UpdateHandler.VIEW_PICKLE_FILE, mode = 0o660)
            with open(UpdateHandler.VIEW_PICKLE_FILE, 'wb') as pkl_file:
                pickle.dump(self.view, pkl_file, protocol=pickle.HIGHEST_PROTOCOL)
            self.__LOGGER.info(f"Success - View saved to '{UpdateHandler.VIEW_PICKLE_FILE}'")
        except FileNotFoundError as e:
            self.__LOGGER.error(f"No pickle file '{UpdateHandler.VIEW_PICKLE_FILE}' found - Please check path exists - {type(e).__name__} - {e} - {sys.exc_info()[2].tb_frame.f_code.co_filename} - {sys.exc_info()[2].tb_lineno}")
            raise e
        except Exception as e:
            self.__LOGGER.error(f"Could not save View to '{UpdateHandler.VIEW_PICKLE_FILE}' - {type(e).__name__} - {e} - {type(e).__name__} - {e} - {sys.exc_info()[2].tb_frame.f_code.co_filename} - {sys.exc_info()[2].tb_lineno}")
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
            self.__LOGGER.error(f"Could not load View from '{UpdateHandler.VIEW_PICKLE_FILE}' - {type(e).__name__} - {e} - {type(e).__name__} - {e} - {sys.exc_info()[2].tb_frame.f_code.co_filename} - {sys.exc_info()[2].tb_lineno}")
            raise e

    def _get_ips_as_dict(self, addresses):
        ips_dict = {'public_ips': '', 'private_ips': ''}
        for net in addresses:
            for ip_interface in addresses[net]:
                if ip_interface["OS-EXT-IPS:type"] == 'fixed':
                    ips_dict['private_ips'] += f", {net}:{ip_interface['addr']}" if ips_dict['private_ips'] else f"{net}:{ip_interface['addr']}"
                if ip_interface["OS-EXT-IPS:type"] == 'floating':
                    ips_dict['public_ips'] += f", {net}:{ip_interface['addr']}" if ips_dict['public_ips'] else f"{net}:{ip_interface['addr']}"
        return ips_dict
    
    def _get_output_as_string(self, output_list):
        output_str = ''
        for output_tup in output_list:
            output_str += f", {output_tup[0]}={output_tup[1]}" if output_str else f"{output_tup[0]}={output_tup[1]}"
        return output_str

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
            self.__LOGGER.warning(f"Failed - Updater Data Destroy - {fails}")
        self.view = None
        super().disconnect()

    

