# Local Imports
from conser.utils.service_logger import create_logger
from conser.factory.abs_classes.handlers import AbsViewHandler
import conser.exceptions as EXCP
import conser.utils.common as UTILS
from conser.modules.clients.concertim.objects.view import ConcertimView
from conser.modules.clients.concertim.objects.device import ConcertimDevice
from conser.modules.clients.concertim.objects.rack import ConcertimRack
from conser.modules.clients.concertim.objects.template import ConcertimTemplate
from conser.modules.clients.concertim.objects.user import ConcertimUser
from conser.modules.clients.concertim.objects.team import ConcertimTeam
from conser.modules.clients.concertim.objects.location import Location

# Py Packages
import time

class SyncHandler(AbsViewHandler):
    """
    The Sync handlers main purpose is to pull data from the configured cloud
    and update the 'view' object with any new information. 

    This is achieved by first pulling in any existing data from Concertim,
    then fetching the data from the cloud, consolidating the two sets,
    and finally saving the resulting set of data to the view for other handlers
    to consume.
    """
    ############
    # DEFAULTS #
    ############
    # interval = 15 (resync_interval * resync_amount) to match concertim MRD polling interval
    RESYNC_INTERVAL = 3
    RESYNC_CHECKS_AMOUNT = 5
    # Metadata is mapped with concertim_field:middleware_field
    METADATA_MAPPING = {
        'rack': {
            "openstack_stack_id": "cluster_cloud_id",
            "stack_status_reason": "status_reason",
            "openstack_stack_owner": "user_cloud_name",
            "openstack_stack_output": "output",
            "openstack_stack_owner_id": "project_cloud_id"
        },
        'device': {
            "net_interfaces": "network_interfaces",
            "openstack_instance_id": "device_cloud_id",
            "openstack_stack_id": "cluster_cloud_id"
        }
    }

    ########
    # INIT #
    ########
    def __init__(self, clients_dict, log_file, log_level):
        self._LOG_LEVEL = log_level
        self._LOG_FILE = log_file
        self.__LOGGER = create_logger(__name__, self._LOG_FILE, self._LOG_LEVEL)
        self.clients = clients_dict
        self.view = None

    ##########################
    # SYNC HANDLER FUNCTIONS #
    ##########################
    ### The 'run_process' function contains the main loop controller
    ### located under 'HANDLER REQUIRED FUNCTIONS' header

    def pull_cloud_data(self):
        self.__LOGGER.info(f"Starting - Populating Cloud Data")
        self.layer_cloud_tempaltes()
        self.layer_cloud_racks()
        self.layer_cloud_devices()
        self.__LOGGER.info(f"Finished - Populating Cloud Data")

    def pull_concertim_view(self):
        self.__LOGGER.info(f"Starting - Populating Concertim View")
        #self.fetch_concertim_teams() -- to be implemented with new teams concept - temp solution for now
        # /TEMP
        self._build_teams_from_projects()
        # TEMP/
        self.fetch_concertim_users()
        self.fetch_concertim_templates()
        self.fetch_concertim_racks()
        self.fetch_concertim_devices()
        self.map_concertim_components()
        self.__LOGGER.info(f"Finished - Populating Concertim View")

    def fetch_concertim_users(self):
        self.__LOGGER.debug("Starting -- Fetching Concertim Users")
        # EXIT CONDITIONS
        if 'concertim' not in self.clients or not self.clients['concertim']:
            raise EXCP.NoClientFound('concertim')

        # OBJECT LOGIC
        con_users_list = self.clients['concertim'].list_users()
        for con_user in con_users_list:
            # Skip admin user
            if con_user['root']:
                continue
            self.__LOGGER.debug(f"Starting --- Creating new ConcertimUser -> {con_user['id']}")
            new_user = ConcertimUser(
                concertim_id=con_user['id'], 
                cloud_id=None if not con_user['cloud_user_id'] else con_user['cloud_user_id'], 
                billing_id=None if not con_user['billing_acct_id'] else con_user['billing_acct_id'],
                concertim_name=con_user['login'], 
                cloud_name='CM_' + con_user['login'], 
                full_name=con_user['fullname'], 
                email=con_user['email'], 
                default_project_cloud_id=None if not con_user['project_id'] else con_user['project_id'], 
                description="User pulled from Concertim"
            )
            new_user.billing_period_start = con_user['billing_period_start'] if 'billing_period_start' in con_user and con_user['billing_period_start'] else ''
            new_user.billing_period_end = con_user['billing_period_end'] if 'billing_period_end' in con_user and con_user['billing_period_end'] else ''
            self.view.add_user(new_user)
            self.__LOGGER.debug(f"Finished --- New ConcertimUser created in View : '{new_user}'")
        self.__LOGGER.debug("Finished -- Fetching Concertim Users")
    
    def fetch_concertim_templates(self):
        self.__LOGGER.debug("Starting -- Fetching Concertim Templates")
        # EXIT CONDITIONS
        if 'concertim' not in self.clients or not self.clients['concertim']:
            raise EXCP.NoClientFound('concertim')

        # OBJECT LOGIC
        con_templates_list = self.clients['concertim'].list_templates()
        for con_template in con_templates_list:
            self.__LOGGER.debug(f"Starting --- Creating new ConcertimTemplate -> '{con_template['id']}'")
            new_template = ConcertimTemplate(
                concertim_id=con_template['id'], 
                cloud_id=con_template['foreign_id'], 
                concertim_name=con_template['name'], 
                cloud_name=con_template['name'], 
                ram=con_template['ram'], 
                disk=con_template['disk'], 
                vcpus=con_template['vcpus'], 
                size=con_template['height'], 
                description=con_template['description']
            )
            self.view.add_template(new_template)
            self.__LOGGER.debug(f"Finished --- New ConcertimTemplate created in View : '{new_template}'")
        self.__LOGGER.debug("Finished -- Fetching Concertim Templates")

    def fetch_concertim_racks(self):
        self.__LOGGER.debug("Starting -- Fetching Concertim Racks")
        # EXIT CONDITIONS
        if 'concertim' not in self.clients or not self.clients['concertim']:
            raise EXCP.NoClientFound('concertim')

        # OBJECT LOGIC
        con_racks_list = self.clients['concertim'].list_racks()
        for con_rack in con_racks_list:
            self.__LOGGER.debug(f"Starting --- Creating new ConcertimRack -> '{con_rack['id']}'")
            #-- Parse metadata
            cluster_cloud_id = None
            cluster_metadata = {}
            for k,v in con_rack['metadata'].items():
                if k in SyncHandler.METADATA_MAPPING['rack']:
                    if SyncHandler.METADATA_MAPPING['rack'][k] == 'cluster_cloud_id':
                        cluster_cloud_id = v
                    else:
                        cluster_metadata[SyncHandler.METADATA_MAPPING['rack'][k]] = v
            #-- Grab IDs
            cluster_user_concertim_id = None if not con_rack['owner']['id'] else con_rack['owner']['id']
            cluster_user_cloud_id = None if not con_rack['owner']['cloud_user_id'] else con_rack['owner']['cloud_user_id']
            #-- Create rack
            new_rack = ConcertimRack(
                concertim_id=con_rack['id'], 
                cloud_id=cluster_cloud_id, 
                billing_id=None if not con_rack['order_id'] else con_rack['order_id'],
                concertim_name=con_rack['name'], 
                cloud_name=con_rack['name'] , 
                user_id_tuple=tuple((cluster_user_concertim_id, cluster_user_cloud_id, None)), 
                height=con_rack['u_height'], 
                description='' if 'description' not in con_rack else con_rack['description'], 
                status=con_rack['status']
            )
            new_rack.metadata = cluster_metadata
            if 'network_details' in con_rack and con_rack['network_details']:
                new_rack.network_details = con_rack['network_details']
            if 'creation_output' in con_rack and con_rack['creation_output']:
                new_rack._creation_output = con_rack['creation_output']
            self.__LOGGER.debug(f"Finished --- New ConcertimRack created in View : '{new_rack}'")
        self.__LOGGER.debug("Finished -- Fetching Concertim Racks")

    def fetch_concertim_devices(self):
        self.__LOGGER.debug("Starting -- Fetching Concertim Devices")
        # EXIT CONDITIONS
        if 'concertim' not in self.clients or not self.clients['concertim']:
            raise EXCP.NoClientFound('concertim')

        # OBJECT LOGIC
        con_devices_list = self.clients['concertim'].list_devices()
        for con_device in con_devices_list:
            self.__LOGGER.debug(f"Starting --- Creating new ConcertimDevice -> '{con_device['id']}'")
            #-- CHECK FOR DEVICE TYPE HERE
            new_device = self._create_server_device_from_concertim(con_device)
            self.view.add_device(new_device)
            self.__LOGGER.debug(f"Finished --- New ConcertimDevice created in View : '{new_device}'")  
        self.__LOGGER.debug("Finished -- Fetching Concertim Devices")

    def map_concertim_components(self):
        self.__LOGGER.debug("Starting -- Mapping Concertim data to each other")
        #self.map_users_to_teams() -- to be implemented with new teams concept - _build_teams_from_projects does this currently
        self.map_racks_to_users()
        self.map_devices_to_racks()
        self.__LOGGER.debug("Finished -- Mapping Concertim data")

    def map_racks_to_users(self):
        self.__LOGGER.debug("Starting --- Mapping Racks to existing Users")
        # EXIT CONDITIONS
        # OBJECT LOGIC
        #-- Loop over all existing racks in concertim (View has just finished pulling all concertim data)
        for rack_id_tup, rack in self.view.racks.items():
            self.__LOGGER.debug(f"Starting ---- Attempting to map rack '{rack.id}' to a user")
            #---- Get the rack's corresponding user object (check for cloud_id, then concertim_id if no cloud_id present)
            user = None
            if rack.user_id_tuple[1] and not user:
                user = self.view.search(
                    object_type='user',
                    id_value=rack.user_id_tuple[1],
                    id_origin='cloud'
                )
            if rack.user_id_tuple[0] and not user:
                user = self.view.search(
                    object_type='user',
                    id_value=rack.user_id_tuple[0],
                    id_origin='concertim'
                )
            #---- If no user is found, skip rack mapping and throw warning
            if not user:
                self.__LOGGER.warning(f"Warning ---- Could not map rack '{rack.id}' - No User matching '{rack.user_id_tuple}' found in View")
                continue
            #---- Reaching here means user is found, so add rack_id_tup to user's racks list
            if rack.id not in self.view.users[user.id].racks:
                self.view.users[user.id].add_rack(rack.id)
                self.view.racks[rack.id].user_id_tuple = user.id
                self.__LOGGER.debug(f"Finished ---- Mapped rack '{rack.id}' to user '{user.id}'")
        self.__LOGGER.debug("Finished --- Mapping Racks to existing Users")

    def map_devices_to_racks(self):
        self.__LOGGER.debug("Starting --- Mapping Devices to existing Racks")
        # EXIT CONDITIONS
        #-- Loop over all existing devices in concertim (View has just finished pulling all concertim data)
        for device_id_tup, device in self.view.devices.items():
            self.__LOGGER.debug(f"Starting ---- Attempting to map device '{device.id}' to a rack")
            #---- Get the device's corresponding rack object (check for cloud_id, then concertim_id if no cloud_id present)
            rack = None
            if device.rack_id_tuple[1] and not rack:
                rack = self.view.search(
                    object_type='rack',
                    id_value=device.rack_id_tuple[1],
                    id_origin='cloud'
                )
            if device.rack_id_tuple[0] and not rack:
                rack = self.view.search(
                    object_type='rack',
                    id_value=device.rack_id_tuple[0],
                    id_origin='concertim'
                )
            #---- If no rack is found, skip device mapping and throw warning
            if not rack:
                self.__LOGGER.warning(f"Warning ---- Could not map device '{device.id}' - No Rack matching '{device.rack_id_tuple}' found in View")
                continue
            #---- Reaching here means rack is found, so add device_id_tup to rack's devices list
            if device.id not in self.view.racks[rack.id].devices:
                self.view.racks[rack.id].add_device(device.id)
                self.view.devices[device.id].rack_id_tuple = rack.id
                self.__LOGGER.debug(f"Finished ---- Mapped device '{device.id}' to rack '{rack.id}'")
        # OBJECT LOGIC
        self.__LOGGER.debug("Finished --- Mapping Devices to existing Racks")

    def layer_cloud_tempaltes(self):
        self.__LOGGER.debug("Starting -- Layering Cloud Templates onto existing View")
        # EXIT CONDITIONS
        create_all = False
        if 'cloud' not in self.clients or not self.clients['cloud']:
            raise EXCP.NoClientFound('cloud')
        if not self.view.templates:
            self.__LOGGER.warning("Warning --- No existing Templates found in view - Creating all new templates from cloud data")
            create_all = True
        
        # OBJECT LOGIC
        #-- Getting all templates (flavors) 
        cloud_templates_dict = self.clients['cloud'].get_all_flavors()
        for template_cloud_id, cloud_template_dict in cloud_templates_dict['flavors'].items():
            #---- Check if the template cloud data matches an already existing concertim template
            #------ if so, move to update instead of create
            if not create_all:
                matching_template = self.view.search(
                    object_type='template',
                    id_value=template_cloud_id,
                    id_origin='cloud'
                )
                if matching_template:
                    self.update_template_from_cloud(cloud_template_dict, matching_template.id)
                    continue
            #---- If reaching here then need to create a new ConcertimTemplate from cloud data
            self.create_template_from_cloud(cloud_template_dict)
        self.__LOGGER.debug("Finished -- Layering Cloud Templates onto existing View")

    def layer_cloud_racks(self):
        self.__LOGGER.debug("Starting -- Layering Cloud Racks onto existing View")
        # EXIT CONDITIONS
        create_all = False
        if 'cloud' not in self.clients or not self.clients['cloud']:
            raise EXCP.NoClientFound('cloud')
        if 'billing' not in self.clients or not self.clients['billing']:
            raise EXCP.NoClientFound('billing')
        if not self.view.racks:
            self.__LOGGER.warning("Warning --- No existing Racks found in view - Creating all new racks from cloud data")
            create_all = True

        # OBJECT LOGIC
        #-- Getting all racks (clusters) 
        cloud_clusters_dict = self.clients['cloud'].get_all_clusters()
        for cluster_cloud_id, cloud_cluster_dict in cloud_clusters_dict['clusters'].items():
            #---- Check if the cluster cloud data matches an already existing concertim rack
            #------ if so, move to update instead of create
            if not create_all:
                matching_rack = self.view.search(
                    object_type='rack',
                    id_value=cluster_cloud_id,
                    id_origin='cloud'
                )
                if matching_rack:
                    self.update_rack_from_cloud(cloud_cluster_dict, matching_rack.id)
                    continue
            #---- If reaching here then need to create a new ConcertimRack from cloud data
            #------ Verification that the rack should be in concertim is done in create_rack function
            self.create_rack_from_cloud(cloud_cluster_dict)
        self.__LOGGER.debug("Finished -- Layering Cloud Racks onto existing View")

    def layer_cloud_devices(self):
        self.__LOGGER.debug("Starting -- Layering Cloud Devices onto existing View")
        # EXIT CONDITIONS
        create_all = False
        if 'cloud' not in self.clients or not self.clients['cloud']:
            raise EXCP.NoClientFound('cloud')
        if not self.view.racks:
            self.__LOGGER.warning("Warning --- No existing Devices found in view - Creating all new devices from cloud data")
            create_all = True

        # OBJECT LOGIC
        #-- Getting all Concertim Managed projects
        cm_projects_list = self.clients['cloud'].get_all_cm_projects()
        for project_cloud_id in cm_projects_list['projects']:
            ## SERVER DEVICES LOGIC
            #---- For each project, get all servers (devices)
            cloud_servers_dict = self.clients['cloud'].get_all_servers(project_cloud_id=project_cloud_id)
            for server_cloud_id, cloud_server_dict in cloud_servers_dict['servers'].items():
                #------ Check if the server cloud data matches an already existing concertim device
                #-------- if so, move to update instead of create
                if not create_all:
                    matching_device = self.view.search(
                        object_type='device',
                        id_value=server_cloud_id,
                        id_origin='cloud'
                    )
                    if matching_device:
                        self.update_server_device_from_cloud(cloud_server_dict, matching_device.id)
                        continue         
                #------ If reaching here then need to create a new ConcertimDevice from cloud data
                self.create_server_device_from_cloud(cloud_server_dict)
            ## VOLS
            ## NETS
        self.__LOGGER.debug("Finished -- Layering Cloud Devices onto existing View")

    def create_template_from_cloud(self, template_dict):
        # EXIT CONDITIONS
        if not template_dict:
            raise EXCP.MissingRequiredArgs('template_dict')
        self.__LOGGER.debug(f"Starting --- Creating new ConcertimTemplate -> '{template_dict['name']}' - from cloud data")
        # OBJECT LOGIC
        template_size = min((int( template_dict['vcpus'] / 2 ) + 1), 4)
        new_template = ConcertimTemplate(
            concertim_id=None, 
            cloud_id=template_dict['id'], 
            concertim_name=template_dict['name'], 
            cloud_name=template_dict['name'], 
            ram=template_dict['ram'], 
            disk=template_dict['disk'], 
            vcpus=template_dict['vcpus'], 
            size=template_size, 
            description="Template created from Cloud by Concertim Service"
        )
        self.view.add_template(new_template)
        self.__LOGGER.debug(f"Finished --- Created new ConcertimTemplate from cloud data")

    def update_template_from_cloud(self, template_dict, template_id_tup):
        # EXIT CONDITIONS
        if not template_dict:
            raise EXCP.MissingRequiredArgs('template_dict')
        if not template_id_tup:
            raise EXCP.MissingRequiredArgs('template_id_tup')
        self.__LOGGER.debug(f"Starting --- Updating existing ConcertimTemplate '{template_id_tup}' with cloud data")

        # OBJECT LOGIC
        con_template = self.view.templates[template_id_tup]
        if con_template.ram != template_dict['ram']:
            self.view.templates[template_id_tup].ram = template_dict['ram']
            self.view.templates[template_id_tup]._updated = True

        if con_template.disk != template_dict['disk']:
            self.view.templates[template_id_tup].disk = template_dict['disk']
            self.view.templates[template_id_tup]._updated = True

        if con_template.vcpus != template_dict['vcpus']:
            self.view.templates[template_id_tup].vcpus = template_dict['vcpus']
            self.view.templates[template_id_tup]._updated = True

        cloud_template_size = min((int( template_dict['vcpus'] / 2 ) + 1), 4)
        if con_template.size != cloud_template_size:
            self.view.templates[template_id_tup].size = cloud_template_size
            self.view.templates[template_id_tup]._updated = True

        self.__LOGGER.debug(f"Finished --- Updated existing ConcertimTemplate from cloud data")

    def create_rack_from_cloud(self, cluster_dict):
        # EXIT CONDITIONS
        if not cluster_dict:
            raise EXCP.MissingRequiredArgs('cluster_dict')
        if 'CM_' not in cluster_dict['user_cloud_name']:
            return
        self.__LOGGER.debug(f"Starting --- Creating new ConcertimRack -> '{cluster_dict['name']}' - from cloud data")
        
        # OBJECT LOGIC
        #-- Search for the billing order for the cluster
        matching_billing_subs = self.clients['billing'].lookup_cluster_billing_info(
            cluster_cloud_id=cluster_dict['id']
        )
        cluster_billing_id = None
        if matching_billing_subs['count'] < 1:
            self.__LOGGER.warning(f"Warning --- No matching billing order found for cluster '{cluster_dict['id']}' - setting as None")
        elif matching_billing_subs['count'] > 1:
            raise EXCP.TooManyBillingOrders(matching_billing_subs)
        else:
            cluster_billing_id = list(matching_billing_subs['subscriptions'])[0]

        #-- Search for the cluster owner
        matching_user = None
        for user_id_tup, con_user in self.view.users.items():
            if con_user.name[1] == cluster_dict['user_cloud_name']:
                matching_user = con_user
                break
        #-- If there is no matching user, log Error and skip
        if not matching_user:
            self.__LOGGER.error(f"ERROR --- No matching User found for cluster '{cluster_dict['id']}' - owner is '{cluster_dict['user_cloud_name']}' - skipping")
            return
        #-- Get accurate status
        cluster_status = 'FAILED'
        for con_status, valid_cloud_status_list in self.clients['cloud'].CONCERTIM_STATE_MAP['RACK'].items():
            if cluster_dict['status'] in valid_cloud_status_list:
                cluster_status = con_status
        #-- All items found, create rack in view
        new_rack = ConcertimRack(
            concertim_id=None, 
            cloud_id=cluster_dict['id'],
            billing_id=cluster_billing_id,
            concertim_name=cluster_dict['name'],
            cloud_name=cluster_dict['name'],
            user_id_tuple=matching_user.id,
            height=self.clients['concertim'].rack_height, 
            description='Rack created from Cloud by Concertim Service', 
            status=cluster_status
        )
        new_rack.output = cluster_dict['cluster_outputs']
        new_rack._creation_output = self._get_output_as_string(cluster_dict['cluster_outputs'])
        #TODO: Get nework details here
        new_rack.network_details = {}
        for con_md, cloud_md in SyncHandler.METADATA_MAPPING['rack'].items():
            if cloud_md in cluster_dict:
                new_rack.metadata[cloud_md] = cluster_dict[cloud_md]
        new_rack._resources = cluster_dict['cluster_resources']
        new_rack._status_reason = cluster_dict['status_reason']
        new_rack._delete_marker = False
        self.view.add_rack(new_rack)
        self.__LOGGER.debug(f"Finished --- Created new ConcertimRack from cloud data")

    def update_rack_from_cloud(self, cluster_dict, rack_id_tup):
        # EXIT CONDITIONS
        if not cluster_dict:
            raise EXCP.MissingRequiredArgs('cluster_dict')
        if not rack_id_tup:
            raise EXCP.MissingRequiredArgs('rack_id_tup')
        self.__LOGGER.debug(f"Starting --- Updating existing ConcertimRack '{rack_id_tup}' with cloud data")

        # OBJECT LOGIC
        con_rack = self.view.racks[rack_id_tup]
        #-- Get current accurate status
        cluster_status = 'FAILED'
        for con_status, valid_cloud_status_list in self.clients['cloud'].CONCERTIM_STATE_MAP['RACK'].items():
            if cluster_dict['status'] in valid_cloud_status_list:
                cluster_status = con_status
        #-- Check dynamic vals
        if con_rack.output != cluster_dict['cluster_outputs']:
            self.view.racks[rack_id_tup].output = cluster_dict['cluster_outputs']
            self.view.racks[rack_id_tup]._updated = True

        if con_rack.status != cluster_status:
            self.view.racks[rack_id_tup].status = cluster_status
            self.view.racks[rack_id_tup]._updated = True

        clust_output_string = self._get_output_as_string(cluster_dict['cluster_outputs'])
        if con_rack._creation_output != clust_output_string:
            self.view.racks[rack_id_tup]._creation_output = clust_output_string
            self.view.racks[rack_id_tup]._updated = True

        if con_rack._resources != cluster_dict['cluster_resources']:
            self.view.racks[rack_id_tup]._resources = cluster_dict['cluster_resources']
            self.view.racks[rack_id_tup]._updated = True

        if con_rack._status_reason != cluster_dict['status_reason']:
            self.view.racks[rack_id_tup]._status_reason = cluster_dict['status_reason']
            self.view.racks[rack_id_tup]._updated = True

        curr_cluster_metadata = {}
        for con_md, cloud_md in SyncHandler.METADATA_MAPPING['rack'].items():
            if cloud_md in cluster_dict:
                curr_cluster_metadata = cluster_dict[cloud_md]
        for k,v in con_rack.metadata.items():
            if k in curr_cluster_metadata and v != curr_cluster_metadata[k]:
                self.view.racks[rack_id_tup].metadata[k] = curr_cluster_metadata[k]
                self.view.racks[rack_id_tup]._updated = True
        
        #TODO: Check/Update network_details

        self.view.racks[rack_id_tup]._delete_marker=False
        self.__LOGGER.debug(f"Finished --- Updated existing ConcertimRack from cloud data")

    def create_server_device_from_cloud(self, server_dict):
        # EXIT CONDITIONS
        if not server_dict:
            raise EXCP.MissingRequiredArgs('server_dict')
        self.__LOGGER.debug(f"Starting --- Creating new ConcertimDevice -> '{server_dict['name']}' - from cloud data")

        # OBJECT LOGIC
        #-- Search for the containing rack
        matching_rack = None
        for rack_id_tup, con_rack in self.view.racks.items():
            #---- for every rack matching the project, check if server ID is in resources list
            if con_rack.metadata['project_cloud_id'] != server_dict['project_cloud_id']:
                continue
            for server_res_id in con_rack._resources['servers']:
                if server_res_id == server_dict['id']:
                    matching_rack = con_rack
                    break
            if matching_rack:
                break
        #---- If there is no matching rack, log Error and skip
        if not matching_rack:
            self.__LOGGER.error(f"ERROR --- No matching Rack found for device '{server_dict['id']}' - skipping")
            return
        #-- Get accurate status
        device_status = 'FAILED'
        for con_status, valid_cloud_status_list in self.clients['cloud'].CONCERTIM_STATE_MAP['DEVICE'].items():
            if server_dict['status'] in valid_cloud_status_list:
                device_status = con_status
        #-- Grab device Template
        server_template = self.view.search(
            object_type='template', 
            id_value=server_dict['template_cloud_id'], 
            id_origin='cloud'
        )
        #-- Create device
        new_device = ConcertimDevice(
            concertim_id=None, 
            cloud_id=server_dict['id'], 
            concertim_name=server_dict['name'], 
            cloud_name=server_dict['name'], 
            rack_id_tuple=matching_rack.id, 
            template=server_template, 
            location=None, 
            description="Server Device created from Cloud by Concertim Service", 
            status=device_status
        )
        new_device.ssh_key = server_dict['ssh_key_name']
        new_device.volume_details = server_dict['volumes']
        new_device.public_ips = server_dict['public_ips']
        new_device.private_ips = server_dict['private_ips']
        new_device.network_interfaces = server_dict['network_interfaces']
        #TODO: Get login user for server
        new_device.login_user = ''
        new_device._delete_marker=False
        self.view.add_device(new_device)
        self.__LOGGER.debug(f"Finished --- Created new ConcertimDevice from cloud data")

    def update_server_device_from_cloud(self, server_dict, device_id_tup):
        # EXIT CONDITIONS
        if not server_dict:
            raise EXCP.MissingRequiredArgs('server_dict')
        if not device_id_tup:
            raise EXCP.MissingRequiredArgs('device_id_tup')
        self.__LOGGER.debug(f"Starting --- Updating existing ConcertimDevice '{device_id_tup}' with cloud data")

        # OBJECT LOGIC
        con_device = self.view.devices[device_id_tup]
        #-- Get current accurate status
        device_status = 'FAILED'
        for con_status, valid_cloud_status_list in self.clients['cloud'].CONCERTIM_STATE_MAP['DEVICE'].items():
            if server_dict['status'] in valid_cloud_status_list:
                device_status = con_status
        #-- Check dynamic values
        if con_device.status != device_status:
            self.view.devices[device_id_tup].status = device_status
            self.view.devices[device_id_tup]._updated = True

        if con_device.volume_details != server_dict['volumes']:
            self.view.devices[device_id_tup].volume_details = server_dict['volumes']
            self.view.devices[device_id_tup]._updated = True

        if con_device.public_ips != server_dict['public_ips']:
            self.view.devices[device_id_tup].public_ips = server_dict['public_ips']
            self.view.devices[device_id_tup]._updated = True

        if con_device.private_ips != server_dict['private_ips']:
            self.view.devices[device_id_tup].private_ips = server_dict['private_ips']
            self.view.devices[device_id_tup]._updated = True

        if con_device.network_interfaces != server_dict['network_interfaces']:
            self.view.devices[device_id_tup].network_interfaces = server_dict['network_interfaces']
            self.view.devices[device_id_tup]._updated = True

        self.view.devices[device_id_tup]._delete_marker=False
        self.__LOGGER.debug(f"Finished --- Updated existing ConcertimDevice from cloud data")

    ##############################
    # HANDLER REQUIRED FUNCTIONS #
    ##############################
    def run_process(self):
        """
        The main running loop of the Handler.
        """
        self.__LOGGER.info(f"=====================================================================================")
        self.__LOGGER.info(f"Starting - Full Cloud + Concertim mapping for View object")
        # Start with empty view
        self.view = ConcertimView()
        # Add existing concertim data to view
        self.pull_concertim_view()
        # Add cloud data ontop of concertim data - updating stale concertim values with new cloud data
        self.pull_cloud_data()
        # Save view
        self.__LOGGER.info("Saving View")
        UTILS.save_view(self.view)
        self.__LOGGER.info("View Successfully Saved")
        # Check for resyncs
        for i in range(SyncHandler.RESYNC_CHECKS_AMOUNT):
            self.__LOGGER.debug(f".....Checking for resync.....")
            if UTILS.check_resync_flag():
                self.__LOGGER.info(f"RESYNC FLAG FOUND - Deleting resync.flag and starting full sync process")
                UTILS.delete_resync_flag()
                return
            if UTILS.check_resync_hold():
                self.__LOGGER.debug(f"RESYNC HOLD FOUND - Waiting for hold to finish and resync.flag to appear")
                i -= 1
                time.sleep(0.2)
                continue
            time.sleep(SyncHandler.RESYNC_INTERVAL)
        # process finished - merge all saved views
        self.__LOGGER.debug(f"Merging saved views")
        UTILS.merge_views()
        self.__LOGGER.info(f"Finished - Full Cloud + Concertim mapping for View object")
        self.__LOGGER.info(f"=====================================================================================\n\n")


    def disconnect(self):
        """
        Function for disconnecting all clients before garbage collection.
        """
        self.__LOGGER.info("Disconnecting Sync Clients and Components")
        for name, client in self.clients.items():
            client.disconnect()
        self.clients = None

    ########################
    # SYNC HANDLER HELPERS #
    ########################
    
    def _get_output_as_string(self, output_list):
        output_str = ''
        for output_tup in output_list:
            output_str += f", {output_tup[0]}={output_tup[1]}" if output_str else f"{output_tup[0]}={output_tup[1]}"
        return output_str

    def _create_server_device_from_concertim(self, con_device):
        #-- Parse metadata
            device_cloud_id = None
            rack_cloud_id = None
            device_metadata = {}
            for k,v in con_device['metadata'].items():
                if k in SyncHandler.METADATA_MAPPING['device']:
                    if SyncHandler.METADATA_MAPPING['device'][k] == 'device_cloud_id':
                        device_cloud_id = v
                    elif SyncHandler.METADATA_MAPPING['device'][k] == 'cluster_cloud_id':
                        rack_cloud_id = v
                    else:
                        device_metadata[SyncHandler.METADATA_MAPPING['device'][k]] = v
            #-- Grab device Location 
            device_location = Location(
                start_u=con_device['location']['start_u'], 
                end_u=con_device['location']['end_u'], 
                facing=con_device['location']['facing']
            )
            #-- Grab device Template
            device_template = self.view.search(
                object_type='template', 
                id_value=con_device['template_id'], 
                id_origin='concertim'
            )
            #-- Grab IDs
            rack_concertim_id = con_device['location']['rack_id']
            #-- Create device
            new_device = ConcertimDevice(
                concertim_id=con_device['id'], 
                cloud_id=device_cloud_id, 
                concertim_name=con_device['name'], 
                cloud_name=con_device['name'], 
                rack_id_tuple=tuple((rack_concertim_id, rack_cloud_id, None)), 
                template=device_template, 
                location=device_location, 
                description=con_device['description'], 
                status=con_device['status']
            )
            new_device.ssh_key = con_device['ssh_key'] if 'ssh_key' in con_device and con_device['ssh_key'] else ''
            new_device.volume_details = con_device['volume_details'] if 'volume_details' in con_device and con_device['volume_details'] else []
            new_device.public_ips = con_device['public_ips'] if 'public_ips' in con_device and con_device['public_ips'] else ''
            new_device.private_ips = con_device['private_ips'] if 'private_ips' in con_device and con_device['private_ips'] else ''
            new_device.login_user = con_device['login_user'] if 'login_user' in con_device and con_device['login_user'] else ''
            return new_device

    def _build_teams_from_projects(self):
        self.__LOGGER.debug("Starting -- Building Concertim Teams in view based on Concertim Managed projects in cloud")
        # EXIT CASES
        if 'cloud' not in self.clients or not self.clients['cloud']:
            raise EXCP.NoClientFound('cloud')
        if 'billing' not in self.clients or not self.clients['billing']:
            raise EXCP.NoClientFound('billing')

        # OBJECT LOGIC
        cm_projects = self.clients['cloud'].get_all_cm_projects()
        #-- Loop over all CM_<project>s and find their billing acct
        for project_cloud_id in cm_projects['projects']:
            self.__LOGGER.debug(f"Starting --- Creating new ConcertimTeam for project '{project_cloud_id}'")
            billing_accts = None
            try:
                billing_accts = self.clients['billing'].lookup_project_billing_info(
                    project_cloud_id=project_cloud_id
                )
            except Exception as e:
                self.__LOGGER.error(f"FAILED - Could not retrieve billing info for project '{project_cloud_id}' - {e} - skipping")
                continue
            if billing_accts['count'] < 1:
                self.__LOGGER.warning(f"WARNING - No billing account found for project '{project_cloud_id}' - skipping")
                continue
            elif billing_accts['count'] > 1:
                raise EXCP.TooManyBillingAccounts(project_cloud_id)
            #-- Reaching here means that the billing acct is found and only 1 exists for the project - get project info and build team
            project_info = self.clients['cloud'].get_project_info(
                project_cloud_id=project_cloud_id
            )
            billing_acct = billing_accts['accounts'][0]
            new_team = ConcertimTeam(
                concertim_id=None, 
                cloud_id=project_cloud_id, 
                billing_id=billing_acct['id'],
                concertim_name=project_info['name'], 
                cloud_name=project_info['name'], 
                description="Team created from Cloud by Concertim Service"
            )
            new_team.team_members = project_info['users']['team_members']
            new_team.team_admins = project_info['users']['admins']
            new_team._primary_billing_user_cloud_id = billing_acct['primary_user_cloud_id']
            self.view.add_team(new_team)
            self.__LOGGER.debug(f"Finished --- New ConcertimTeam created in View : {new_team}")
        self.__LOGGER.debug("Finished -- Building Concertim Teams in view based on Concertim Managed projects in cloud")