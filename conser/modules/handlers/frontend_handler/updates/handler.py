# Local Imports
from conser.utils.service_logger import create_logger
from conser.factory.abs_classes.handlers import Handler
import conser.exceptions as EXCP
import conser.utils.common as UTILS

# Py Packages
import time
import json

class UpdatesHandler(Handler):
    ############
    # DEFAULTS #
    ############
    UPDATES_INTERVAL = 10
    ########
    # INIT #
    ########
    def __init__(self, clients_dict, log_file, log_level):
        self._LOG_LEVEL = log_level
        self._LOG_FILE = log_file
        self.__LOGGER = create_logger(__name__, self._LOG_FILE, self._LOG_LEVEL)
        self.clients = clients_dict
        self.view = None

    #############################
    # UPDATES HANDLER FUNCTIONS #
    #############################
    def templates_changes(self):
        self.__LOGGER.debug("Starting -- Sending templates changes")
        # EXIT CASES
        if not self.view.templates:
            self.__LOGGER.debug("Finished -- No Templates found in View")
            return

        # OBJECT LOGIC
        for template_id_tup, template in self.view.templates.items():
            self.__LOGGER.debug(f"Checking template {template_id_tup}")
            #-- check if the template has a concertim ID, if so update, else create
            if template_id_tup[0] and template_id_tup[1]:
                self.__LOGGER.debug(f"Template exists in Concertim - updating template {template_id_tup}")
                self.update_existing_template(template)
            elif not template_id_tup[0] and template_id_tup[1]:
                self.__LOGGER.debug(f"Template not found in Concertim - creating template {template_id_tup}")
                self.create_new_template(template)
            elif template.tag is None:
                self.__LOGGER.warning(f"Unrecognized template found in view {template}")
        self.__LOGGER.debug("Finished -- Sending templates changes")

    def racks_changes(self):
        self.__LOGGER.debug("Starting -- Sending racks changes")
        # EXIT CASES
        if not self.view.racks:
            self.__LOGGER.debug("Finished -- No Racks found in View")
            return

        # OBJECT LOGIC
        new_racks = False
        for rack_id_tup, rack in self.view.racks.items():
            self.__LOGGER.debug(f"Checking rack {rack_id_tup}")
            #-- check if rack needs to be deleted from concertim
            if rack._delete_marker and rack_id_tup[0]:
                self.__LOGGER.debug(f"Rack marked for delete - deleting rack {rack_id_tup}")
                self.delete_stale_rack(rack)
            #-- check if the rack has a concertim ID, if so update, else create
            elif rack_id_tup[0] and rack_id_tup[1]:
                self.__LOGGER.debug(f"Rack exists in Concertim - updating rack {rack_id_tup}")
                self.update_existing_rack(rack)
            elif not rack_id_tup[0] and rack_id_tup[1]:
                self.__LOGGER.debug(f"Rack not found in Concertim - creating rack {rack_id_tup}")
                self.create_new_rack(rack)
                new_racks = True
            else:
                self.__LOGGER.warning(f"Unrecognized rack found in view {rack}")
        if new_racks:
            UTILS.create_resync_flag()
        self.__LOGGER.debug("Finished -- Sending racks changes")

    def devices_changes(self):
        self.__LOGGER.debug("Starting -- Sending devices changes")
        # EXIT CASES
        if not self.view.devices:
            self.__LOGGER.debug("Finished -- No Devices found in View")
            return

        # OBJECT LOGIC
        for device_id_tup, device in self.view.devices.items():
            self.__LOGGER.debug(f"Checking device {device_id_tup}")
            #-- check if device needs to be deleted from concertim
            if device._delete_marker and device_id_tup[0]:
                self.__LOGGER.debug(f"Device marked for delete - deleting device {device_id_tup}")
                self.delete_stale_device(device)
            #-- check if the device has a concertim ID, if so update, else create
            #-- Check for device type here and branch to different function
            elif device_id_tup[0] and device_id_tup[1]:
                self.__LOGGER.debug(f"Device exists in Concertim - updating device {device_id_tup}")
                self.update_existing_device(device)
            elif not device_id_tup[0] and device_id_tup[1]:
                if not self.view.racks[device.rack_id_tuple].id[0]:
                    self.__LOGGER.debug(f"Device not found in Concertim - Cannot create device - waiting for rack to be created first - skipping")
                    continue
                self.__LOGGER.debug(f"Device not found in Concertim - creating device {device_id_tup}")
                created_device = self.create_new_device(device)
                device.id = (created_device['id'], device_id_tup[1])
            else:
                self.__LOGGER.warning(f"Unrecognized device found in view {device}")
        self.__LOGGER.debug("Finished -- Sending devices changes")

    def update_existing_template(self, template_obj):
        self.__LOGGER.debug(f"Starting --- Updating existing template {template_obj.id}")
        # OBJECT LOGIC
        if template_obj._updated:
            try:
                self.clients['concertim'].update_template(
                    ID=template_obj.id[0],
                    variables_dict={
                        "name": template_obj.name[1],
                        "description": template_obj.description
                    }
                )
            except Exception as e:
                self.__LOGGER.error(f"FAILED - Could not update template {template_obj} - {e} - skipping")
                self.__LOGGER.exception(e)
                return
        self.__LOGGER.debug(f"Finished --- Updating existing template {template_obj.id}")

    def create_new_template(self, template_obj):
        self.__LOGGER.debug(f"Starting --- Creating new template {template_obj.id}")
        # OBJECT LOGIC
        try:
            new_template = self.clients['concertim'].create_template(
                variables_dict={
                    "name": template_obj.name[1],
                    "description": template_obj.description,
                    "height": template_obj.size,
                    "ram" : template_obj.ram,
                    "disk" :template_obj.disk ,
                    "vcpus" : template_obj.vcpus,
                    "foreign_id" : template_obj.id[1]
                }
            )
            template_obj.id = (new_template['id'], template_obj.id[1])
        except Exception as e:
            self.__LOGGER.error(f"FAILED - Could not create template {template_obj} - {e} - skipping")
            self.__LOGGER.exception(e)
            return
        self.__LOGGER.debug(f"Finished --- Creating new template {template_obj.id}")

    def update_existing_rack(self, rack_obj):
        self.__LOGGER.debug(f"Starting --- Updating existing rack {rack_obj.id}")
        # OBJECT LOGIC
        if rack_obj._updated:
            try:
                self.clients['concertim'].update_rack(
                    ID=rack_obj.id[0],
                    variables_dict={
                        "name": rack_obj.name[1],
                        "u_height": rack_obj.height,
                        "status" : rack_obj.status,
                        "network_details": rack_obj.network_details,
                        "creation_output": rack_obj._creation_output,
                        "openstack_stack_id" : rack_obj.id[1],
                        "openstack_stack_owner" : rack_obj.metadata['creator_cloud_name'],
                        "openstack_stack_owner_id" : rack_obj.team_id_tuple[1],
                        "stack_status_reason": rack_obj._status_reason,
                        'openstack_stack_output': rack_obj.output
                    }
                )
                rack_obj._updated = False
            except Exception as e:
                self.__LOGGER.error(f"FAILED - Could not update rack {rack_obj} - {e} - skipping")
                self.__LOGGER.exception(e)
                return
        self.__LOGGER.debug(f"Finished --- Updating existing rack {rack_obj.id}")

    def create_new_rack(self, rack_obj):
        self.__LOGGER.debug(f"Starting --- Creating new rack {rack_obj.id}")
        # OBJECT LOGIC
        try:
            rack_resp = self.clients['concertim'].create_rack(
                variables_dict={
                    "team_id": rack_obj.team_id_tuple[0],
                    "name": rack_obj.name[1],
                    "u_height": rack_obj.height,
                    "status" : rack_obj.status,
                    "network_details": rack_obj.network_details,
                    "creation_output": rack_obj._creation_output,
                    "order_id": rack_obj.id[2],
                    "openstack_stack_id" : rack_obj.id[1],
                    "openstack_stack_owner" : rack_obj.metadata['creator_cloud_name'],
                    "openstack_stack_owner_id" : rack_obj.team_id_tuple[1],
                    "stack_status_reason": rack_obj._status_reason,
                    'openstack_stack_output': rack_obj.output
                }
            )
            rack_obj.id = tuple((rack_resp['id'], rack_obj.id[1], rack_obj.id[2]))
        except Exception as e:
            self.__LOGGER.error(f"FAILED - Could not create rack {rack_obj} - {e} - skipping")
            self.__LOGGER.exception(e)
            return
        self.__LOGGER.debug(f"Finished --- Creating new rack {rack_obj.id}")

    def delete_stale_rack(self, rack_obj):
        self.__LOGGER.debug(f"Starting --- Deleting stale rack {rack_obj.id}")
        # OBJECT LOGIC
        try:
            self.clients['concertim'].delete_rack(rack_obj.id[0], recurse=True)
        except Exception as e:
            self.__LOGGER.error(f"FAILED - Deleting rack from concertim {rack_obj} - {e} - skipping")
            self.__LOGGER.exception(e)
            return
        self.__LOGGER.debug(f"Finished --- Deleting stale rack {rack_obj.id}")

    def update_existing_device(self, device_obj):
        self.__LOGGER.debug(f"Starting --- Updating existing device {device_obj.id}")
        # OBJECT LOGIC
        if device_obj._updated:
            try:
                self.clients['concertim'].update_device(
                    ID=device_obj.id[0],
                    variables_dict={
                        "name": device_obj.name[1],
                        "description": device_obj.description,
                        "status" : device_obj.status,
                        "public_ips": device_obj.public_ips,
                        "private_ips": device_obj.private_ips,
                        "ssh_key": device_obj.ssh_key,
                        "volume_details": device_obj.volume_details,
                        "login_user": device_obj.login_user,
                        "net_interfaces": device_obj.network_interfaces,
                        'openstack_instance_id': device_obj.id[1],
                        "openstack_stack_id": device_obj.rack_id_tuple[1]
                    }
                )
                device_obj._updated = False
            except Exception as e:
                self.__LOGGER.error(f"FAILED - Could not update device {device_obj} - {e} - skipping")
                self.__LOGGER.exception(e)
                return
        self.__LOGGER.debug(f"Finished --- Updating existing device {device_obj.id}")

    def create_new_device(self, device_obj):
        self.__LOGGER.debug(f"Starting --- Creating new device {device_obj.id}")
        # OBJECT LOGIC
        try:
            self.clients['concertim'].create_compute_device(
                variables_dict={
                    "template_id": device_obj.template.id[0],
                    "name": device_obj.name[0],
                    "description": device_obj.description,
                    "status" : device_obj.status,
                    "facing": device_obj.location.facing,
                    "rack_id": self.view.racks[device_obj.rack_id_tuple].id[0],
                    "start_u": device_obj.location.start_u,
                    "net_interfaces": device_obj.network_interfaces,
                    "public_ips": device_obj.details.get('public_ips'),
                    "private_ips": device_obj.details.get('private_ips'),
                    "ssh_key": device_obj.details.get('ssh_key'),
                    "volume_details": device_obj.details.get('volume_details'),
                    "login_user": device_obj.details.get('login_user'),
                    'openstack_instance_id': device_obj.id[1],
                    "openstack_stack_id": self.view.racks[device_obj.rack_id_tuple].id[1]
                }
            )
        except Exception as e:
            self.__LOGGER.error(f"FAILED - Could not create device {device_obj} - {e} - skipping")
            self.__LOGGER.exception(e)
            return
        self.__LOGGER.debug(f"Finished --- Creating new device {device_obj.id}")

    def delete_stale_device(self, device_obj):
        self.__LOGGER.debug(f"Starting --- Deleting stale device {device_obj.id}")
        # OBJECT LOGIC
        try:
            self.clients['concertim'].delete_device(device_obj.id[0])
        except Exception as e:
            self.__LOGGER.error(f"FAILED - Deleting device from concertim {device_obj} - {e} - skipping")
            return
        self.__LOGGER.debug(f"Finished --- Deleting stale device {device_obj.id}")

    ##############################
    # HANDLER REQUIRED FUNCTIONS #
    ##############################
    def run_process(self):
        """
        The main running loop of the Handler.
        """
        self.__LOGGER.info(f"=====================================================================================")
        self.__LOGGER.info(f"Starting - Updating Concertim Front-end with current View data")
        # EXIT CASES
        if 'concertim' not in self.clients or not self.clients['concertim']:
            raise EXCP.NoClientFound('concertim')

        #-- Load current view
        try:
            self.view = UTILS.load_view()
        except Exception as e:
            self.__LOGGER.error(f"Could not load view - waiting for next loop")
            self.__LOGGER.exception(e)

        if self.view:
            #-- Edit Templates
            self.templates_changes()
            #-- Edit Racks
            self.racks_changes()
            #-- Edit Devices
            self.devices_changes()
            #-- Reflect any ID changes in the keys of the view dicts
            self.view.rebuild_indices()

        # Persist any ID changes we've caused by creating Concertim objects.
        # SyncHandler will blow these away when it completes its next run but by
        # that point the IDs should be in the Concertim source data anyway.
        # Doing this prevents us from trying to create objects in Concertim
        # again that we created on our previous run. Such attempts would fail
        # and prevent any other changes from being made later in the run.
        UTILS.save_view(self.view)
        UTILS.merge_views()
        
        self.__LOGGER.info(f"Finished - Updating Concertim Front-end with current View data")
        self.__LOGGER.info(f"=====================================================================================\n\n")
        time.sleep(UpdatesHandler.UPDATES_INTERVAL)

    def disconnect(self):
        """
        Function for disconnecting all clients before garbage collection.
        """
        self.__LOGGER.info("Disconnecting Updates Clients and Components")
        for name, client in self.clients.items():
            client.disconnect()
        self.clients = None

    ###########################
    # UPDATES HANDLER HELPERS #
    ###########################
