# Local Imports
from utils.service_logger import create_logger
from openstack.opstk_auth import OpenStackAuth
from openstack.keystone import KeystoneHandler
from openstack.nova import NovaHandler
from openstack.gnocchi import GnocchiHandler


class OpenstackService(object):
    def __init__(self, config_obj):
        self.__CONFIG = config_obj
        self.__LOGGER = create_logger(__name__, '/var/log/concertim-openstack-service-opt.log', self.__CONFIG['log_level'])
        self.__OPSTK_AUTH = OpenStackAuth(self.__CONFIG['openstack'])
        self.keystone = KeystoneHandler(self.__OPSTK_AUTH.get_session(), self.__CONFIG['log_level'])
        self.gnocchi = GnocchiHandler(self.__OPSTK_AUTH.get_session(), self.__CONFIG['log_level'])
        self.nova = NovaHandler(self.__OPSTK_AUTH.get_session(), self.__CONFIG['log_level'])
    
    # Returns a list of project ID that the openstack concertim user is a member of
    def get_concertim_projects(self):
        projects = self.keystone.get_projects(user=self.keystone._concertim_user)
        id_list = []
        for project in projects:
            id_list.append(project.id)
        return id_list

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

    def get_cpu_load(self, resource, start, stop):
        self.__LOGGER.debug(f"Getting CPU Load % for {resource['id']}")
        cpu_metric_id = resource['metrics']['cpu']
        cpu_load_tuple = self.gnocchi.get_aggregate(f"(aggregate rate:mean (metric {cpu_metric_id} mean))", start, stop)
        granularity = cpu_load_tuple[1]
        cpu_load_val = (cpu_load_tuple[2] / (1000000000.0 * granularity)) * 100
        return cpu_load_val

    def get_ram_usage(self, resource, start, stop):
        self.__LOGGER.debug(f"Getting RAM Usage % for {resource['id']}")
        memory_metric_id = resource['metrics']['memory']
        memory_usage_metric_id = resource['metrics']['memory.usage']
        memory = self.gnocchi.client.metric.get_measures(metric=memory_metric_id, limit=1)[0][2]
        memory_usage = self.gnocchi.get_metric_measure(metric=memory_usage_metric_id, start=start, stop=stop)[2]
        ram_usage_percent = memory_usage/memory*100
        return ram_usage_percent
    
    def get_network_usage(self, resource, start, stop):
        self.__LOGGER.debug(f"Getting Network Usage for {resource['id']}")
        net_in_metric = resource['metrics']['network.incoming.bytes']
        net_out_metric = resource['metrics']['network.outgoing.bytes']
        net_in_tup = self.gnocchi.client.metric.get_measures(metric=net_in_metric, aggregation="rate:mean", start=start, stop=stop)[0]
        net_out_tup = self.gnocchi.client.metric.get_measures(metric=net_out_metric, aggregation="rate:mean", start=start, stop=stop)[0]
        usage_rate = (net_in_tup[2] + net_out_tup[2]) / net_in_tup[1]
        return usage_rate

    def get_throughput(self, resource, start, stop):
        self.__LOGGER.debug(f"Getting Disk Throughput for {resource['id']}")
        disk_read_metric = resource['metrics']['disk.device.read.bytes']
        disk_write_metric = resource['metrics']['disk.device.write.bytes']
        disk_read_tup = self.gnocchi.client.metric.get_measures(metric=disk_read_metric, aggregation="rate:mean", start=start, stop=stop)[0]
        disk_write_tup = self.gnocchi.client.metric.get_measures(metric=disk_write_metric, aggregation="rate:mean", start=start, stop=stop)[0]
        throughput = (disk_write_tup[2] + disk_read_tup[2]) / disk_read_tup[1]
        return throughput

    def get_iops(self, resource, start, stop):
        self.__LOGGER.debug(f"Getting Disk IOPs for {resource['id']}")
        disk_read_metric = resource['metrics']['disk.device.read.requests']
        disk_write_metric = resource['metrics']['disk.device.write.requests']
        disk_read_tup = self.gnocchi.client.metric.get_measures(metric=disk_read_metric, aggregation="rate:mean", start=start, stop=stop)[0]
        disk_write_tup = self.gnocchi.client.metric.get_measures(metric=disk_write_metric, aggregation="rate:mean", start=start, stop=stop)[0]
        iops = (disk_write_tup[2] + disk_read_tup[2]) / disk_read_tup[1]
        return iops

    # Sort Openstack project resources and group by instance_id
    def __sort_resource_list(self, resource_list):
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
                grouped_resources[instance_id] = {"display_name":None,"resources":[]}
            if display_name is not None:
                grouped_resources[instance_id]["display_name"] = display_name.split('.')[0] + '-' + instance_id[:5]
            grouped_resources[instance_id]["resources"].append(resource)
        return grouped_resources

    def disconnect(self):
        self.__LOGGER.info("Disconnecting Openstack Services")
        self.__OPSTK_AUTH = None
        self.keystone.close()
        self.gnocchi.close()
        self.nova.close()