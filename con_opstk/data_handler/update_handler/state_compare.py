# Local Imports
from con_opstk.utils.service_logger import create_logger
from con_opstk.data_handler.update_handler.update_base import UpdateHandler
from con_opstk.concertim.utils.view import ConcertimOpenstackView
from con_opstk.concertim.components.device import ConcertimDevice
from con_opstk.concertim.components.rack import ConcertimRack
from con_opstk.concertim.components.template import ConcertimTemplate
from con_opstk.concertim.components.user import ConcertimUser
from con_opstk.concertim.components.location import Location
from con_opstk.concertim.exceptions import ConcertimItemConflict, MissingRequiredArgs
# Py Packages
import sys


class BulkUpdateHandler(UpdateHandler):
    def __init__(self, config_obj, log_file, clients=None, billing_enabled=False):
        self.clients = clients if clients else UpdateHandler.DEFAULT_CLIENTS
        super().__init__(config_obj, log_file, self.clients, billing_enabled=billing_enabled)
        self.__LOGGER = create_logger(__name__, self._LOG_FILE, self._CONFIG['log_level'])
        self.default_rack_height=self._CONFIG['concertim']['default_rack_height']
        self.__resync_count = 0

    def full_update_sync(self):
        self.__LOGGER.info(f"Starting - Full Openstack Concertim Sync")
        self.__LOGGER.debug(f"Pulling View data directly from Concertim")
        self.view = ConcertimOpenstackView()
        self.populate_view()
        self.update_concertim()
        if self.view._needs_resync and self.__resync_count <= 2:
            self.__LOGGER.info(f"RESYNC SCHEDULED")
            self.view._needs_resync = False
            self.__resync_count += 1
            self.full_update_sync()
        elif self.view._needs_resync and self.__resync_count > 2:
            self.__LOGGER.warning(f"TOO MANY RESYNCS - {self.__resync_count} - PLEASE CHECK LOGS")
            raise Exception(f"TOO MANY RESYNCS - {self.__resync_count} - PLEASE CHECK LOGS")
        else:
            self.__resync_count = 0
            self.view._needs_resync = False
        self.save_view()
        self.__LOGGER.info(f"Finished - Full Openstack Concertim Sync\n")

    def _check_resync(self):
        self.__LOGGER.info(f"....Checking resync....")
        stash_curr_view = self.view
        self.load_view()
        if self.view._needs_resync and self.__resync_count <= 2:
            self.__LOGGER.info(f"RESYNC SCHEDULED")
            stash_curr_view = None
            self.__resync_count += 1
            self.view._needs_resync = False
            self.full_update_sync()
        elif self.view._needs_resync and self.__resync_count > 2:
            self.__LOGGER.warning(f"TOO MANY RESYNCS - {self.__resync_count} - PLEASE CHECK LOGS")
            raise Exception(f"TOO MANY RESYNCS - {self.__resync_count} - PLEASE CHECK LOGS")
        else:
            self.view = stash_curr_view
            stash_curr_view = None
            self.view._needs_resync = False
            self.__resync_count = 0

    def update_concertim(self):
        self.__LOGGER.info(f"Starting - Updating Concertim with new Openstack data")
        self.update_templates()
        self.update_racks()
        self.update_devices()
        self.__LOGGER.info(f"Finished - Updating Concertim with new Openstack data")

    def update_templates(self):
        try:
            self.__LOGGER.debug(f"Starting - Updating templates in Concertim based on Flavors in Openstack")
            openstack_flavors = self.openstack_service.get_flavors()
            self.__LOGGER.debug(f"Checking for new Flavors not in Concertim")
            in_openstack = []
            # Start new template creation
            for flavor_key in openstack_flavors:
                os_flavor_id = openstack_flavors[flavor_key]['id']
                in_openstack.append(os_flavor_id)
                os_flavor_name = openstack_flavors[flavor_key]['name']
                matching_templates = [con_temp for id_tup, con_temp in self.view.templates.items() if id_tup[1] == os_flavor_id]
                if matching_templates:
                    continue
                self.__LOGGER.debug(f"No Template found for Openstack Flavor[Name:{os_flavor_name},ID:{os_flavor_id}] - Creating in Concertim")
                self.create_template_in_concertim(openstack_flavors[flavor_key])
            # End new template creation

            self.__LOGGER.debug(f"--- Checking for stale Templates that are mapped to a non-existing Flavor in Openstack")
            stale_templates_ids = [id_tup for id_tup, con_temp in self.view.templates.items() if id_tup[1] not in in_openstack]
            # Start stale template deletion
            if stale_templates_ids:
                self.__LOGGER.warning(f"--- Stale templates found - IDs:{stale_templates_ids} - Deleting from Concertim")
                for stale_temp_id in stale_templates_ids:
                    try:
                        self.concertim_service.delete_template(stale_temp_id[0])
                        del self.view.templates[stale_temp_id]
                    except Exception as e:
                        self.__LOGGER.warning(f"Unhandled Exception when deleting template {stale_temp_id[0]} - Skipping - {type(e).__name__} - {e}")
                        self.view._needs_resync = True
                        continue
            else:
                self.__LOGGER.debug("--- No stale Templates found")
            # End stale template deletion
            self.__LOGGER.debug(f"Finished - Updating templates in Concertim based on Flavors in Openstack")
        except Exception as e:
            self.__LOGGER.error(f"Failed to update Templates - {type(e).__name__} - {e} - {sys.exc_info()[2].tb_frame.f_code.co_filename} - {sys.exc_info()[2].tb_lineno}")
            raise e

    def update_racks(self):
        try:
            self.__LOGGER.debug(f"Starting - Updating racks in Concertim based on stacks in Openstack")
            self.__LOGGER.debug(f"Checking for new Stacks not in Concertim")
            in_openstack = []
            # Start new rack creation
            for user_id_tup in self.view.users:
                self.__LOGGER.debug(f"Updating Racks for User[IDs:{user_id_tup},project_id{self.view.users[user_id_tup].openstack_project_id}]")
                openstack_stacks = self.openstack_service.list_stacks(project_id=self.view.users[user_id_tup].openstack_project_id)
                for heat_stack_obj in openstack_stacks:
                    in_openstack.append(heat_stack_obj.id)
                    matching_racks = [con_rack for id_tup, con_rack in self.view.racks.items() if id_tup[1] == heat_stack_obj.id]
                    if matching_racks:
                        self.__LOGGER.debug(f"Matching Rack found")
                        temp_rack = matching_racks[0]
                        if not temp_rack.name[1]:
                            self.view.racks[temp_rack.id].name = (temp_rack.name[0], heat_stack_obj.stack_name)
                        # Existing device found, check if it needs to update
                        if heat_stack_obj.stack_status not in UpdateHandler.CONCERTIM_STATE_MAP['RACK'][temp_rack.status]:
                            self.__LOGGER.debug(f"Matching Rack needs updated status - Updating")
                            self.update_rack_status(heat_stack_obj, temp_rack.id)
                        # Check rack output
                        if self.__empty_output_data(temp_rack):
                            self.__LOGGER.debug(f"Matching Rack has empty output values in ConcertimRack - Attempting to update")
                            self.update_rack_output(heat_stack_obj, temp_rack.id)
                        # Check rack network details
                        #if not temp_rack.network_details:
                        #    self.__LOGGER.debug(f"Matching Rack has empty network data in ConcertimRack - Attempting to update")
                        #    self.update_rack_network(heat_stack_obj, temp_rack.id)
                        # Check rack metadata
                        for m_key, m_val in self.view.racks[temp_rack.id].metadata.items():
                            if not m_val and m_key:
                                self.__LOGGER.debug(f"Matching Rack has empty metadata in ConcertimRack - Attempting to update")
                                self.update_rack_metadata(heat_stack_obj, temp_rack.id)
                                break
                        continue
                    self.__LOGGER.debug(f"No Rack found for Openstack Stack[ID:{heat_stack_obj.id},Name:{heat_stack_obj.stack_name}] - Creating in Concertim")
                    self.create_rack_in_concertim(heat_stack_obj, user_id_tup)
            # End new rack creation

            self.__LOGGER.debug(f"--- Checking for stale Racks that are mapped to a non-existing Stacks in Openstack")
            stale_racks_ids = [id_tup for id_tup, con_rack in self.view.racks.items() if id_tup[1] not in in_openstack]
            # Start stale rack deletion
            if stale_racks_ids:
                self.__LOGGER.warning(f"--- Stale racks found - IDs:{stale_racks_ids} - Deleting from Concertim")
                for stale_rack_id in stale_racks_ids:
                    try:
                        self.concertim_service.delete_rack(stale_rack_id[0], recurse=True)
                        stale_rack_user = [id_tup for id_tup, con_user in self.view.users.items() if id_tup[0] == self.view.racks[stale_rack_id].user_id]
                        if stale_rack_user:
                            self.view.users[stale_rack_user[0]].remove_rack(stale_rack_id[0])
                        del self.view.racks[stale_rack_id]
                    except Exception as e:
                        self.__LOGGER.warning(f"Unhandled Exception when deleting rack {stale_rack_id[0]} - Skipping - {type(e).__name__} - {e}")
                        self.view._needs_resync = True
                        continue
            else:
                self.__LOGGER.debug("--- No stale Racks found")
            # End stale rack deletion
            self.__LOGGER.debug(f"Finished - Updating racks in Concertim based on stacks in Openstack")
        except Exception as e:
            self.__LOGGER.error(f"Failed to update Racks - {type(e).__name__} - {e} - {sys.exc_info()[2].tb_frame.f_code.co_filename} - {sys.exc_info()[2].tb_lineno}")
            raise e

    def update_devices(self):
        try:
            self.__LOGGER.debug(f"Starting - Updating Devices in Concertim based on Instances in Openstack")
            self.__LOGGER.debug(f"Checking for new Instances not in Concertim that belong to a Rack in Concertim")
            in_openstack = []
            # Start new device creation for each rack in view
            for rack_id_tup in self.view.racks:
                self.__LOGGER.debug(f"Updating Devices for Rack[IDs:{rack_id_tup}]")
                nova_servers_list = self.openstack_service.get_stack_instances(rack_id_tup[1])
                # Instance device creation
                for nova_server in nova_servers_list:
                    in_openstack.append(nova_server.id)
                    matching_devices = [con_dev for id_tup, con_dev in self.view.devices.items() if id_tup[1] == nova_server.id]
                    if matching_devices:
                        temp_device = matching_devices[0]
                        if not temp_device.name[1]:
                            self.view.devices[temp_device.id].name = (temp_device.name[0], nova_server.name)
                        # Existing device found, check if it needs to update
                        if nova_server._info['OS-EXT-STS:vm_state'] not in UpdateHandler.CONCERTIM_STATE_MAP['DEVICE'][temp_device.status]:
                            self.__LOGGER.debug(f"Matching Device found - Needs updated status - Updating")
                            self.update_device_status(nova_server, temp_device.id)
                        if not (temp_device.ips and temp_device.ssh_key and temp_device.volume_details):
                            self.__LOGGER.debug(f"Matching Device found - Empty metadata in ConcertimDevice - Attempting to update")
                            self.update_device_metadata(nova_server, temp_device.id)
                        continue
                    self.__LOGGER.debug(f"No Device found for Openstack Server[ID:{nova_server.id},Name:{nova_server.name}] - Creating in Concertim")
                    self.create_device_in_concertim(nova_server, rack_id_tup)
            # End new device creation

            self.__LOGGER.debug(f"--- Checking for stale Devices that are mapped to a non-existing Instances in Openstack")
            stale_device_ids = [id_tup for id_tup, con_device in self.view.devices.items() if id_tup[1] not in in_openstack]
            # Start stale device deletion
            if stale_device_ids:
                self.__LOGGER.warning(f"--- Stale devices found - IDs:{stale_device_ids} - Deleting from Concertim")
                for stale_device_id in stale_device_ids:
                    try:
                        self.concertim_service.delete_device(stale_device_id[0])
                        stale_device_rack = [id_tup for id_tup, con_rack in self.view.racks.items() if id_tup[0] == self.view.devices[stale_device_id].rack_id]
                        if stale_device_rack:
                            self.view.racks[stale_device_rack[0]].remove_device(stale_device_id[0], self.view.devices[stale_device_id].location)
                        del self.view.devices[stale_device_id]
                    except Exception as e:
                        self.__LOGGER.warning(f"Unhandled Exception when deleting device {stale_device_id[0]} - Skipping - {type(e).__name__} - {e}")
                        self.view._needs_resync = True
                        continue
            else:
                self.__LOGGER.debug("--- No stale Devices found")
            # End stale device deletion
            self.__LOGGER.debug(f"Finished - Updating Devices in Concertim based on Instances in Openstack")
        except Exception as e:
            self.__LOGGER.error(f"Failed to update Devices - {type(e).__name__} - {e} - {sys.exc_info()[2].tb_frame.f_code.co_filename} - {sys.exc_info()[2].tb_lineno}")
            raise e

    def create_template_in_concertim(self, os_flavor):
        try:
            new_template = ConcertimTemplate(concertim_id=None, openstack_id=os_flavor['id'], 
                                                concertim_name=os_flavor['name'], openstack_name=os_flavor['name'], 
                                                ram=os_flavor['ram'], disk=os_flavor['disk'], 
                                                vcpus=os_flavor['vcpus'], size=None, description='Flavor from Openstack')
            if new_template.vcpus <= 1:
                new_template.size = 1
            elif new_template.vcpus <= 2:
                new_template.size = 2
            elif new_template.vcpus <= 4:
                new_template.size = 3
            else:
                new_template.size = 4
            concertim_response_template = None
            try:
                concertim_response_template = self.concertim_service.create_template({'name': new_template.name[1], 
                                                                                'description': new_template.description, 
                                                                                'height': new_template.size, 
                                                                                'ram' : new_template.ram, 
                                                                                'disk' : new_template.disk, 
                                                                                'vcpus' : new_template.vcpus, 
                                                                                'foreign_id' : new_template.id[1]})
                new_template.id = (concertim_response_template['id'], new_template.id[1])
                self.__LOGGER.debug(f"Successfully created new Template: {new_template}")
                self.view.add_template(new_template)
                return True
            except ConcertimItemConflict as e:
                self.__LOGGER.warning(f"The template {new_template.name[1]} already exists - Skipping - {type(e).__name__} - {e}")
                self.view._needs_resync = True
                return False
            except Exception as e:
                self.__LOGGER.error(f"Unhandled Exception when creating template {new_template.name[1]} - Skipping - {type(e).__name__} - {e}")
                self.view._needs_resync = True
                return False
        except Exception as e:
            self.__LOGGER.error(f"Failed to create Template - {type(e).__name__} - {e} - {sys.exc_info()[2].tb_frame.f_code.co_filename} - {sys.exc_info()[2].tb_lineno}")
            raise e

    def create_rack_in_concertim(self, os_stack, user_id_tup):
        try:
            con_state_list = [c_state for c_state, os_state_list in UpdateHandler.CONCERTIM_STATE_MAP['RACK'].items() if os_stack.stack_status in os_state_list]
            if con_state_list:
                con_state = con_state_list[0]
            else:
                con_state = 'FAILED'
            # BASE RACK CREATION
            new_rack = ConcertimRack(concertim_id=None, openstack_id=os_stack.id, 
                                    concertim_name=os_stack.stack_name.replace('.','-').replace('_','-'), openstack_name=os_stack.stack_name, 
                                    user_id=user_id_tup[0], height=self.default_rack_height, 
                                    description='Heat Stack in Openstack', status=con_state)
            new_rack.output = self.openstack_service.get_stack_output(os_stack.id)
            new_rack._creation_output = self._get_output_as_string(new_rack.output)
            new_rack.network_details = {} ## TODO: ADD GETTING NETWORK DETAILS FOR STACK
            # ADD EXISTING METADATA
            if hasattr(os_stack, 'stack_status_reason') and os_stack.stack_status_reason:
                new_rack.add_metadata(openstack_stack_status_reason=os_stack.stack_status_reason)
            if hasattr(os_stack, 'stack_owner') and os_stack.stack_owner:
                new_rack.add_metadata(openstack_stack_owner=os_stack.stack_owner)
            if hasattr(os_stack, 'stack_user_project_id') and os_stack.stack_user_project_id:
                new_rack.add_metadata(openstack_stack_owner_id=os_stack.stack_user_project_id)
            concertim_response_rack = None
            # CREATE BILLNIG ORDER FOR STACK
            try:
                billing_acct = self.view.users[user_id_tup].billing_acct_id
                order_id = self.billing_service.create_order(billing_acct)['headers']['Location'].split('/')[-1]
                new_rack.order_id = order_id
            except Exception as e:
                self.__LOGGER.error(f"Failed to create Rack - {type(e).__name__} - {e} - {sys.exc_info()[2].tb_frame.f_code.co_filename} - {sys.exc_info()[2].tb_lineno}")
                raise e
            try:
                concertim_response_rack = self.concertim_service.create_rack({'name': new_rack.name[0],
                                                                'user_id' : new_rack.user_id,
                                                                'u_height': new_rack.height,
                                                                'openstack_stack_id' : new_rack.id[1],
                                                                'status' : new_rack.status,
                                                                'order_id': new_rack.order_id
                                                                'network_details' : new_rack.network_details,
                                                                'creation_output' : new_rack._creation_output,
                                                                'openstack_stack_output': new_rack.output,
                                                                'openstack_stack_status_reason':os_stack.stack_status_reason,
                                                                'openstack_stack_owner':os_stack.stack_owner,
                                                                'openstack_stack_owner_id' : os_stack.stack_user_project_id})
                new_rack.id = (concertim_response_rack['id'],new_rack.id[1])
                self.__LOGGER.debug(f"Successfully created new Rack: {new_rack}")
                self.view.add_rack(new_rack)
                self.view.users[user_id_tup].add_rack(new_rack.id[0])
                return True
            except ConcertimItemConflict as e:
                self.__LOGGER.warning(f"The rack {new_rack.name[0]} already exists - Skipping - {type(e).__name__} - {e}")
                self.view._needs_resync = True
                return False
            except Exception as e:
                self.__LOGGER.error(f"Unhandled Exception when creating rack {new_rack.name[0]} - Skipping - {type(e).__name__} - {e}")
                self.view._needs_resync = True
                return False
        except Exception as e:
            self.__LOGGER.error(f"Failed to create Rack - {type(e).__name__} - {e} - {sys.exc_info()[2].tb_frame.f_code.co_filename} - {sys.exc_info()[2].tb_lineno}")
            raise e

    def create_device_in_concertim(self, os_instance, rack_id_tup):
        try:
            con_state_list = [c_state for c_state, os_state_list in UpdateHandler.CONCERTIM_STATE_MAP['DEVICE'].items() if os_instance._info['OS-EXT-STS:vm_state'] in os_state_list]
            if con_state_list:
                con_state = con_state_list[0]
            else:
                con_state = 'FAILED'
            matching_template_id_tup = [id_tup for id_tup, con_temp in self.view.templates.items() if id_tup[1] == os_instance.flavor['id']]
            if not matching_template_id_tup:
                self.__LOGGER.error(f"Cannot create device for Instance[ID:{os_instance.id},Name:{os_instance.name}] - No ConcertimTemplate matching Flavor[ID:{os_instance.flavor['id']}] found")
                return
            # BASE ConcertimDevice CREATION
            template_for_inst = self.view.templates[matching_template_id_tup[0]]
            loc_for_inst = self.__find_empty_slot(rack_id_tup, template_for_inst.size)
            new_device = ConcertimDevice(concertim_id=None, openstack_id=os_instance.id, 
                                        concertim_name=os_instance.name.replace('.','-').replace('_','-'), openstack_name=os_instance.name, 
                                        rack_id=rack_id_tup[0], template=template_for_inst, 
                                        location=loc_for_inst, description='Nova Server in Openstack', status=con_state)
            # ADD EXISTING METADATA
            #if hasattr(os_instance, 'accessIPv4') and os_instance.accessIPv4:
            #    new_device.ips.append(os_instance.accessIPv4)
            #if hasattr(os_instance, 'accessIPv6') and os_instance.accessIPv6:
            #    new_device.ips.append(os_instance.accessIPv6)
            if hasattr(os_instance, 'addresses') and os_instance.addresses:
                new_device.ips = os_instance.addresses
                ips_as_dict = self._get_ips_as_dict(os_instance.addresses)
                if 'public_ips' in ips_as_dict:
                    new_device.public_ips = ips_as_dict['public_ips']
                if 'private_ips' in ips_as_dict:
                    new_device.private_ips = ips_as_dict['private_ips']
            if hasattr(os_instance, 'key_name') and os_instance.key_name:
                new_device.ssh_key = os_instance.key_name
            if hasattr(os_instance, 'os-extended-volumes:volumes_attached') and os_instance._info['os-extended-volumes:volumes_attached']:
                new_device.volume_details = os_instance._info['os-extended-volumes:volumes_attached']
            new_device.login_user = '' ## TODO: ADD GETTING LOGIN USER
            # CREATE DEVICE IN CONCERTIM
            concertim_response_device = None
            try:
                concertim_response_device = self.concertim_service.create_device({'template_id': new_device.template.id[0], 
                                                                    'description': new_device.description, 
                                                                    'name': new_device.name[0], 
                                                                    'facing': new_device.location.facing, 
                                                                    'rack_id': new_device.rack_id, 
                                                                    'start_u': new_device.location.start_u, 
                                                                    'openstack_instance_id' : new_device.id[1],
                                                                    'status' : con_state,
                                                                    'login_user' : new_device.login_user, 
                                                                    'private_ips' : new_device.private_ips, 
                                                                    'public_ips' : new_device.public_ips, 
                                                                    'openstack_ips' : new_device.ips,
                                                                    'ssh_key': new_device.ssh_key,
                                                                    'volume_details': new_device.volume_details})
                new_device.id = (concertim_response_device['id'], new_device.id[1])
                self.__LOGGER.debug(f"Successfully created new Device: {new_device}")
                self.view.add_device(new_device)
                self.view.racks[rack_id_tup].add_device(new_device.id[0], new_device.location)
            except ConcertimItemConflict as e:
                self.__LOGGER.warning(f"The device {new_device.name[0]} already exists - Skipping - {type(e).__name__} - {e}")
                self.view._needs_resync = True
                return False
            except Exception as e:
                self.__LOGGER.error(f"Unhandled Exception when creating device {new_device.name[0]} - Skipping - {type(e).__name__} - {e}")
                self.view._needs_resync = True
                return False
        except Exception as e:
            self.__LOGGER.error(f"Failed to create Device - {type(e).__name__} - {e} - {sys.exc_info()[2].tb_frame.f_code.co_filename} - {sys.exc_info()[2].tb_lineno}")
            raise e

    def update_rack_status(self, os_stack, rack_id_tup):
        try:
            con_state_list = [c_state for c_state, os_state_list in UpdateHandler.CONCERTIM_STATE_MAP['RACK'].items() if os_stack.stack_status in os_state_list]
            if con_state_list:
                con_state = con_state_list[0]
            else:
                con_state = 'FAILED'
            try:
                self.concertim_service.update_rack(rack_id_tup[0], {'name':self.view.racks[rack_id_tup].name[0],'status':con_state})
                self.view.racks[rack_id_tup].status = con_state
                self.__LOGGER.debug(f"Status updated to {con_state}")
            except Exception as e:
                self.__LOGGER.error(f"Unhandled Exception when updating status for Rack {rack_id_tup[0]} - Skipping - {type(e).__name__} - {e}")
                self.view._needs_resync = True
                return 
        except Exception as e:
            self.__LOGGER.error(f"Failed to update Rack status - {type(e).__name__} - {e} - {sys.exc_info()[2].tb_frame.f_code.co_filename} - {sys.exc_info()[2].tb_lineno}")
            raise e

    def update_rack_output(self, os_stack, rack_id_tup):
        try:
            # Store other rack metadata
            curr_md = self.view.racks[rack_id_tup].metadata
            vars_dict_to_send = {'name':self.view.racks[rack_id_tup].name[0], 
                                'openstack_stack_id': os_stack.id, 
                                **curr_md}
            new_output = self.openstack_service.get_stack_output(os_stack.id)
            new_creation_output = self._get_output_as_string(new_output)
            vars_dict_to_send['openstack_stack_output'] = new_output
            vars_dict_to_send['creation_output'] = new_creation_output
            try:
                self.concertim_service.update_rack(rack_id_tup[0], vars_dict_to_send)
                self.view.racks[rack_id_tup].output = new_output
                self.view.racks[rack_id_tup]._creation_output = new_creation_output
                self.__LOGGER.debug(f"Output Updated")
            except Exception as e:
                self.__LOGGER.error(f"Unhandled Exception when output metadata for Rack {rack_id_tup[0]} - Skipping - {type(e).__name__} - {e}")
                self.view._needs_resync = True
                return 
        except Exception as e:
            self.__LOGGER.error(f"Failed to update Rack output - {type(e).__name__} - {e} - {sys.exc_info()[2].tb_frame.f_code.co_filename} - {sys.exc_info()[2].tb_lineno}")
            raise e

    def update_rack_metadata(self, os_stack, rack_id_tup):
        try:
            # Clear currnet metadata for rack
            curr_output = self.view.racks[rack_id_tup].output
            self.view.racks[rack_id_tup].metadata = {}
            ###
            os_stk_owner = ''
            os_stk_owner_id = ''
            os_stk_status_reas = ''
            if hasattr(os_stack, 'stack_status_reason') and os_stack.stack_status_reason:
                os_stk_status_reas = os_stack.stack_status_reason
            if hasattr(os_stack, 'stack_owner') and os_stack.stack_owner:
                os_stk_owner = os_stack.stack_owner
            if hasattr(os_stack, 'stack_user_project_id') and os_stack.stack_user_project_id:
                os_stk_owner_id = os_stack.stack_user_project_id
            if not (os_stk_owner or os_stk_owner_id or os_stk_status_reas):
                try:
                    self.concertim_service.update_rack(rack_id_tup[0], {'name':self.view.racks[rack_id_tup].name[0],
                                                                        'openstack_stack_output': curr_output,
                                                                        'openstack_stack_status_reason': os_stk_status_reas,
                                                                        'openstack_stack_owner': os_stk_owner,
                                                                        'openstack_stack_owner_id': os_stk_owner_id,
                                                                        'openstack_stack_id': os_stack.id})
                    self.view.racks[rack_id_tup].add_metadata(openstack_stack_status_reason=os_stk_status_reas,openstack_stack_owner=os_stk_owner,openstack_stack_owner_id=os_stk_owner_id)
                    self.__LOGGER.debug(f"Metadata Updated")
                except Exception as e:
                    self.__LOGGER.error(f"Unhandled Exception when updating metadata for Rack {rack_id_tup[0]} - Skipping - {type(e).__name__} - {e}")
                    self.view._needs_resync = True
                    return 
            else:
                self.__LOGGER.debug(f"Rack Metadata fields are empty - Skipping update")
                return
        except Exception as e:
            self.__LOGGER.error(f"Failed to update Rack metadata - {type(e).__name__} - {e} - {sys.exc_info()[2].tb_frame.f_code.co_filename} - {sys.exc_info()[2].tb_lineno}")
            raise e

    def update_device_status(self, os_instance, device_id_tup):
        try:
            con_state_list = [c_state for c_state, os_state_list in UpdateHandler.CONCERTIM_STATE_MAP['DEVICE'].items() if os_instance._info['OS-EXT-STS:vm_state'] in os_state_list]
            if con_state_list:
                con_state = con_state_list[0]
            else:
                con_state = 'FAILED'
            try:
                self.concertim_service.update_device(device_id_tup[0], {'name':self.view.devices[device_id_tup].name[0],'status':con_state})
                self.view.devices[device_id_tup].status = con_state
                self.__LOGGER.debug(f"Status updated to {con_state}")
            except Exception as e:
                self.__LOGGER.error(f"Unhandled Exception when updating status for Device {device_id_tup[0]} - Skipping - {type(e).__name__} - {e}")
                self.view._needs_resync = True
                return 
        except Exception as e:
            self.__LOGGER.error(f"Failed to update Device status - {type(e).__name__} - {e} - {sys.exc_info()[2].tb_frame.f_code.co_filename} - {sys.exc_info()[2].tb_lineno}")
            raise e

    def update_device_metadata(self, os_instance, device_id_tup):
        try:
            os_ips = []
            os_private_ips = ''
            os_public_ips = ''
            os_ssh_key = ''
            os_vols_att = {}
            if hasattr(os_instance, 'addresses') and os_instance.addresses:
                os_ips = (os_instance.addresses)
                ips_as_dict = self._get_ips_as_dict(os_instance.addresses)
                if 'public_ips' in ips_as_dict:
                    os_public_ips = ips_as_dict['public_ips']
                if 'private_ips' in ips_as_dict:
                    os_private_ips = ips_as_dict['private_ips']
            if hasattr(os_instance, 'key_name') and os_instance.key_name:
                os_ssh_key = os_instance.key_name
            if hasattr(os_instance, 'os-extended-volumes:volumes_attached') and os_instance._info['os-extended-volumes:volumes_attached']:
                os_vols_att = os_instance._info['os-extended-volumes:volumes_attached']
            os_login_user = '' ## TODO: ADD GETTING LOGIN USER
            if not (os_ips or os_ssh_key or os_vols_att):
                try:
                    self.concertim_service.update_device(device_id_tup[0], {'name':self.view.devices[device_id_tup].name[0], 
                                                                            'private_ips' : os_private_ips, 
                                                                            'public_ips' : os_public_ips, 
                                                                            'openstack_ips' : os_ips,
                                                                            'ssh_key': os_ssh_key,
                                                                            'login_user': os_login_user,
                                                                            'volume_details': os_vols_att})
                    self.view.devices[device_id_tup].ips = os_ips
                    self.view.devices[device_id_tup].private_ips = os_private_ips
                    self.view.devices[device_id_tup].public_ips = os_public_ips
                    self.view.devices[device_id_tup].ssh_key = os_ssh_key
                    self.view.devices[device_id_tup].login_user = os_login_user
                    self.view.devices[device_id_tup].volume_details = os_vols_att
                    self.__LOGGER.debug(f"Metadata Updated")
                except Exception as e:
                    self.__LOGGER.error(f"Unhandled Exception when updating metadata for Device {device_id_tup[0]} - Skipping - {type(e).__name__} - {e}")
                    self.view._needs_resync = True
                    return 
            else:
                self.__LOGGER.debug(f"Instance Metadata fields are empty - Skipping update")
                return
        except Exception as e:
            self.__LOGGER.error(f"Failed to update Device metadata - {type(e).__name__} - {e} - {sys.exc_info()[2].tb_frame.f_code.co_filename} - {sys.exc_info()[2].tb_lineno}")
            raise e

    def __empty_output_data(self, con_rack):
        for output_tup in con_rack.output:
            if output_tup[1]:
                continue
            return True
        return False

    def __find_empty_slot(self, rack_id_tup, size):
        try:
            occupied_spots = self.view.racks[rack_id_tup]._occupied
            height = self.view.racks[rack_id_tup].height
            self.__LOGGER.debug(f"Finding spot in Rack[ID:{rack_id_tup[0]}] - Occupied Slots: {occupied_spots}")
            spot_found = False
            start_location = -1
            for rack_row in range(height, 0, -1):
                if (rack_row + size - 1) <= height and rack_row >= 1:
                    fits = True
                    for device_section in range(0, size):
                        row = (rack_row + device_section)
                        if row in occupied_spots:
                            fits = False
                    if fits:
                        start_location = rack_row
                        spot_found = True
                        break
            if spot_found:
                end_location = start_location + size - 1
                self.__LOGGER.debug(f"Empty space found")
                return Location(start_u=start_location, end_u=end_location, facing='f')
            self.__LOGGER.debug(f"No empty rack space found - Resizing rack and trying again.")
            self.concertim_service.update_rack(rack_id_tup[0], {'u_height': int(height + size)})
            return self.__find_spot_in_rack(rack_id_tup, size)
        except Exception as e:
            self.__LOGGER.error(f"Failed to find empty spot in Rack - {type(e).__name__} - {e} - {sys.exc_info()[2].tb_frame.f_code.co_filename} - {sys.exc_info()[2].tb_lineno}")
            raise e


