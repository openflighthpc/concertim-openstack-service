# Local Imports
from utils.service_logger import create_logger
from openstack.opstk_auth import OpenStackAuth
from openstack.keystone import KeystoneHandler
from openstack.nova import NovaHandler
from openstack.gnocchi import GnocchiHandler
from openstack.heat import HeatHandler

# Custom Exceptions
class MissingOpenstackObject(Exception):
    pass

class OpenstackService(object):
    def __init__(self, config_obj, log_file):
        self.__CONFIG = config_obj
        self.__LOGGER = create_logger(__name__, log_file, self.__CONFIG['log_level'])
        self.__OPSTK_AUTH = OpenStackAuth(self.__CONFIG['openstack'])
        self.keystone = KeystoneHandler(self.__OPSTK_AUTH.get_session(), log_file, self.__CONFIG['log_level'])
        self.gnocchi = GnocchiHandler(self.__OPSTK_AUTH.get_session(), log_file, self.__CONFIG['log_level'])
        self.nova = NovaHandler(self.__OPSTK_AUTH.get_session(), log_file, self.__CONFIG['log_level'])
        self.heat = HeatHandler(self.__OPSTK_AUTH.get_session(), log_file, self.__CONFIG['log_level'])
    
    # Returns a list of project ID that the openstack concertim user is a 'watcher' in
    def get_concertim_projects(self):
        role=None
        user=None
        proj_id_list=[]
        self.__LOGGER.debug(f"Getting 'watcher' role")
        watcher_role = self.keystone.watcher_role
        if watcher_role is None:
            self.__LOGGER.error(f"Could not find 'watcher' role, please have an Admin create the 'watcher' role in Openstack.")
            raise MissingOpenstackObject(f"Could not find 'watcher' role, please have an Admin create the 'watcher' role in Openstack.")
        elif type(watcher_role) is list:
            self.__LOGGER.debug(f"Multiple 'watcher' roles found, using first occurance.")
            role = watcher_role[0]
        else:
            role = watcher_role

        self.__LOGGER.debug(f"Getting 'concertim' user")
        concertim_user = self.keystone.concertim_user
        if concertim_user is None:
            self.__LOGGER.error(f"Could not find 'concertim' user, please have an Admin create the 'concertim' user in Openstack.")
            raise MissingOpenstackObject(f"Could not find 'concertim' user, please have an Admin create the 'concertim' user in Openstack.")
        elif type(concertim_user) is list:
            self.__LOGGER.debug(f"Multiple 'concertim' users found, using first occurance.")
            user = concertim_user[0]
        else:
            user = concertim_user
        
        self.__LOGGER.debug(f"Getting 'concertim' user role assignments for 'watcher' role.")
        ra_list = self.keystone.client.role_assignments.list(user=user, role=role)
        for ra in ra_list:
            proj_id_list.append(ra.scope['project']['id'])
        
        self.__LOGGER.debug(f"Projects found for concertim:watcher : {proj_id_list}")
        return proj_id_list

    def get_instances(self, project_id):
        instances = self.nova.list_servers(project_id)
        return instances

    def get_flavors(self):
        self.__LOGGER.debug("Getting Openstack flavors")
        flavor_details = {}
        os_flavors = self.nova.list_flavors()
        for flavor in os_flavors:
            flavor_details[str(flavor.name)] = flavor._info
        return flavor_details
    
    def get_project_resources(self, project_id):
        project_id_query = {"and": [{"=":{"project_id":project_id}}, {"=":{"ended_at":None}}]}
        self.__LOGGER.debug(f"Searching Gnocchi for resources in project:{project_id}")
        results = self.gnocchi.search_resource(project_id_query)
        sorted_results = self.__sort_resource_list(results)
        return sorted_results

    def get_cpu_load(self, resource, start, stop, granularity=5):
        self.__LOGGER.debug(f"Getting CPU Load % for {resource['id']}")
        try:
            cpu_metric_id = resource['metrics']['cpu']
            ns_gran_prod = 1000000000.0 * granularity
            cpu_rate_resposes = self.gnocchi.get_metric_measure(metric=cpu_metric_id, aggregation='rate:mean', granularity=granularity, start=start, stop=stop)[-1]
            self.__LOGGER.debug(f"Calculating CPU Load Percent")
            cpu_load_ns_to_s = cpu_rate_resposes[2] / ns_gran_prod
            cpu_load_percent = cpu_load_ns_to_s * 100
            return round(cpu_load_percent,2)
        except IndexError as e:
            self.__LOGGER.warning(f"Metric retrieval [CPU Load : resource : {resource['id']}] returned no values, returning '0.0'  : {e}")
            return 0.0

    def get_ram_usage(self, resource, start, stop, granularity=5):
        self.__LOGGER.debug(f"Getting RAM Usage % for {resource['id']}")
        try:
            memory_metric_id = resource['metrics']['memory']
            memory_usage_metric_id = resource['metrics']['memory.usage']
            memory = self.gnocchi.get_metric_measure(metric=memory_metric_id, refresh=False, limit=1)[0][2]
            memory_usage = self.gnocchi.get_metric_measure(metric=memory_usage_metric_id, aggregation='mean', granularity=granularity, start=start, stop=stop)[-1]
            self.__LOGGER.debug(f"Calculating RAM used Percentage")
            ram_usage_percent = memory_usage[2] / memory * 100
            return round(ram_usage_percent,2)
        except IndexError as e:
            self.__LOGGER.warning(f"Metric retrieval [RAM Usage : resource : {resource['id']}] returned no values, returning '0.0'  : {e}")
            return 0.0
    
    def get_network_usage(self, resource, start, stop, granularity=5):
        self.__LOGGER.debug(f"Getting Network Usage for {resource['id']}")
        try:
            net_in_metric = resource['metrics']['network.incoming.bytes']
            net_out_metric = resource['metrics']['network.outgoing.bytes']
            net_in_tup = self.gnocchi.get_metric_measure(metric=net_in_metric, aggregation='rate:mean', granularity=granularity, start=start, stop=stop)[-1]
            net_out_tup = self.gnocchi.get_metric_measure(metric=net_out_metric, aggregation='rate:mean', granularity=granularity, start=start, stop=stop)[-1]
            self.__LOGGER.debug(f"Calculating Network usage in B/s")
            usage_rate = (net_in_tup[2] + net_out_tup[2]) / granularity
            return round(usage_rate,2)
        except IndexError as e:
            self.__LOGGER.warning(f"Metric retrieval [Network Usage : resource : {resource['id']}] returned no values, returning '0.0'  : {e}")
            return 0.0

    def get_throughput(self, resource, start, stop, granularity=5):
        self.__LOGGER.debug(f"Getting Disk Throughput for {resource['id']}")
        try:
            disk_read_metric = resource['metrics']['disk.device.read.bytes']
            disk_write_metric = resource['metrics']['disk.device.write.bytes']
            disk_read_tup = self.gnocchi.get_metric_measure(metric=disk_read_metric, aggregation='rate:mean', granularity=granularity, start=start, stop=stop)[-1]
            disk_write_tup = self.gnocchi.get_metric_measure(metric=disk_write_metric, aggregation='rate:mean', granularity=granularity, start=start, stop=stop)[-1]
            self.__LOGGER.debug(f"Calculating Disk Throughput in B/s")
            throughput = (disk_write_tup[2] + disk_read_tup[2]) / granularity
            return round(throughput,2)
        except IndexError as e:
            self.__LOGGER.warning(f"Metric retrieval [Throughput : resource : {resource['id']}] returned no values, returning '0.0'  : {e}")
            return 0.0

    def get_iops(self, resource, start, stop, granularity=5):
        self.__LOGGER.debug(f"Getting Disk IOPs for {resource['id']}")
        try:
            disk_read_metric = resource['metrics']['disk.device.read.requests']
            disk_write_metric = resource['metrics']['disk.device.write.requests']
            disk_read_tup = self.gnocchi.get_metric_measure(metric=disk_read_metric, aggregation='rate:mean', granularity=granularity, start=start, stop=stop)[-1]
            disk_write_tup = self.gnocchi.get_metric_measure(metric=disk_write_metric, aggregation='rate:mean', granularity=granularity, start=start, stop=stop)[-1]
            self.__LOGGER.debug(f"Calculating Disk IOPs in Ops/s")
            iops = (disk_write_tup[2] + disk_read_tup[2]) / granularity
            return round(iops,2)
        except IndexError as e:
            self.__LOGGER.warning(f"Metric retrieval [IOPs : resource : {resource['id']}] returned no values, returning '0.0'  : {e}")
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

    def list_stacks(self):
        self.__LOGGER.debug("Getting Openstack Heat Stacks")
        return self.heat.list_stacks()

    def get_stack(self, stack_id):
        self.__LOGGER.debug(f"Getting Openstack Heat Stack {stack_id}")
        return self.heat.get_stack(stack_id)

    def list_stack_resources(self, stack_id, **kwargs):
        return self.heat.list_stack_resources(stack_id, **kwargs)

    def get_stack_instances(self, stack_id):
        instance_ids = []
        instances = []
        stack_instance_resources = self.heat.list_stack_resources(stack_id=stack_id, type='OS::Nova::Server')
        stack_server_group_resources = self.heat.list_stack_resources(stack_id=stack_id, type='OS::Nova::ServerGroup')
        # server group parsing
        if stack_server_group_resources:
            for sg_r in stack_server_group_resources:
                nova_sg = self.nova.get_server_group(sg_r.physical_resource_id)
                instance_ids = instance_ids + nova_sg._info['members']
        # instance parsing
        if stack_instance_resources:
            for inst_r in stack_instance_resources:
                if inst_r.resource_type == 'OS::Nova::Server':
                    instance_ids.append(inst_r.physical_resource_id)
        # get nova server objs for all instance ids
        for inst_id in instance_ids:
            if self.nova.server_exists(inst_id):
                instances.append(self.nova.get_server(inst_id))
        return instances

    def disconnect(self):
        self.__LOGGER.info("Disconnecting Openstack Services")
        self.__OPSTK_AUTH = None
        self.keystone.close()
        self.gnocchi.close()
        self.nova.close()
