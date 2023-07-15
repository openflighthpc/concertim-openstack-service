# Local Imports
from utils.service_logger import create_logger
from data_handler.handler import DataHandler
from openstack.openstack import MissingOpenstackObject
# Py Packages
import time
from datetime import datetime, timedelta
import sys

class MetricHandler(DataHandler):
    def __init__(self, openstack, concertim, config_obj, log_file, interval=5):
        self.__LOGGER = create_logger(__name__, log_file, config_obj['log_level'])
        self.interval = interval
        super().__init__(openstack, concertim, config_obj, log_file)

    def send_metrics(self):
        self.__LOGGER.info('METRICS - BEGIN SENDING METRICS')
        try:
            self.__LOGGER.debug(f"Getting concertim:watcher project_ids list")
            concertim_projects_list = self.openstack_service.get_concertim_projects()
            self.__LOGGER.debug(f"Getting all current devices in Concertim")
            concertim_device_list = self.concertim_service.list_devices()
            for project_id in concertim_projects_list:
                self.__LOGGER.debug(f"Getting resource list for {project_id}")
                temp_recs = self.openstack_service.get_project_resources(project_id)
                self.__LOGGER.debug(f"Merging concertim device IDs with Openstack resources")
                resources = self.__merge_ids(temp_recs, concertim_device_list)

                # Handle instance resource group
                self.__LOGGER.debug(f"Starting - instance-based metric sending")
                for instance_id in (not_vol for not_vol in resources if not_vol not in ['volumes']):
                    if resources[instance_id]['concertim_id']:
                        # Handle instance / nova based metrics for instance resource group with a device present
                        self.__LOGGER.debug(f"Handling metrics for instance : {instance_id}, device : {resources[instance_id]['concertim_id']}")
                        self.handle_metrics(resources[instance_id])
                self.__LOGGER.debug(f"Finished - Instance-based metric sending for project {project_id}")

                # Handle other resource groups
                self.__LOGGER.debug(f"Starting - volume-based metric sending")
                # Handle metrics for volume resource type
                self.__LOGGER.debug(f"Finished - Volume-based metric sending for project {project_id}")
            self.__LOGGER.info(f"METRICS - METRIC SENDING COMPLETE")
        except MissingOpenstackObject as e:
            logger.error(f"Missing Openstack Component: {e}")
            raise e


    # Send all metrics for a given instance's resources
    def handle_metrics(self, instance_resource_dict):
        self.__LOGGER.debug(f"Starting - Processing metrics for instance:{instance_resource_dict['display_name']}")
        # 'interval' seconds window (range from now-interval to now)
        # NOTE: 'interval' and 'granularity' are closely related. 
        #       'interval' should only equal a valid granularity to ensure proper calculation
        stop = datetime.utcnow()- timedelta(seconds=1)
        start = stop - timedelta(seconds=self.interval)
        self.__LOGGER.debug(f"Metric window: [start:'{start}' - stop:'{stop}']")
        for resource in instance_resource_dict["resources"]:
            # Metric Fetching based on resource
            # '''
            if resource["type"] == "instance":
                # CPU Load as a percent
                cpu_load = self.openstack_service.get_cpu_load(resource, start, stop, granularity=5)
                #print(f"CPU LOAD FOR {resource['id']} : {cpu_load} %")
                self.concertim_service.send_metric(instance_resource_dict["concertim_id"], {'type': "double",'name': "os.instance.cpu_utilization",'value': cpu_load,'units': '%','slope': "both",'ttl': 3600})
                #'''
                # RAM Usage as a percent
                ram_usage = self.openstack_service.get_ram_usage(resource, start, stop, granularity=5)
                #print(f"RAM USAGE FOR {resource['id']} : {ram_usage} %")
                self.concertim_service.send_metric(instance_resource_dict["concertim_id"], {'type': "double",'name': "os.instance.ram_usage",'value': ram_usage,'units': '%','slope': "both",'ttl': 3600})
            #'''
            elif resource["type"] == "instance_network_interface":
                # Network usgae in megabytes/s
                network_usage = self.openstack_service.get_network_usage(resource, start, stop, granularity=5)
                #print(f"NET USAGE FOR {resource['id']} : {network_usage} B/s")
                self.concertim_service.send_metric(instance_resource_dict["concertim_id"], {'type': "double",'name': "os.net.avg_usage",'value': network_usage,'units': 'B/s','slope': "both",'ttl': 3600})
            #'''
            elif resource["type"] == "instance_disk":
                # Throughput in megabytes/s
                throughput = self.openstack_service.get_throughput(resource, start, stop, granularity=5)
                #print(f"THROUGHPUT FOR {resource['id']} : {throughput} B/s")
                self.concertim_service.send_metric(instance_resource_dict["concertim_id"], {'type': "double",'name': "os.disk.avg_throughput",'value': throughput,'units': 'B/s','slope': "both",'ttl': 3600})
                #'''
                # IOPs in Ops/s
                iops = self.openstack_service.get_iops(resource, start, stop, granularity=5)
                #print(f"IOPS FOR {resource['id']} : {iops} Ops/s")
                self.concertim_service.send_metric(instance_resource_dict["concertim_id"], {'type': "double",'name': "os.disk.avg_iops",'value': iops,'units': 'Ops/s','slope': "both",'ttl': 3600})
            #'''
        self.__LOGGER.debug(f"Finished - Processing metrics for instance:{instance_resource_dict['display_name']}")

    def __merge_ids(self, resource_list, concertim_device_list):
        merged = resource_list
        for instance_id in resource_list:
            if instance_id in ['volumes']:
                self.__LOGGER.debug(f"Skipping volumes")
                continue
            for device in concertim_device_list:
                if device['metadata']['openstack_instance_id'].replace('-','') == instance_id.replace('-',''):
                    self.__LOGGER.debug(f"Resources for device '{device['id']}' found. Merging IDs")
                    merged[instance_id]['concertim_id'] = device['id']
        return merged
