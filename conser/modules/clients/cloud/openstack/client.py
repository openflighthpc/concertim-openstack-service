# Local Imports
from conser.utils.service_logger import create_logger
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
    # Granularity set to 15 to match Concertim MRD polling rate
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
                'units': {
                    'cpu_load': '%',
                    'ram_usage': '%',
                    'network_usage': 'B/s',
                    'throughput': 'B/s',
                    'iops': 'OPS/s',
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
        self.req_keystone_objs = None 
        if req_keystone_objs:
            self.req_keystone_objs = self.__populate_required_objs('keystone', self.required_ks_objs)
        self.CONCERTIM_STATE_MAP = {
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

    ##########################################
    # CLOUD CLIENT OBJECT REQUIRED FUNCTIONS #
    ##########################################
    def create_cm_project(self, name, primary_user_cloud_id):
        """
        Create a new Concertim Managaed account/project

        returns a dict in the format
        return_dict = {
            'id': 
            'name': 
            'description': 
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
            'name': new_project.name,
            'description': new_project.description
        }

        # RETURN
        return return_dict
    
    def create_cm_user(self, username, password, email):
        """
        Create a new Concertim Managed user.

        Returns a dict in the format
        return_dict = {
            'id':
            'name':
            'email': 
            'description':
        }
        """
        self.__LOGGER.debug(f"Creating new Concertim-managed User for '{username}'")
        # EXIT CASES
        if 'keystone' not in self.components or not self.components['keystone']:
            raise EXCP.NoComponentFound('keystone')
        if not username or not password or not email:
            raise EXCP.MissingRequiredArgs('username', 'email', 'password')

        # CLOUD OBJECT LOGIC
        new_user = self.components['keystone'].create_user(username, password, 'default', email=email, desc="Concertim Managed User")
        self.__LOGGER.debug(f"New Concertim-managed User created successfully - '{new_user}'")

        # BUILD RETURN DICT
        return_dict = {
            'id': new_user.id,
            'name': new_user.name,
            'email': new_user.email,
            'description': new_user.description
        }

        # RETURN
        return return_dict

    def create_keypair(self, name, imported_pub_key=None, key_type='ssh', user_cloud_id=None):
        """
        Create a new KeyPair for a given User/Account

        Returns a dict in the format
        return_dict = {
            'private_key': 
            'public_key': 
            'name': 
            'id': 
        }
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
            'private_key': new_keypair.private_key,
            'public_key': new_keypair.public_key,
            'name': new_keypair.name,
            'id': new_keypair.id
        }

        # RETURN
        return return_dict

    def get_metrics(self, resource_type, resource_id, start, stop):
        """
        Get all metrics for a resource that are available in OpenstackClient.SUPPORTED_METRIC_GROUPS

        resource_id : the ID of the resource in the cloud
        resource_type : the string type name of the resource in the cloud
                      Valid resource_type options:
                        server
                        #(not implemeted) volume
                        #(not implemeted) network
        start: the datetime of when to start the metric accumulation
        stop: the datetime of when to stop the metric accumulation
        
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
            metric_vals[metric_type] = {
                'value': value, 
                'unit': OpenstackClient.SUPPORTED_METRIC_GROUPS['resource_map'][resource_type]['units'][metric_type]
            }
            if not result:
                self.__LOGGER.warning(f"A metric returned an empty result when calculating {metric_type}")

        # BUILD RETURN DICT
        self.__LOGGER.debug(f"Building Return dictionary")
        # RETURN
        return metric_vals

    def get_user_info(self, user_cloud_id=None):
        """
        Get a user's cloud info

        returns a dict in the format
        return_dict = {
            'id': 
            'name': 
            'email': 
            'description': 
            'projects': {
                'team_member': []
                'team_admin': []
            }
        }
        """
        # EXIT CASES
        if 'keystone' not in self.components or not self.components['keystone']:
            raise EXCP.NoComponentFound('keystone')
        if not user_cloud_id:
            raise EXCP.MissingRequiredArgs('user_cloud_id')
        if not self.req_keystone_objs['role']['admin'] 
            or not self.req_keystone_objs['role']['member']:
            raise EXCP.MissingRequiredCloudObject(self.req_keystone_objs)

        # CLOUD OBJECT LOGIC
        self.__LOGGER.debug(f"Fetching User info for {user_cloud_id}")
        user = self.components['keystone'].get_user(user_cloud_id)
        user_ras = self.components['keystone'].get_user_assignments(user_cloud_id)
        user_projects = {
            'team_member': [],
            'team_admin': []
        }
        for ra in user_ras:
            if ra._info['role']['id'] == self.req_keystone_objs['role']['admin']:
                user_projects['team_admin'].append(ra._info['scope']['project']['id'])
            if ra._info['role']['id'] == self.req_keystone_objs['role']['member']:
                user_projects['team_member'].append(ra._info['scope']['project']['id'])

        # BUILD RETURN DICT
        self.__LOGGER.debug(f"Building Return dictionary")
        return_dict = {
            'id': user.id,
            'name': user.name,
            'email': user.email,
            'description': user.description
            'user_projects': user_projects
        }

        # RETURN
        return return_dict

    def get_project_info(self, project_cloud_id=None):
        """
        Get cloud info for the given account/project

        returns a dict in the format
        return_dict = {
            'id': 
            'name': 
            'description': 
            'users': {
                'team_members': []
                'team_admins': []
            }
        }
        """
        # EXIT CASES
        if 'keystone' not in self.components or not self.components['keystone']:
            raise EXCP.NoComponentFound('keystone')
        if not self.req_keystone_objs['role']['admin'] 
            or not self.req_keystone_objs['role']['member']:
            raise EXCP.MissingRequiredCloudObject(self.req_keystone_objs)
        if not project_cloud_id:
            raise EXCP.MissingRequiredArgs('project_cloud_id')

        # CLOUD OBJECT LOGIC
        self.__LOGGER.debug(f"Fetching info for {project_cloud_name}")
        project = self.components['keystone'].get_project(project_cloud_id)
        project_ras = self.components['keystone'].get_project_assignments(user_cloud_id)
        project_users = {
            'team_members': [],
            'team_admins': []
        }
        for ra in project_ras:
            if ra._info['role']['id'] == self.req_keystone_objs['role']['admin']:
                project_users['team_admins'].append(ra._info['user']['id'])
            if ra._info['role']['id'] == self.req_keystone_objs['role']['member']:
                project_users['team_members'].append(ra._info['user']['id'])

        # BUILD RETURN DICT
        self.__LOGGER.debug(f"Building Return dictionary")
        return_dict = {
            'id': project.id,
            'name': project.name,
            'description': project.description,
            'users': project_users
        }

        # RETURN
        return return_dict

    def get_all_cm_users(self):
        """
        Get all Concertim Managed Users IDs from the cloud.

        returns a dict in the format
        return_dict = {
            'users': [ids]
        }
        """
        # EXIT CASES
        self.__LOGGER.debug(f"Fetching all Concertim Managed Users")
        if 'keystone' not in self.components or not self.components['keystone']:
            raise EXCP.NoComponentFound('keystone')

        # CLOUD OBJECT LOGIC
        users_list = self.components['keystone'].get_users()

        # BUILD RETURN DICT
        self.__LOGGER.debug(f"Building Return dictionary")
        return_dict = {
            'users': [user.id for user in users_list if 'CM_' in user.name]
        }
        # RETURN
        return return_dict

    def get_all_cm_projects(self):
        """
        Get all Concertim Managed Accounts/Projects IDs from the cloud.

        returns a dict in the format
        return_dict = {
            'projects': [ids]
        }
        """
        self.__LOGGER.debug(f"Fetching all Concertim Managed Projects")
        # EXIT CASES
        if 'keystone' not in self.components or not self.components['keystone']:
            raise EXCP.NoComponentFound('keystone')

        # CLOUD OBJECT LOGIC
        projects_list = self.components['keystone'].get_projects()

        # BUILD RETURN DICT
        self.__LOGGER.debug(f"Building Return dictionary")
        return_dict = {
            'projects': [project.id for project in projects_list if 'CM_' in project.name]
        }
        # RETURN
        return return_dict
    
    def get_cost(self, obj_type, obj_cloud_id, start, stop):
        """
        Get the cost data for a given Cloud Object

        Valid obj_types are :
            project
            instance

        returns a dict in the format
        return_dict = {
            'cost': 
        }
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

        returns a dict in the format
        return_dict = {
            'id': 
            'public_key': 
            'name': 
        }
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
            'id': key_pair.id,
            'public_key': key_pair.public_key,
            'name': key_pair.name
        }
        
        # RETURN
        return return_dict

    def get_all_keypairs(self, user_cloud_id=None):
        """
        Get all keypairs for a user/account

        returns a dict in the format
        return_dict = {
            key_pairs: {
                <key_id>: {
                    'id': 
                    'public_key': 
                    'name': 
                }
            }
        }
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
            'key_pairs': {}
        }
        for kp in key_pairs:
            return_dict['key_pairs'][kp.id]['id'] = kp.id
            return_dict['key_pairs'][kp.id]['name'] = kp.name
            return_dict['key_pairs'][kp.id]['public_key'] = kp.public_key

        # RETURN
        return return_dict

    def get_server_info(self, server_cloud_id):
        """
        Get details for a given server/instance.

        return_dict = {
            'id': 
            'name':
            'status':
            'project_cloud_id':
            'template_cloud_id':
            'public_ips': []
            'private_ips': []
            'ssh_key_name':
            'volumes': []
            'network_interfaces': []
        }
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
        pub_ips = []
        pri_ips = []
        vols = []
        for net, ad_list in server._info['addresses'].items():
            for address in ad_list:
                if 'OS-EXT-IPS:type' in address and address['OS-EXT-IPS:type'] == 'fixed':
                    pri_ips.append(address['addr'])
                if 'OS-EXT-IPS:type' in address and address['OS-EXT-IPS:type'] == 'floating':
                    pub_ips.append(address['addr'])
        for vol in server._info['os-extended-volumes:volumes_attached']:
            vols.append(vol['id'])

        # BUILD RETURN DICT
        self.__LOGGER.debug(f"Building Return dictionary")
        return_dict = {
            'id': server.id,
            'name': server.name,
            'status': server._info['OS-EXT-STS:vm_state'],
            'project_cloud_id': server.tenant_id,
            'template_cloud_id': server._info['flavor']['id'],
            'public_ips': pub_ips
            'private_ips': pri_ips
            'ssh_key_name': server.key_name,
            'volumes': vols,
            'network_interfaces': server._info['addresses'].keys()
        }

        # RETURN
        return return_dict
    
    def get_cluster_info(self, cluster_cloud_id):
        """
        Get details for a given cluster.

        return_dict = {
            'id': 
            'name': 
            'base_name':
            'project_cloud_id': 
            'description': 
            'user_cloud_name': 
            'status': 
            'status_reason': 
            'cluster_resources': {
                'servers': {
                    <resource_id>: {
                        'id':
                        'name':
                    }
                }
                'volumes': {}
                'networks': {}
                'other': {}
            }
            'cluster_outputs': [(output_key,output_details)]
        }
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
                    resources['servers'][resource.physical_resource_id] = {
                        'id': resource._info['physical_resource_id'],
                        'name': resource._info['resource_name']
                    }
                else:
                    server_group = self.components['nova'].get_server_group(
                        group_id=resource.physical_resource_id
                    )
                    for inst_id in server_group._info['members']:
                        resources['servers'][inst_id] = {
                            'id': inst_id,
                            'name': None
                        }
            elif res_type[1] == 'Cinder':
                resources['volumes'][resource.physical_resource_id] = {
                    'id': resource._info['physical_resource_id'],
                    'name': resource._info['resource_name']
                }
            elif res_type[1] == 'Neutron':
                resources['networks'][resource.physical_resource_id] = {
                    'id': resource._info['physical_resource_id'],
                    'name': resource._info['resource_name']
                }
            else:
                resources['other'][resource.physical_resource_id] = {
                    'id': resource._info['physical_resource_id'],
                    'name': resource._info['resource_name']
                }
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
            'name': cluster._info['stack_name'],
            'base_name': cluster._info['stack_name'].split('--')[0],
            'project_cloud_id': cluster._info['parameters']['OS::project_id'],
            'description': cluster._info['description'],
            'user_cloud_name': cluster._info['stack_owner'],
            'status': cluster._info['stack_status'],
            'status_reason': cluster._info['stack_status_reason'],
            'cluster_resources': resources,
            'cluster_outputs': output
        }

        # RETURN
        return return_dict

    def get_all_servers(self, project_cloud_id=None):
        """
        Get all servers - optionally for a given Project/Account.

        return_dict = {
            'servers': {
                <server_id>: {}
            }
        }
        """
        msg = "Fetching all Servers info"
        if project_cloud_id:
            msg += f" for project {project_cloud_id}"
        self.__LOGGER.debug(msg)
        # EXIT CASES
        if 'nova' not in self.components or not self.components['nova']:
            raise EXCP.NoComponentFound('nova')

        # CLOUD OBJECT LOGIC
        servers = self.components['nova'].list_servers(
            project_id=project_cloud_id
        )

        # BUILD RETURN DICT
        self.__LOGGER.debug(f"Building Return dictionary")
        return_dict = {
            'servers': {}
        }
        for inst in servers:
            # Format each Server object
            pub_ips = []
            pri_ips = []
            vols = []
            for net, ad_list in inst._info['addresses'].items():
                for address in ad_list:
                    if 'OS-EXT-IPS:type' in address and address['OS-EXT-IPS:type'] == 'fixed':
                        pri_ips.append(address['addr'])
                    if 'OS-EXT-IPS:type' in address and address['OS-EXT-IPS:type'] == 'floating':
                        pub_ips.append(address['addr'])
            for vol in inst._info['os-extended-volumes:volumes_attached']:
                vols.append(vol['id'])

            # BUILD RETURN DICT
            self.__LOGGER.debug(f"Building Return dictionary")
            server_dict = {
                'id': inst.id,
                'name': inst.name,
                'status': inst._info['OS-EXT-STS:vm_state'],
                'project_cloud_id': inst.tenant_id,
                'template_cloud_id': inst._info['flavor']['id'],
                'public_ips': pub_ips
                'private_ips': pri_ips
                'ssh_key_name': inst.key_name,
                'volumes': vols,
                'network_interfaces': server._info['addresses'].keys()
            }
            return_dict['servers'][inst.id] = server_dict

        # RETURN
        return return_dict

    def get_all_clusters(self, project_cloud_id=None):
        """
        Get all clusters - optionally for a given Project/Account.

        return_dict = {
            'clusters': {
                <cluster_id>: {}
            }
        }
        """
        msg = "Fetching all Clusters info"
        if project_cloud_id:
            msg += f" for project {project_cloud_id}"
        self.__LOGGER.debug(msg)
        # EXIT CASES
        if 'heat' not in self.components or not self.components['heat']:
            raise EXCP.NoComponentFound('heat')
        if 'nova' not in self.components or not self.components['nova']:
            raise EXCP.NoComponentFound('nova')

        # CLOUD OBJECT LOGIC
        #-- List all stacks
        all_stacks = self.components['heat'].list_stacks()
        if project_cloud_id:
            self.__LOGGER.debug(f"Filtering stacks to only project={project_cloud_id}")
            #-- Use only stacks that match the project
            stack_list = [stack for stack in all_stacks if stack.project == project_cloud_id]
        else:
            stack_list = all_stacks
        #-- Get stack info for each stack
        # BUILD RETURN DICT
        self.__LOGGER.debug(f"Building Return dictionary")
        return_dict = {
            'clusters': {}
        }
        for stack in stack_list:
            return_dict['clusters'][stack.id] = self.get_cluster_info(
                cluster_cloud_id=stack.id
            )

        # RETURN
        return return_dict

    def get_all_flavors(self):
        """
        Get all available flavors for servers in the Cloud.

        return_dict = {
            'flavors': {
                <flavor_id>: {
                    'id':
                    'name':
                    'ram': 
                    'disk': 
                    'vcpus': 
                }
            }
        }
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
            'flavors': {}
        }
        for flavor in flavors:
            return_dict['flavors'][flavor.id] = {
                'id': flavor._info['id'],
                'name': flavor._info['name'],
                'ram': flavor._info['ram'],
                'disk': flavor._info['disk'],
                'vcpus': flavor._info['vcpus'],
            }

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

    def start_message_queue(self):
        """
        Start listening to the message queue and intercepting messages
        """
        if 'mq' not in self.components or not self.components['mq']:
            raise EXCP.NoComponentFound('mq')

        self.components['mq'].start_listening()


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
