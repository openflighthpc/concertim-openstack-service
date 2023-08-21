# Local Imports
from con_opstk.utils.service_logger import create_logger
from con_opstk.openstack.opstk_auth import OpenStackAuth
from con_opstk.openstack.exceptions import UnknownOpenstackHandler, NoHandlerFound, MissingOpenstackObject
# Py Packages
import sys
import novaclient.exceptions
import heatclient.exc

class OpenstackService(object):
    _REQUIRED_KS_OBJS = {
            'domain': [],
            'role': ['admin', 'member', 'watcher'],
            'user': ['admin', 'concertim'],
            'project': []
        }

    def __init__(self, config_obj, log_file, client_list=[], required_ks_objs={}):
        self._CONFIG = config_obj
        self._LOG_FILE = log_file
        self.__LOGGER = create_logger(__name__, self._LOG_FILE, self._CONFIG['log_level'])
        self.__OPSTK_AUTH = OpenStackAuth(self._CONFIG['openstack'])
        self._handlers_key_map = {}
        self.handlers = {client:self.__create_handler(client) for client in client_list}
        self.req_keystone_objs = required_ks_objs
        if 'keystone' in self._handlers_key_map:
            self.req_keystone_objs = self.__populate_required_objs('keystone', required_ks_objs) if required_ks_objs else self.__populate_required_objs('keystone', OpenstackService._REQUIRED_KS_OBJS)
    
    # Private method to return correct ClientHandler object with instance's openstack auth data
    def __create_handler(self, client_name, auth=None):
        self.__LOGGER.debug(f"Creating '{client_name}' handler for corresponding Openstack Client")
        try:
            sess = auth.get_session() if auth is not None else self.__OPSTK_AUTH.get_session()
            if client_name.lower() in ["keystone", "keystoneclient", "keystone_client", "keystonehandler", "keystone_handler"]:
                from con_opstk.openstack.client_handlers.keystone import KeystoneHandler
                kh = KeystoneHandler(sess, self._LOG_FILE, self._CONFIG['log_level'])
                self.__LOGGER.debug(f"Successfully added KeystoneHandler to OpenstackService")
                self._handlers_key_map['keystone'] = client_name
                return kh
            elif client_name.lower() in ["nova", "novaclient", "nova_client", "novahandler", "nova_handler"]:
                from con_opstk.openstack.client_handlers.nova import NovaHandler
                nh = NovaHandler(sess, self._LOG_FILE, self._CONFIG['log_level'])
                self.__LOGGER.debug(f"Successfully added NovaHandler to OpenstackService")
                self._handlers_key_map['nova'] = client_name
                return nh
            elif client_name.lower() in ["heat", "heatclient", "heat_client", "heathandler", "heat_handler"]:
                from con_opstk.openstack.client_handlers.heat import HeatHandler
                hh = HeatHandler(sess, self._LOG_FILE, self._CONFIG['log_level'])
                self.__LOGGER.debug(f"Successfully added HeatHandler to OpenstackService")
                self._handlers_key_map['heat'] = client_name
                return hh
            elif client_name.lower() in ["gnocchi", "gnocchiclient", "gnocchi_client", "gnocchihandler", "gnocchi_handler"]:
                from con_opstk.openstack.client_handlers.gnocchi import GnocchiHandler
                gh = GnocchiHandler(sess, self._LOG_FILE, self._CONFIG['log_level'])
                self.__LOGGER.debug(f"Successfully added GnocchiHandler to OpenstackService")
                self._handlers_key_map['gnocchi'] = client_name
                return gh
            else:
                self.__LOGGER.error(f"Attempted to add an unknown handler : '{client_name}'")
                raise UnknownOpenstackHandler(f"Unknown Handler : {client_name}")
        except Exception as e:
            self.__LOGGER.error(f"{type(e).__name__} - {e} - {sys.exc_info()[2].tb_frame.f_code.co_filename} - {sys.exc_info()[2].tb_lineno}")
            raise e

    # Method for adding new handlers to existing OpenstackService - returns client handler if successful
    # OPTIONAL : pass a different OpenStackAuth object, otherwise instance native auth is used
    def add_client_handler(self, handler_name, auth=None):
        self.__LOGGER.debug(f"Adding new handler '{handler_name}'")
        try:
            self.handlers[handler_name] = self.__create_handler(handler_name, auth)
            return self.handlers[handler_name]
        except MissingOpenstackObject as e:
            self.__LOGGER.error(f"{type(e).__name__} - Please create missing objects - {e}")
            raise SystemExit(e)
        except Exception as e:
            self.__LOGGER.error(f"Unhandled Exception - {type(e).__name__} : {e} - {sys.exc_info()[2].tb_frame.f_code.co_filename} - {sys.exc_info()[2].tb_lineno}")
            raise e

    # Method for deleting handlers from an existing OpenstackService
    def delete_client_handler(self, handler_name):
        self.__LOGGER.debug(f"Attempting to delete handler {handler_name}")
        try:
            del self.handlers[handler_name]
            return True
        except Exception as e:
            self.__LOGGER.error(f"Unhandled Exception - {type(e).__name__} : {e} - {sys.exc_info()[2].tb_frame.f_code.co_filename} - {sys.exc_info()[2].tb_lineno}")
            raise e

    # Private method for checking if a handler exists in the object, if not raise exception
    def __check_handlers(self, *args):
        missing = [ client for client in args if client not in self._handlers_key_map ]
        if missing:
            self.__LOGGER.error(f"Required handler(s) missing for most recent operation : {missing}")
            raise NoHandlerFound(missing)
        else:
            return True

    # Private method for fetching required openstack objects from given handler
    # valid client_types (string): keystone, nove, gnocchi, heat
    # obj_names (dict{string:list}) : {'obj type' : ['name1', 'name2']}
    def __populate_required_objs(self, client_type, obj_names):
        self.__LOGGER.debug(f"Fetching required Openstack Objects for {client_type}")
        self.__check_handlers(client_type)
        handler = self.handlers[self._handlers_key_map[client_type]]

        found_objs = {}
        missing_objs = []
        for obj_type in obj_names:
            found_objs[obj_type] = {}
            for obj_name in obj_names[obj_type]:
                try:
                    found_objs[obj_type][obj_name] = getattr(handler, f"get_{obj_type}")(obj_name)
                except AttributeError as e:
                    self.__LOGGER.error(f"Failed fetching {obj_type}:{obj_name} - no function 'get_{obj_type}' found for {client_type} handler")
                    self.__LOGGER.error(f"{type(e).__name__} - {e}")
                    raise e
                if found_objs[obj_type][obj_name] is None:
                    missing_objs.append(f"{client_type}:{obj_type}:{obj_name}")
        
        if missing_objs:
            self.__LOGGER.error(f"Could not find required object(s) {missing_objs} - please have Administrator create in Openstack")
            raise MissingOpenstackObject(f"{missing_objs}")
        return found_objs

    # Returns a list of project ID that the openstack concertim user is a 'watcher' in
    def get_concertim_projects(self):
        self.__LOGGER.debug(f"Getting 'concertim' user role assignments for 'watcher' role.")
        self.__check_handlers('keystone')
        keystone = self.handlers[self._handlers_key_map['keystone']]

        proj_id_list=[]
        watcher_role = self.req_keystone_objs['role']['watcher']
        concertim_user = self.req_keystone_objs['user']['concertim']
        
        ra_list = keystone.client.role_assignments.list(user=concertim_user, role=watcher_role)
        for ra in ra_list:
            proj_id_list.append(ra.scope['project']['id'])
        
        self.__LOGGER.debug(f"Projects found for concertim:watcher : [{proj_id_list}]")
        return proj_id_list

    def get_instances(self, project_id):
        self.__LOGGER.debug(f"Getting Openstack instances for project '{project_id}'")
        self.__check_handlers('nova')
        nova = self.handlers[self._handlers_key_map['nova']]

        instances = nova.list_servers(project_id)
        return instances

    def get_flavors(self):
        self.__LOGGER.debug("Getting Openstack flavors with full details")
        self.__check_handlers('nova')
        nova = self.handlers[self._handlers_key_map['nova']]

        flavor_details = {}
        os_flavors = nova.list_flavors()
        for flavor in os_flavors:
            flavor_details[str(flavor.name)] = flavor._info
        return flavor_details
    
    def get_project_resources(self, project_id):
        self.__LOGGER.debug(f"Searching Gnocchi for resources in project:{project_id}")
        self.__check_handlers('gnocchi')
        gnocchi = self.handlers[self._handlers_key_map['gnocchi']]

        project_id_query = {"and": [{"=":{"project_id":project_id}}, {"=":{"ended_at":None}}]}
        results = gnocchi.search_resource(project_id_query)
        sorted_results = self.__sort_resource_list(results)
        return sorted_results

    def create_new_cm_project(self, name, domain='default'):
        self.__LOGGER.debug(f"Creating new Concertim-managed project '{name}' in domain '{domain}'")
        self.__check_handlers('keystone')
        keystone = self.handlers[self._handlers_key_map['keystone']]

        if domain != 'default':
            domain_ref = keystone.get_domain(domain)
        else:
            domain_ref = domain

        new_project = keystone.create_project(name, domain_ref, desc="Concertim managed project")
        self.__LOGGER.debug(f"Adding [concertim,admin] user roles to new project")
        try:
            keystone.add_user_to_project(user=self.req_keystone_objs['user']['concertim'],project=new_project,role=self.req_keystone_objs['role']['watcher'])
            keystone.add_user_to_project(user=self.req_keystone_objs['user']['concertim'],project=new_project,role=self.req_keystone_objs['role']['member'])
            keystone.add_user_to_project(user=self.req_keystone_objs['user']['admin'],project=new_project,role=self.req_keystone_objs['role']['admin'])
            self.__LOGGER.debug(f"New Concertim-managed project created successfully - '{new_project}'")
            return new_project
        except Exception as e:
            self.__LOGGER.error(f"Failed - Aborting - scrubbing created project")
            keystone.delete(new_project)
            self.__LOGGER.error(f"Failed to add required roles to new project - {type(e).__name__} - {e}")
            raise e

    def create_new_cm_user(self, name, password, email, project, domain='default'):
        self.__LOGGER.debug(f"Creating new Concertim-managed User '{name}' in domain '{domain}'")
        self.__check_handlers('keystone')
        keystone = self.handlers[self._handlers_key_map['keystone']]

        domain_ref = ''
        if domain != 'default':
            domain_ref = keystone.get_domain(domain)
        else:
            domain_ref = domain

        new_user = keystone.create_user(name, password, domain_ref, email=email, project=project, desc="Concertim managed User")
        try:
            self.__LOGGER.debug(f"Adding new_user to project")
            keystone.add_user_to_project(user=new_user,project=project,role=self.req_keystone_objs['role']['member'])
            self.__LOGGER.debug(f"New Concertim-managed user created successfully - '{new_user}'")
            return new_user
        except Exception as e:
            self.__LOGGER.error(f"Failed - Aborting - scrubbing created user")
            keystone.delete(new_user)
            self.__LOGGER.error(f"Failed to add required roles to new user - {type(e).__name__} - {e}")
            raise e

    def get_cpu_load(self, resource, start, stop, granularity=5):
        self.__LOGGER.debug(f"Getting CPU Load % for {resource['id']}")
        self.__check_handlers('gnocchi')
        gnocchi = self.handlers[self._handlers_key_map['gnocchi']]
        try:
            cpu_metric_id = resource['metrics']['cpu']
            ns_gran_prod = 1000000000.0 * granularity
            cpu_rate_resposes = gnocchi.get_metric_measure(metric=cpu_metric_id, aggregation='rate:mean', granularity=granularity, start=start, stop=stop)[-1]
            self.__LOGGER.debug(f"Calculating CPU Load Percent")
            cpu_load_ns_to_s = cpu_rate_resposes[2] / ns_gran_prod
            cpu_load_percent = cpu_load_ns_to_s * 100
            return round(cpu_load_percent,2)
        except IndexError as e:
            self.__LOGGER.warning(f"Metric retrieval [CPU Load : resource : {resource['id']}] returned no values, returning '0.0' : {e}")
            return 0.0

    def get_ram_usage(self, resource, start, stop, granularity=5):
        self.__LOGGER.debug(f"Getting RAM Usage % for {resource['id']}")
        self.__check_handlers('gnocchi')
        gnocchi = self.handlers[self._handlers_key_map['gnocchi']]
        try:
            memory_metric_id = resource['metrics']['memory']
            memory_usage_metric_id = resource['metrics']['memory.usage']
            memory = gnocchi.get_metric_measure(metric=memory_metric_id, refresh=False, limit=1)[0][2]
            memory_usage = gnocchi.get_metric_measure(metric=memory_usage_metric_id, aggregation='mean', granularity=granularity, start=start, stop=stop)[-1]
            self.__LOGGER.debug(f"Calculating RAM used Percentage")
            ram_usage_percent = memory_usage[2] / memory * 100
            return round(ram_usage_percent,2)
        except IndexError as e:
            self.__LOGGER.warning(f"Metric retrieval [RAM Usage : resource : {resource['id']}] returned no values, returning '0.0' : {e}")
            return 0.0
    
    def get_network_usage(self, resource, start, stop, granularity=5):
        self.__LOGGER.debug(f"Getting Network Usage for {resource['id']}")
        self.__check_handlers('gnocchi')
        gnocchi = self.handlers[self._handlers_key_map['gnocchi']]
        try:
            net_in_metric = resource['metrics']['network.incoming.bytes']
            net_out_metric = resource['metrics']['network.outgoing.bytes']
            net_in_tup = gnocchi.get_metric_measure(metric=net_in_metric, aggregation='rate:mean', granularity=granularity, start=start, stop=stop)[-1]
            net_out_tup = gnocchi.get_metric_measure(metric=net_out_metric, aggregation='rate:mean', granularity=granularity, start=start, stop=stop)[-1]
            self.__LOGGER.debug(f"Calculating Network usage in B/s")
            usage_rate = (net_in_tup[2] + net_out_tup[2]) / granularity
            return round(usage_rate,2)
        except IndexError as e:
            self.__LOGGER.warning(f"Metric retrieval [Network Usage : resource : {resource['id']}] returned no values, returning '0.0' : {e}")
            return 0.0

    def get_throughput(self, resource, start, stop, granularity=5):
        self.__LOGGER.debug(f"Getting Disk Throughput for {resource['id']}")
        self.__check_handlers('gnocchi')
        gnocchi = self.handlers[self._handlers_key_map['gnocchi']]
        try:
            disk_read_metric = resource['metrics']['disk.device.read.bytes']
            disk_write_metric = resource['metrics']['disk.device.write.bytes']
            disk_read_tup = gnocchi.get_metric_measure(metric=disk_read_metric, aggregation='rate:mean', granularity=granularity, start=start, stop=stop)[-1]
            disk_write_tup = gnocchi.get_metric_measure(metric=disk_write_metric, aggregation='rate:mean', granularity=granularity, start=start, stop=stop)[-1]
            self.__LOGGER.debug(f"Calculating Disk Throughput in B/s")
            throughput = (disk_write_tup[2] + disk_read_tup[2]) / granularity
            return round(throughput,2)
        except IndexError as e:
            self.__LOGGER.warning(f"Metric retrieval [Throughput : resource : {resource['id']}] returned no values, returning '0.0' : {e}")
            return 0.0

    def get_iops(self, resource, start, stop, granularity=5):
        self.__LOGGER.debug(f"Getting Disk IOPs for {resource['id']}")
        self.__check_handlers('gnocchi')
        gnocchi = self.handlers[self._handlers_key_map['gnocchi']]
        try:
            disk_read_metric = resource['metrics']['disk.device.read.requests']
            disk_write_metric = resource['metrics']['disk.device.write.requests']
            disk_read_tup = gnocchi.get_metric_measure(metric=disk_read_metric, aggregation='rate:mean', granularity=granularity, start=start, stop=stop)[-1]
            disk_write_tup = gnocchi.get_metric_measure(metric=disk_write_metric, aggregation='rate:mean', granularity=granularity, start=start, stop=stop)[-1]
            self.__LOGGER.debug(f"Calculating Disk IOPs in Ops/s")
            iops = (disk_write_tup[2] + disk_read_tup[2]) / granularity
            return round(iops,2)
        except IndexError as e:
            self.__LOGGER.warning(f"Metric retrieval [IOPs : resource : {resource['id']}] returned no values, returning '0.0' : {e}")
            return 0.0

    # Sort Openstack project resources and group by instance_id
    def __sort_resource_list(self, resource_list):
        self.__LOGGER.debug(f"Sorting Gnocchi Resources")
        grouped_resources = {}
        for resource in resource_list:
            display_name = None
            if "instance_id" in resource and resource["type"] != "volume":
                instance_id = resource["instance_id"]
            elif "id" in resource and resource["type"] == "instance":
                instance_id = resource["id"]
                display_name = resource["display_name"]
            elif resource["type"] == "volume":
                instance_id = "volumes"
            else:
                continue
            if instance_id not in grouped_resources:
                grouped_resources[instance_id] = {"display_name":None,"concertim_id":None,"resources":[]}
            if display_name is not None:
                grouped_resources[instance_id]["display_name"] = display_name.split('.')[0] + '-' + instance_id[:5]
            grouped_resources[instance_id]["resources"].append(resource)
        self.__LOGGER.debug(f"Sorting Completed")
        return grouped_resources

    def list_stacks(self, project_id=None):
        self.__LOGGER.debug("Getting Openstack Heat Stacks")
        self.__check_handlers('heat')
        heat = self.handlers[self._handlers_key_map['heat']]

        if project_id:
            return heat.list_stacks(filters={'project':project_id})
        return heat.list_stacks()

    def get_stack(self, stack_id):
        self.__LOGGER.debug(f"Getting Openstack Heat Stack {stack_id}")
        self.__check_handlers('heat')
        heat = self.handlers[self._handlers_key_map['heat']]

        return heat.get_stack(stack_id)

    def list_stack_resources(self, stack_id, **kwargs):
        self.__LOGGER.debug(f"Getting Openstack Resources for Heat Stack {stack_id}")
        self.__check_handlers('heat')
        heat = self.handlers[self._handlers_key_map['heat']]

        return heat.list_stack_resources(stack_id, **kwargs)

    def get_stack_instances(self, stack_id):
        self.__LOGGER.debug(f"Getting Openstack Instance Ids for Instances belonging to Heat Stack {stack_id}")
        self.__check_handlers('heat', 'nova')
        heat = self.handlers[self._handlers_key_map['heat']]
        nova = self.handlers[self._handlers_key_map['nova']]

        instance_ids = []
        instances = []
        stack_instance_resources = heat.list_stack_resources(stack_id=stack_id, type='OS::Nova::Server')
        stack_server_group_resources = heat.list_stack_resources(stack_id=stack_id, type='OS::Nova::ServerGroup')
        # server group parsing
        if stack_server_group_resources:
            for sg_r in stack_server_group_resources:
                nova_sg = nova.get_server_group(sg_r.physical_resource_id)
                instance_ids = instance_ids + nova_sg._info['members']
        # instance parsing
        if stack_instance_resources:
            for inst_r in stack_instance_resources:
                if inst_r.resource_type == 'OS::Nova::Server':
                    instance_ids.append(inst_r.physical_resource_id)
        # get nova server objs for all instance ids
        for inst_id in instance_ids:
            try:
                instances.append(nova.get_server(inst_id))
            except novaclient.exceptions.NotFound as e:
                self.__LOGGER.warning(f"Could not find server '{inst_id}' from stack '{stack_id}' in Openstack - skipping")
                continue
        return instances

    def get_stack_output(self, stack_id):
        self.__LOGGER.debug(f"Getting output from Heat Stack {stack_id}")
        self.__check_handlers('heat')
        heat = self.handlers[self._handlers_key_map['heat']]
        
        return_output = []
        output_list = heat.list_stack_output(stack_id)
        for output_dict in output_list:
            output_details = heat.show_output(stack_id,output_dict['output_key'])
            return_output.append((output_dict['output_key'],output_details['output_value']))
        return return_output

    def update_instance_status(self, instance_id, action):
        self.__LOGGER.debug(f"Attempting action '{action}' on instance '{instance_id}'")
        self.__check_handlers('nova')
        nova = self.handlers[self._handlers_key_map['nova']]
        actions_map = {
            'on': nova.switch_on_device,
            'off': nova.switch_off_device,
            'suspend': nova.suspend_device,
            'resume': nova.resume_device,
            'destroy': nova.destroy_device
        }
        if action not in actions_map:
            raise APIServerDefError("Invalid action")
        attempt = actions_map[action](instance_id)
        if isinstance(attempt, novaclient.exceptions.ClientException):
            raise attempt
        return attempt

    def update_stack_status(self, stack_id, action):
        self.__LOGGER.debug(f"Attempting action '{action}' on stack '{stack_id}'")
        self.__check_handlers('heat')
        heat = self.handlers[self._handlers_key_map['heat']]
        actions_map = {
            #'on': heat.switch_on_stack,
            #'off': heat.switch_off_stack,
            #'suspend': heat.suspend_stack,
            #'resume': heat.resume_stack,
            'destroy': heat.destroy_stack
        }
        if action not in actions_map:
            raise APIServerDefError("Invalid action")
        attempt = actions_map[action](stack_id)
        # If attempt returns the specified exc from the heat.action(id) call, use fallback
        if isinstance(attempt, heatclient.exc.BaseException):
            return self._update_stack_status_fallback(stack_id, action)
        return attempt

    # For when the heat stack has issues changing status
    # Loop over each instance and change status one at a time
    # Returns a dict of {'success':[], 'failure':[], outcome: }
    # This would need additional logic for updating status of other resources.
#     def _update_stack_status_fallback(self, stack_id, action):
#         self.__LOGGER.debug(f"Attempting action '{action}' on stack '{stack_id}' using fallback method")
#         instances = self.get_stack_instances(stack_id)
#         result = {'success': [], 'failure': [], 'outcome': None}
#         for inst in instances:
#             try:
#                 temp = self.update_instance_status(inst, action)
#                 result["success"].append(temp)
#             except (novaclient.exceptions.MethodNotAllowed, novaclient.exceptions.Forbidden, novaclient.exceptions.Conflict) as e:
#                 self.__LOGGER.warning(f"Exception when updating instance in stack {stack_id} - {e.__class__.__name__} - {e.message}")
#                 result["failure"].append(e.message)
#                 continue
#         if result["success"]:
#              result["outcome"] = "partial failure" if result["failure"] else "success"
#         elif result["failure"]:
#              result["outcome"] = "failure"
#         return result

    # NOTE: only specify user if using an ADMIN session
    def create_keypair(self, name, imported_pub_key=None, key_type='ssh'):
        self.__LOGGER.debug(f"Attempting to add new keypair '{name}'")
        self.__check_handlers('nova')
        nova = self.handlers[self._handlers_key_map['nova']]

        try:
             if imported_pub_key:
                 self.__LOGGER.debug(f"Creating keypair using provided public key")
                 keypair = nova.create_keypair(name, public_key=imported_pub_key, key_type=key_type)
                 self.__LOGGER.debug(f"Successfully added keypair {keypair.name} for user {keypair.user_id}")
                 return keypair
             else:
                self.__LOGGER.debug(f"Creating keypair from scratch")
                keypair = nova.create_keypair(name, key_type=key_type)
                self.__LOGGER.debug(f"Successfully added keypair {keypair.name} for user {keypair.user_id}")
                return keypair
        # TODO: except whatever is thrown if keytype is wrong
        # TODO: except whatever is thrown if publickey couldnt be used
        # TODO: except whatever is thrown if could not create for user
        except Exception as e:
            self.__LOGGER.error(f"An unexpected error : {type(e).__name__} - {e}")
            raise e

    def list_keypairs(self):
        self.__LOGGER.debug(f"Attempting to list keypairs")
        self.__check_handlers('nova')
        nova = self.handlers[self._handlers_key_map['nova']]

        try:
            keypairs = nova.list_keypairs()
            self.__LOGGER.debug(f"Successfully obtained keypairs")
            return keypairs
        except Exception as e:
            self.__LOGGER.error(f"An unexpected error : {type(e).__name__} - {e}")
            raise e

    def disconnect(self):
        self.__LOGGER.info("Disconnecting Openstack Services")
        self.__OPSTK_AUTH = None
        for handler in self.handlers.values():
            handler.close()
        self._handlers_key_map = None
        self.handlers = None
