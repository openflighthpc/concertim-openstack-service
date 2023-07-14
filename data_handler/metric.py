# Local Imports
from utils.service_logger import create_logger
from data_handler.handler import DataHandler
# Py Packages
import time
from datetime import datetime, timedelta
import sys

class MetricHandler(DataHandler):
    def __init__(self, openstack, concertim, config_obj, log_file, interval):
        self.__LOGGER = create_logger(__name__, log_file, config_obj['log_level'])
        super().__init__(self, openstack, concertim, config_obj, log_file)
        self.interval = interval

    def send_metrics(self):
        self.__LOGGER.info('Sending Metrics')
        # for all concertim managed projects, get all resources, then post metrics for each resource
        '''
        for project_id in self.devices_racks:
            resources = self.openstack_service.get_project_resources(project_id)
            for rack_id in self.devices_racks[project_id]:
                for instance_id in self.devices_racks[project_id][rack_id]['devices']:
                    self.handle_metrics(resources[instance_id])
        '''
        concertim_projects_list = self.openstack_service.get_concertim_projects()

