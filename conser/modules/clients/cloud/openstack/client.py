# Local Imports
from conser.utils.service_logger import create_logger
from conser.factory.factory import Factory
from conser.factory.abs_classes.clients import AbsCloudClient
from conser.modules.clients.cloud.openstack.auth import OpenStackAuth
import conser.exceptions as EXCP

# Py Packages
import sys

# Openstack Exceptions
import novaclient.exceptions as NEXCP
import heatclient.exc as HEXCP

class OpenstackClient(AbsCloudClient):

    ############
    # DEFAULTS #
    ############
    DEFAULT_GRANULARITY = 15
    SUPPORTED_METRIC_GROUPS = {
        'metric_functions': {
            'cpu_load': 'calc_cpu_load',
            'ram_usage': 'calc_ram_usage',
            'network_usage': 'calc_network_usage',
            'throughput': 'calc_throughput',
            'iops': 'calc_iops'
        }
        'resource_map': {
            'server': {
                'metrics_list': ['cpu_load', 'ram_usage', 'network_usage', 'throughput', 'iops'],
                'resource_ids': {
                    'instance': 'id',
                    'instance_disk': 'instance_id',
                    'instance_network_interface': 'instance_id'
                }
            }
        }
    }
    SUPPORTED_COST_GROUPS = {
        'project': {
            'id_field': 'project_id'
        },
        'instance': {
            'id_field': 'id'
        }
    }
    VALID_SERVER_ACTIONS = {
        'on': 'switch_on_instance',
        'off': 'switch_off_instance',
        'suspend': 'suspend_instance',
        'resume': 'resume_instance',
        'destroy': 'destroy_instance'
    }
    VALID_CLUSTER_ACTIONS = {
        'suspend': 'suspend_stack',
        'resume': 'resume_stack',
        'destroy': 'destroy_stack'
    }

    ########
    # INIT #
    ########
    def __init__(self, openstack_config, components, log_file, log_level, required_ks_objs={}):
        self._LOG_LEVEL = log_level
        self._LOG_FILE = log_file
        self._CONFIG = openstack_config
        self.components = components
        self.__LOGGER = create_logger(__name__, self._LOG_FILE, self._LOG_LEVEL)
        self.__LOGGER.info("CREATING OPENSTACK CLIENT")
        self.req_keystone_objs = self.__populate_required_objs('keystone', self.required_ks_objs)

    ##########################################
    # CLOUD CLIENT OBJECT REQUIRED FUNCTIONS #
    ##########################################
    def create_cm_project(self, name, primary_user_cloud_id):
        """
        Create a new Concertim Managaed account/project

        returns a dict in the format
        return_dict = {
            'id': new_project.id,
            'project': new_project.__dict__._info
        }
        """
        self.__LOGGER.debug(f"Creating new Concertim-managed project '{name}'")
        # EXIT CASES
        if 'keystone' not in self.components or not self.components['keystone']:
            raise EXCP.NoComponentFound('keystone')
        if not self.req_keystone_objs['role']['admin'] 
            or not self.req_keystone_objs['role']['member']
            or not self.req_keystone_objs['role']['watcher']
            or not self.req_keystone_objs['role']['rating']
            or not self.req_keystone_objs['user']['admin']
            or not self.req_keystone_objs['user']['concertim']
            or not self.req_keystone_objs['user']['cloudkitty']:
            raise EXCP.MissingRequiredCloudObject(self.req_keystone_objs)
        if not primary_user_cloud_id:
            raise EXCP.MissingRequiredArgs('primary_user_cloud_id')

        # CLOUD OBJECT LOGIC
        #-- Create project
        new_project = self.components['keystone'].create_project(f"CM_{name}", 'default', desc="Concertim Managed Project")
        #-- Add users
        self.components['keystone'].add_user_to_project(
            user=primary_user_cloud_id,
            project=new_project,
            role=self.req_keystone_objs['role']['admin']
        )
        self.components['keystone'].add_user_to_project(
            user=self.req_keystone_objs['user']['admin'],
            project=new_project,
            role=self.req_keystone_objs['role']['admin']
        )
        self.components['keystone'].add_user_to_project(
            user=self.req_keystone_objs['user']['concertim'],
            project=new_project,
            role=self.req_keystone_objs['role']['watcher']
        )
        self.components['keystone'].add_user_to_project(
            user=self.req_keystone_objs['user']['cloudkitty'],
            project=new_project,
            role=self.req_keystone_objs['role']['rating']
        )
        self.__LOGGER.debug(f"New Concertim-managed project created successfully - '{new_project}'")

        # BUILD RETURN DICT
        self.__LOGGER.debug(f"Building Return dictionary")
        return_dict = {
            'id': new_project.id,
            'project': new_project._info
        }

        # RETURN
        return return_dict
    
    def create_cm_user(self, name, password, email):
        """
        Create a new Concertim Managed user.

        Returns a dict in the format
        return_dict = {
            'id': new_user.id,
            'user': new_user.__dict__['_info']
        }
        """
        self.__LOGGER.debug(f"Creating new Concertim-managed User for '{name}'")
        # EXIT CASES
        if 'keystone' not in self.components or not self.components['keystone']:
            raise EXCP.NoComponentFound('keystone')
        if not name or not password or not email:
            raise EXCP.MissingRequiredArgs('name', 'email', 'password')

        # CLOUD OBJECT LOGIC
        new_user = self.components['keystone'].create_user(name, password, 'default', email=email, desc="Concertim Managed User")
        self.__LOGGER.debug(f"New Concertim-managed User created successfully - '{new_user}'")

        # BUILD RETURN DICT
        return_dict = {
            'id': new_user.id,
            'user': new_user._info
        }

        # RETURN
        return return_dict

    def create_keypair(self, name, imported_pub_key=None, key_type='ssh', user_cloud_id=None):
        """
        Create a new KeyPair for a given User/Account
        """
        self.__LOGGER.debug(f"Create new keypair '{name}")
        # EXIT CASES
        if 'nova' not in self.components or not self.components['nova']:
            raise EXCP.NoComponentFound('nova')
        if not name or not key_type:
            raise EXCP.MissingRequiredArgs('name', 'key_type')

        # CLOUD OBJECT LOGIC
        new_keypair = self.components['nova'].create_keypair(
            name=name, 
            imported_pub_key=imported_pub_key, 
            key_type=key_type
        )
        self.__LOGGER.debug(f"New keypair created successfully - '{new_keypair}'")

        # BUILD RETURN DICT
        self.__LOGGER.debug(f"Building Return dictionary")
        return_dict = {
            'key_pair': new_keypair._info
        }

        # RETURN
        return return_dict

    def get_metrics(self, resource_type, resource_id, start, stop):
        """
        Get the metrics for a resource for each given metric type in the provided metrics list

        resource_id : the ID of the resource in the cloud
        Valid resource_type options:
            server
           #(not implemeted) volume
           #(not implemeted) network
        Valid metric types are:
            cpu_load
            ram_usage
            network_usage
            throughput
            iops
        """
        # EXIT CASES
        if 'gnocchi' not in self.components or not self.components['gnocchi']:
            raise EXCP.NoComponentFound('gnocchi')
        if resource_type not in OpenstackClient.SUPPORTED_METRIC_GROUPS['resource_map']:
            raise EXCP.InvalidArguments(f"resource_type:{resource_type}")
        if not resource_id:
            raise EXCP.MissingRequiredArgs(f"resource_id")
        if not start:
            raise EXCP.MissingRequiredArgs(f"start")
        if not stop:
            raise EXCP.MissingRequiredArgs(f"stop")

        # CLOUD OBJECT LOGIC
        granularity = OpenstackClient.DEFAULT_GRANULARITY
        resource_dict = {'metrics': {}}
        #-- CREATE INTERNAL CALCULATION FUNCTIONS
        def calc_cpu_load():
            self.__LOGGER.debug(f"Calculating CPU Load %")
            if 'cpu' not in resource_dict['metrics']:
                raise EXCP.MissingResourceMetric('cpu')
            try:
                cpu_rate = self.components['gnocchi'].get_metric_measure(
                    metric=resource_dict['metrics']['cpu'],
                    aggregation='rate:mean',
                    granularity=granularity,
                    start=start,
                    stop=stop
                )[-1][2]
                cpu_load_percent = cpu_rate / (1000000000.0 * granularity) * 100
                return round(cpu_load_percent,2), True
            except IndexError as ie:
                return 0.0, False

        def calc_ram_usage():
            self.__LOGGER.debug(f"Calculating RAM Usage %")
            if 'memory' not in resource_dict['metrics']:
                raise EXCP.MissingResourceMetric('memory')
            if 'memory.usage' not in resource_dict['metrics']:
                raise EXCP.MissingResourceMetric('memory.usage')
            try:
                memory = self.components['gnocchi'].get_metric_measure(
                    metric=resource_dict['metrics']['memory'],
                    refresh=False,
                    limit=1
                )[-1][2]
                memory_usage = self.components['gnocchi'].get_metric_measure(
                    metric=resource_dict['metrics']['memory.usage'],
                    aggregation='mean',
                    granularity=granularity,
                    start=start,
                    stop=stop
                )[-1][2]
                ram_usage = memory_usage / memory * 100
                return ram_usage, True
            except IndexError as ie:
                return 0.0, False

        def calc_network_usage():
            self.__LOGGER.debug(f"Calculating Network Usage %")
            if 'network.incoming.bytes' not in resource_dict['metrics']:
                raise EXCP.MissingResourceMetric('network.incoming.bytes')
            if 'network.outgoing.bytes' not in resource_dict['metrics']:
                raise EXCP.MissingResourceMetric('network.outgoing.bytes')
            try:
                net_in = self.components['gnocchi'].get_metric_measure(
                    metric=resource_dict['metrics']['network.incoming.bytes'],
                    aggregation='rate:mean',
                    granularity=granularity,
                    start=start,
                    stop=stop
                )[-1][2]
                net_out = self.components['gnocchi'].get_metric_measure(
                    metric=resource_dict['metrics']['network.outgoing.bytes'],
                    aggregation='rate:mean',
                    granularity=granularity,
                    start=start,
                    stop=stop
                )[-1][2]
                network_usage = (net_in + net_out) / granularity
                return network_usage, True
            except IndexError as ie:
                return 0.0, False
        
        def calc_throughput():
            self.__LOGGER.debug(f"Calculating Throughput")
            if 'disk.device.read.bytes' not in resource_dict['metrics']:
                raise EXCP.MissingResourceMetric('disk.device.read.bytes')
            if 'disk.device.write.bytes' not in resource_dict['metrics']:
                raise EXCP.MissingResourceMetric('disk.device.write.bytes')
            try:
                disk_read = self.components['gnocchi'].get_metric_measure(
                    metric=resource_dict['metrics']['disk.device.read.bytes'],
                    aggregation='rate:mean',
                    granularity=granularity,
                    start=start,
                    stop=stop
                )[-1][2]
                disk_write = self.components['gnocchi'].get_metric_measure(
                    metric=resource_dict['metrics']['disk.device.write.bytes'],
                    aggregation='rate:mean',
                    granularity=granularity,
                    start=start,
                    stop=stop
                )[-1][2]
                throughput = (disk_read + disk_write) / granularity
                return throughput, True
            except IndexError as ie:
                return 0.0, False
        
        def calc_iops():
            self.__LOGGER.debug(f"Calculating IOPs")
            if 'disk.device.read.requests' not in resource_dict['metrics']:
                raise EXCP.MissingResourceMetric('disk.device.read.requests')
            if 'disk.device.write.requests' not in resource_dict['metrics']:
                raise EXCP.MissingResourceMetric('disk.device.write.requests')
            try:
                disk_read = self.components['gnocchi'].get_metric_measure(
                    metric=resource_dict['metrics']['disk.device.read.requests'],
                    aggregation='rate:mean',
                    granularity=granularity,
                    start=start,
                    stop=stop
                )[-1][2]
                disk_write = self.components['gnocchi'].get_metric_measure(
                    metric=resource_dict['metrics']['disk.device.write.requests'],
                    aggregation='rate:mean',
                    granularity=granularity,
                    start=start,
                    stop=stop
                )[-1][2]
                iops = (disk_read + disk_write) / granularity
                return iops, True
            except IndexError as ie:
                return 0.0, False
        
        #-- GET RESOURCES
        #---- Loop over mapping and get metric ids for the resource type
        for r_type, id_field in OpenstackClient.SUPPORTED_METRIC_GROUPS['resource_map'][resource_type]['resource_ids'].items():
            self.__LOGGER.debug(f"Getting metrics for resource: {r_type}.{id_field}.{resource_id}")
            r_dict = self.components['gnocchi'].search_resource(
                query={"=":{id_field: resource_id}}
                resource_type=r_type,
                details=True
            )
            if 'metrics' not in r_dict:
                raise EXCP.MissingResourceMetric(f"{r_type}:{id_field}:{resource_id}")
            # Merge the metrics dicts
            resource_dict['metrics'] = {**resource_dict['metrics'], **r_dict['metrics']}

        #-- Call internal calculation functions to build metric_vals
        metric_vals = {}
        for metric_type in OpenstackClient.SUPPORTED_METRIC_GROUPS['resource_map'][resource_type]['metrics_list']:
            value, result = locals()[OpenstackClient.SUPPORTED_METRIC_GROUPS['metric_functions'][metric_type]]()
            metric_vals[metric_type] = value
            if not result:
                self.__LOGGER.warning(f"A metric returned an empty result when calculating {metric_type}")

        # BUILD RETURN DICT
        self.__LOGGER.debug(f"Building Return dictionary")
        # RETURN
        return metric_vals

    def get_user_info(self, user_cloud_id=None, user_cloud_name=None):
        """
        Get a user's cloud info
        """
        # EXIT CASES
        if 'keystone' not in self.components or not self.components['keystone']:
            raise EXCP.NoComponentFound('keystone')
        if not user_cloud_id and not user_cloud_name:
            raise EXCP.MissingRequiredArgs('user_cloud_id or user_cloud_name')

        # CLOUD OBJECT LOGIC
        if user_cloud_id:
            self.__LOGGER.debug(f"Fetching User info for {user_cloud_id}")
            user = self.components['keystone'].get_user_by_id(user_cloud_id)
        elif user_cloud_name:
            self.__LOGGER.debug(f"Fetching User info for {user_cloud_name}")
            user = self.components['keystone'].get_user(user_cloud_name)
        else:
            raise EXCP.InvalidArguments(user_cloud_id, user_cloud_name)

        # BUILD RETURN DICT
        self.__LOGGER.debug(f"Building Return dictionary")
        return_dict = {
            'id': user.id,
            'user': user._info
        }

        # RETURN
        return return_dict

    def get_project_info(self, project_cloud_id=None, project_cloud_name=None):
        """
        Get cloud info for the given account/project
        """
        # EXIT CASES
        if 'keystone' not in self.components or not self.components['keystone']:
            raise EXCP.NoComponentFound('keystone')
        if not project_cloud_id and not project_cloud_name:
            raise EXCP.MissingRequiredArgs('project_cloud_id or project_cloud_name')

        # CLOUD OBJECT LOGIC
        if project_cloud_id:
            self.__LOGGER.debug(f"Fetching info for {project_cloud_id}")
            project = self.components['keystone'].get_project_by_id(project_cloud_id)
        elif project_cloud_name:
            self.__LOGGER.debug(f"Fetching info for {project_cloud_name}")
            project = self.components['keystone'].get_project(project_cloud_name)
        else:
            raise EXCP.InvalidArguments(project_cloud_id, project_cloud_name)

        # BUILD RETURN DICT
        self.__LOGGER.debug(f"Building Return dictionary")
        return_dict = {
            'id': project.id,
            'project': project._info
        }

        # RETURN
        return return_dict

    def get_all_cm_users(self):
        """
        Get all Concertim Managed Users in the cloud.
        """
        # EXIT CASES
        self.__LOGGER.debug(f"Fetching all Concertim Managed Users")
        if 'keystone' not in self.components or not self.components['keystone']:
            raise EXCP.NoComponentFound('keystone')

        # CLOUD OBJECT LOGIC
        users_list = self.components['keystone'].get_users()
        return_dict = {
            'ids': [],
            'users': []
        }
        for user in users_list:
            if 'CM_' in user.name:
                return_dict['ids'].append(user.id)
                return_dict['users'].append(user._info)

        # BUILD RETURN DICT
        self.__LOGGER.debug(f"Building Return dictionary")
        # RETURN
        return return_dict

    def get_all_cm_projects(self):
        """
        Get all Concertim Managed Accounts/Projects in the cloud.
        """
        self.__LOGGER.debug(f"Fetching all Concertim Managed Projects")
        # EXIT CASES
        if 'keystone' not in self.components or not self.components['keystone']:
            raise EXCP.NoComponentFound('keystone')

        # CLOUD OBJECT LOGIC
        projects_list = self.components['keystone'].get_projects()
        return_dict = {
            'ids': [],
            'projects': []
        }
        for project in projects_list:
            if 'CM_' in project.name:
                return_dict['ids'].append(project.id)
                return_dict['projects'].append(project._info)

        # BUILD RETURN DICT
        self.__LOGGER.debug(f"Building Return dictionary")
        # RETURN
        return return_dict
    
    def get_cost(self, obj_type, obj_cloud_id, start, stop):
        """
        Get the cost data for a given Cloud Object

        Valid obj_types are :
            project
            instance
        """
        self.__LOGGER.debug(f"Fetching cost for {obj_type}.{obj_cloud_id} starting at {start} and ending at {stop}")
        # EXIT CASES
        if 'cloudkitty' not in self.components or not self.components['cloudkitty']:
            raise EXCP.NoComponentFound('cloudkitty')
        if obj_type not in OpenstackClient.SUPPORTED_COST_GROUPS:
            raise EXCP.InvalidArguments(f"obj_type:{obj_type}")
        if not start:
            raise EXCP.MissingRequiredArgs(f"start")
        if not stop:
            raise EXCP.MissingRequiredArgs(f"stop")
        if not obj_cloud_id:
            raise EXCP.MissingRequiredArgs(f"obj_cloud_id")

        # CLOUD OBJECT LOGIC
        result_dict = self.components['cloudkitty'].get_rating_summary(
            obj_id_field=OpenstackClient.SUPPORTED_COST_GROUPS[obj_type]['id_field'], 
            obj_id=obj_cloud_id, 
            begin=start, 
            end=stop
        )
        cost = 0
        for type_res in result_dict:
            cost = cost + float(result_dict[type_res])

        # BUILD RETURN DICT
        self.__LOGGER.debug(f"Building Return dictionary")
        return_dict = {
            'cost': cost
        }
        
        # RETURN
        return return_dict

    def get_keypair(self, key_cloud_id, user_cloud_id=None):
        """
        Get keypair info for a given User's/Account's keypair.
        """
        self.__LOGGER.debug(f"Fetching keypair {key_cloud_id}")
        # EXIT CASES
        if 'nova' not in self.components or not self.components['nova']:
            raise EXCP.NoComponentFound('nova')
        if not key_cloud_id:
            raise EXCP.MissingRequiredArgs('key_cloud_id')

        # CLOUD OBJECT LOGIC
        key_pair = self.components['nova'].get_keypair(
            keypair_name=key_cloud_id,
            user_id=user_cloud_id
        )

        # BUILD RETURN DICT
        self.__LOGGER.debug(f"Building Return dictionary")
        return_dict = {
            'id': key_cloud_id,
            'key_pair': key_pair._info
        }
        
        # RETURN
        return return_dict

    def get_all_keypairs(self, user_cloud_id=None):
        """
        Get all keypairs for a user/account
        """
        self.__LOGGER.debug(f"Fetching all keypairs")
        # EXIT CASES
        if 'nova' not in self.components or not self.components['nova']:
            raise EXCP.NoComponentFound('nova')

        # CLOUD OBJECT LOGIC
        key_pairs = self.components['nova'].list_keypairs(
            user_id=user_cloud_id
        )

        # BUILD RETURN DICT
        self.__LOGGER.debug(f"Building Return dictionary")
        return_dict = {
            'ids': [],
            'key_pairs': {}
        }
        for kp in key_pairs:
            return_dict['ids'].append(kp.id)
            return_dict['key_pairs'][kp.id] = kp._info

        # RETURN
        return return_dict

    def get_server_info(self, server_cloud_id):
        """
        Get details for a given server/instance.
        """
        self.__LOGGER.debug(f"Fetching info for Server {server_cloud_id}")
        # EXIT CASES
        if 'nova' not in self.components or not self.components['nova']:
            raise EXCP.NoComponentFound('nova')
        if not server_cloud_id:
            raise EXCP.MissingRequiredArgs('server_cloud_id')

        # CLOUD OBJECT LOGIC
        server = self.components['nova'].get_server(
            instance_id=server_cloud_id
        )

        # BUILD RETURN DICT
        self.__LOGGER.debug(f"Building Return dictionary")
        return_dict = {
            'id': server.id,
            'server': server._info
        }

        # RETURN
        return return_dict
    
    def get_cluster_info(self, cluster_cloud_id):
        """
        Get details for a given cluster.
        """
        self.__LOGGER.debug(f"Fetching all info for Cluster {cluster_cloud_id}")
        # EXIT CASES
        if 'heat' not in self.components or not self.components['heat']:
            raise EXCP.NoComponentFound('heat')
        if 'nova' not in self.components or not self.components['nova']:
            raise EXCP.NoComponentFound('nova')
        if not cluster_cloud_id:
            raise EXCP.MissingRequiredArgs('cluster_cloud_id')

        # CLOUD OBJECT LOGIC
        #-- cluster from heat
        self.__LOGGER.debug(f"Getting base Cluster info")
        cluster = self.components['heat'].get_stack(
            stack_id=cluster_cloud_id
        )
        #-- cluster resources by resource type
        resources = {
            'servers': {},
            'volumes': {},
            'networks': {},
            'other': {}
        }
        self.__LOGGER.debug(f"Getting Cluster resource data")
        resources_list = self.components['heat'].list_stack_resources(
            stack_id=cluster_cloud_id
        )
        for resource in resources:
            res_type = resource.resource_type.split("::")
            #---- res_types could be (not all listed, just examples)
            #------ OS::Cinder::VolumeAttachment, OS::Cinder::Volume, 
            #------ OS::Nova::Server, OS::Nova::ServerGroup,
            #------ OS::Neutron::Port, OS::Neutron::FloatingIP, OS::Neutron::SecurityGroup, OS::Neutron::RouterInterface, OS::Neutron::Router, OS::Neutron::Net, OS::Neutron::Subnet
            if res_type[1] == 'Nova':
                if res_type[2] != 'ServerGroup':
                    resources['servers'][resource.physical_resource_id] = resource._info
                else:
                    server_group = self.components['nova'].get_server_group(
                        group_id=resource.physical_resource_id
                    )
                    resources['servers'][resource.physical_resource_id] = server_group._info
            elif res_type[1] == 'Cinder':
                resources['volumes'][resource.physical_resource_id] = resource._info
            elif res_type[1] == 'Neutron':
                resources['networks'][resource.physical_resource_id] = resource._info
            else:
                resources['other'][resource.physical_resource_id] = resource._info
        #-- output from heat stack
        self.__LOGGER.debug(f"Getting Cluster output data")
        output = []
        outputs_list = self.components['heat'].list_stack_output(
            stack_id=cluster_cloud_id
        )
        for output_dict in outputs_list:
            details = self.components['heat'].show_output(
                stack_id=cluster_cloud_id,
                output_key=output_dict['output_key']
            )
            output.append(tuple(output_dict['output_key'], details))
        
        # BUILD RETURN DICT
        self.__LOGGER.debug(f"Building Return dictionary")
        return_dict = {
            'id': cluster_cloud_id,
            'cluster_info': cluster._info,
            'cluster_components': resources,
            'cluster_outputs': output
        }

        # RETURN
        return return_dict

    def get_all_servers(self, project_cloud_id):
        """
        Get all servers for a given Project/Account.
        """
        # EXIT CASES
        self.__LOGGER.debug(f"Fetching all Servers info for project {project_cloud_id}")
        if 'nova' not in self.components or not self.components['nova']:
            raise EXCP.NoComponentFound('nova')
        if not project_cloud_id:
            raise EXCP.MissingRequiredArgs('project_cloud_id')

        # CLOUD OBJECT LOGIC
        servers = self.components['nova'].list_servers(
            project_id=project_cloud_id
        )

        # BUILD RETURN DICT
        self.__LOGGER.debug(f"Building Return dictionary")
        return_dict = {
            'ids': [],
            'servers': {}
        }
        for inst in servers:
            return_dict['ids'].append(inst.id)
            return_dict['servers'][inst.id] = inst._info

        # RETURN
        return return_dict

    def get_all_clusters(self, project_cloud_id):
        """
        Get all clusters for a given Project/Account.
        """
        self.__LOGGER.debug(f"Fetching all Clusters info for project {project_cloud_id}")
        # EXIT CASES
        if 'heat' not in self.components or not self.components['heat']:
            raise EXCP.NoComponentFound('heat')
        if 'nova' not in self.components or not self.components['nova']:
            raise EXCP.NoComponentFound('nova')
        if not project_cloud_id:
            raise EXCP.MissingRequiredArgs('project_cloud_id')

        # CLOUD OBJECT LOGIC
        stack_id_list = []
        #-- List all stacks
        all_stacks = self.components['heat'].list_stacks()
        self.__LOGGER.debug(f"Filtering stacks to only project={project_cloud_id}")
        #-- Use only stacks that match the project
        for stack in all_stacks:
            if stack.project == project_cloud_id:
                stack_id_list.append(stack.id)
        #-- Get stack info for each stack
        # BUILD RETURN DICT
        self.__LOGGER.debug(f"Building Return dictionary")
        return_dict = {
            'ids': [],
            'clusters': {}
        }
        for stack_id in stack_id_list:
            return_dict['ids'].append(stack_id)
            return_dict['clusters'][stack_id] = self.get_cluster_info(
                cluster_cloud_id=stack_id
            )

        # RETURN
        return return_dict

    def get_flavors(self):
        """
        Get all available flavors for servers in the Cloud.
        """
        self.__LOGGER.debug(f"Fetching all Flavors available")
        # EXIT CASES
        if 'nova' not in self.components or not self.components['nova']:
            raise EXCP.NoComponentFound('nova')
        
        # CLOUD OBJECT LOGIC
        flavors = self.components['nova'].list_flavors()

        # BUILD RETURN DICT
        self.__LOGGER.debug(f"Building Return dictionary")
        return_dict = {
            'ids': []
            'flavors': {}
        }
        for flavor in flavors:
            return_dict['ids'].append(flavor.id)
            return_dict['flavors'][flavor.id] = flavor._info

        # RETURN
        return return_dict

    def update_server_status(self, server_cloud_id, action):
        """
        Change status of a server/instance (active, stopped, etc.)
        """
        self.__LOGGER.debug(f"Updating Server {server_cloud_id} with action {action}")
        # EXIT CASES
        if 'nova' not in self.components or not self.components['nova']:
            raise EXCP.NoComponentFound('nova')
        if not server_cloud_id:
            raise EXCP.MissingRequiredArgs('server_cloud_id')
        if not action:
            raise EXCP.MissingRequiredArgs('action')
        if action not in OpenstackClient.VALID_SERVER_ACTIONS:
            raise EXCP.InvalidArguments(f"action:{action}")

        # CLOUD OBJECT LOGIC
        attempt = getattr(self.components['nova'], OpenstackClient.VALID_SERVER_ACTIONS[action])(
            instance_id=server_cloud_id
        )

        # BUILD RETURN DICT
        self.__LOGGER.debug(f"Building Return dictionary")
        return_dict = {
            'submitted': True,
            'request_ids': attempt.request_ids,
            'attempt': attempt._info
        }

        # RETURN
        return return_dict

    def update_cluster_status(self, cluster_cloud_id, action):
        """
        Change status of a cluster (active, stopped, etc.)
        """
        self.__LOGGER.debug(f"Updating Cluster {cluster_cloud_id} with action {action}")
        if 'heat' not in self.components or not self.components['heat']:
            raise EXCP.NoComponentFound('heat')
        if not cluster_cloud_id:
            raise EXCP.MissingRequiredArgs('cluster_cloud_id')
        if not action:
            raise EXCP.MissingRequiredArgs('action')
        if action not in OpenstackClient.VALID_CLUSTER_ACTIONS:
            raise EXCP.InvalidArguments(f"action:{action}")

        # CLOUD OBJECT LOGIC
        #-- This call returns True because heat itself returns nothing
        attempt = getattr(self.components['heat'], OpenstackClient.VALID_CLUSTER_ACTIONS[action])(
            stack_id=cluster_cloud_id
        )

        # BUILD RETURN DICT
        self.__LOGGER.debug(f"Building Return dictionary")
        return_dict = {
            'submitted': True,
            'request_ids': [],
            'attempt': {}
        }

        # RETURN
        return return_dict

    def update_user_info(self, user_cloud_id, new_email=None, new_password=None):
        """
        Update a user's info (email, password, etc)
        """
        # EXIT CASES
        self.__LOGGER.debug(f"Updating User {user_cloud_id} info")
        if 'keystone' not in self.components or not self.components['keystone']:
            raise EXCP.NoComponentFound('keystone')
        if not user_cloud_id:
            raise EXCP.MissingRequiredArgs('user_cloud_id')
        if not new_email and not new_password:
            raise EXCP.MissingRequiredArgs('new_email or new_password')

        # CLOUD OBJECT LOGIC
        attempt = self.components['keystone'].update_user(
            user_id=user_cloud_id, 
            email=new_email,
            password=new_password
        )
        changed = []
        if new_email:
            changed.append('email')
        if new_password:
            changed.append('password')

        # BUILD RETURN DICT
        self.__LOGGER.debug(f"Building Return dictionary")
        return_dict = {
            'success': True,
            'changed': changed
        }

        # RETURN
        return return_dict

    def update_project_info(self, project_cloud_id, new_name=None, new_description=None):
        """
        Update an account's/project's info.
        """
        self.__LOGGER.debug(f"Updating Project {project_cloud_id} info")
        # EXIT CASES
        if 'keystone' not in self.components or not self.components['keystone']:
            raise EXCP.NoComponentFound('keystone')
        if not project_cloud_id:
            raise EXCP.MissingRequiredArgs('project_cloud_id')
        if not new_name and not new_description:
            raise EXCP.MissingRequiredArgs('new_name or new_description')

        # CLOUD OBJECT LOGIC
        attempt = self.components['keystone'].update_project(
            project_id=project_cloud_id, 
            name=new_name,
            description=new_description
        )
        changed = []
        if new_name:
            changed.append('name')
        if new_description:
            changed.append('description')

        # BUILD RETURN DICT
        self.__LOGGER.debug(f"Building Return dictionary")
        return_dict = {
            'success': True,
            'changed': changed
        }

        # RETURN
        return return_dict

    def delete_user(self, user_cloud_id):
        """
        Remove a User from the cloud.
        """
        self.__LOGGER.debug(f"Deleting User {user_cloud_id}")
        # EXIT CASES
        if 'keystone' not in self.components or not self.components['keystone']:
            raise EXCP.NoComponentFound('keystone')
        if not user_cloud_id:
            raise EXCP.MissingRequiredArgs('user_cloud_id')

        # CLOUD OBJECT LOGIC
        attempt = self.components['keystone'].delete_user(
            user_id=user_cloud_id
        )

        # BUILD RETURN DICT
        self.__LOGGER.debug(f"Building Return dictionary")
        return_dict = {
            'success': True
        }

        # RETURN
        return return_dict
    
    def delete_project(self, project_cloud_id):
        """
        Remove an account/project from the cloud.
        """
        self.__LOGGER.debug(f"Deleting Project {project_cloud_id}")
        # EXIT CASES
        if 'keystone' not in self.components or not self.components['keystone']:
            raise EXCP.NoComponentFound('keystone')
        if not project_cloud_id:
            raise EXCP.MissingRequiredArgs('project_cloud_id')

        # CLOUD OBJECT LOGIC
        attempt = self.components['keystone'].delete_project(
            project_id=project_cloud_id
        )

        # BUILD RETURN DICT
        self.__LOGGER.debug(f"Building Return dictionary")
        return_dict = {
            'success': True
        }

        # RETURN
        return return_dict
    
    def delete_keypair(self, key_cloud_id):
        """
        Delete a KeyPair from a user/account.
        """
        self.__LOGGER.debug(f"Deleting Keypair {key_cloud_id}")
        # EXIT CASES
        if 'nova' not in self.components or not self.components['nova']:
            raise EXCP.NoComponentFound('nova')
        if not key_cloud_id:
            raise EXCP.MissingRequiredArgs('key_cloud_id')

        # CLOUD OBJECT LOGIC
        attempt = self.components['nova'].delete_keypair(
            keypair=key_cloud_id
        )

        # BUILD RETURN DICT
        self.__LOGGER.debug(f"Building Return dictionary")
        return_dict = {
            'success': True
        }

        # RETURN
        return return_dict

    def delete_cluster(self, cluster_cloud_id):
        """
        Destory a given cluster.
        """
        # EXIT CASES
        if 'heat' not in self.components or not self.components['heat']:
            raise EXCP.NoComponentFound('heat')
        if not cluster_cloud_id:
            raise EXCP.MissingRequiredArgs('cluster_cloud_id')

        # CLOUD OBJECT LOGIC
        attempt = self.update_cluster_status(
            cluster_cloud_id=cluster_cloud_id,
            action='destroy'
        )

        # BUILD RETURN DICT
        # RETURN
        return attempt

    def delete_server(self, server_cloud_id):
        """
        Destroy a given server.
        """
        # EXIT CASES
        if 'heat' not in self.components or not self.components['heat']:
            raise EXCP.NoComponentFound('heat')
        if not server_cloud_id:
            raise EXCP.MissingRequiredArgs('server_cloud_id')

        # CLOUD OBJECT LOGIC
        attempt = self.update_server_status(
            server_cloud_id=server_cloud_id,
            action='destroy'
        )

        # BUILD RETURN DICT
        # RETURN
        return attempt


    ####################################
    # CLIENT OBJECT REQUIRED FUNCTIONS #
    ####################################
    def get_connection_obj(self):
        """
        Function to create a connection to the application

        Returns the session object based on the openstack configuration in the object
        """
        return OpenStackAuth.get_session(self.openstack_config)

    def disconnect(self):
        """
        Function for disconnecting all streams before garbage collection.
        """
        self.__LOGGER.info("Disconnecting Openstack Client and Components")
        self.openstack_config = None
        for name, comp in self.components.items():
            comp.disconnect()
        self.components = None


    ############################
    # OPENSTACK CLIENT HELPERS #
    ############################

    # Private method for fetching required openstack objects from given component
    # valid component_names (string): keystone, nova, gnocchi, heat, cloudkitty
    # obj_names (dict{string:list}) : {'obj type' : ['name1', 'name2']} -> {'user': ['admin', 'member']}
    def __populate_required_objs(self, component_name, obj_names):
        self.__LOGGER.debug(f"Fetching required Openstack Objects for {component_name}")
        if component_name not in self.components or not self.components[component_name]:
            raise EXCP.NoComponentFound(component_name)

        found_objs = {}
        missing_objs = []
        for obj_type in obj_names:
            found_objs[obj_type] = {}
            for obj_name in obj_names[obj_type]:
                try:
                    found_objs[obj_type][obj_name] = getattr(self.components[component_name], f"get_{obj_type}")(obj_name).id
                except AttributeError as e:
                    self.__LOGGER.error(f"Failed fetching {obj_type}.{obj_name} - no function 'get_{obj_type}' found for {component_name} component")
                    self.__LOGGER.error(f"{type(e).__name__} - {e}")
                    raise e
                if not found_objs[obj_type][obj_name]:
                    missing_objs.append(f"{component_name}.{obj_type}.{obj_name}")
        
        if missing_objs:
            self.__LOGGER.error(f"Could not find required object(s) {missing_objs} - please have Administrator create in Openstack")
            raise EXCP.MissingCloudObject(f"{missing_objs}")

        return found_objs
