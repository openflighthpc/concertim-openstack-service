# TODO:
# change 'device' logic to bridge instances in openstack and devices in concertim

import json
import requests
import time
requests.packages.urllib3.disable_warnings() 
import logging
import os
from datetime import datetime, timedelta
import gnocchiclient.v1.client as gnocchi_client
from keystoneauth1 import session
from keystoneauth1.identity import v3
import concertim_helper


# The main service class
class ConcertimService(object):
    # Initializes the service object
    def __init__(self):
        self._CONFIG_FILE = "/etc/concertim-openstack-service/config.json"
        self._LOG_FILE = "/var/log/concertim-openstack-service.log"
        self._config = self._load_config(self._CONFIG_FILE)
        self._logger = self._create_logger(self._LOG_FILE)
        self._auth = None
        self._gnocchi = None
        self._auth_token = None

    # Runs the main service loop
    def run(self):
        self._authenticate_openstack()
        self._connect_gnocchi()
        self._authenticate_concertim(self._config["concertim_username"], self._config["concertim_password"])
        while True:
            self._update_concertim()
            self._send_metrics()
            time.sleep(300)
        #print(concertim_helper.create_concertim_device(concertimService=self, device_name="concertim-instance-4", rack_id=1, start_location_id=38, template_id=5, device_description="Made UP instance", facing="f"))
        #self._update_concertim()
        #self._send_metrics()


    # Loads the configuration from the specified JSON file
    def _load_config(self, config_file):
        with open(config_file) as f:
            return json.load(f)

    # Creates a logger instance to log events and errors to a file
    def _create_logger(self, log_file):
        logger = logging.getLogger(__name__)
        logger.setLevel(self._config["log_level"])
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        if not os.path.exists(self._LOG_FILE):
            open(self._LOG_FILE, 'w').close()
        fh = logging.FileHandler(log_file)
        fh.setFormatter(formatter)
        logger.addHandler(fh)
        return logger

    # Authenticates with the OpenStack Keystone API and obtains an auth object
    def _authenticate_openstack(self):
        auth = v3.Password(auth_url=self._config["auth_url"],
                           username=self._config["username"],
                           password=self._config["password"],
                           project_name=self._config["project_name"],
                           user_domain_name=self._config["user_domain_name"],
                           project_domain_name=self._config["project_domain_name"])
        self._auth = auth
        
    # Authenticates with the CONCERTIM API and obtains an authentication token
    def _authenticate_concertim(self, login, password):
        base_url = self._config["concertim_url"]
        url = f"{base_url}/users/sign_in.json"
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        data = json.dumps({
            "user": {
                "login": login,
                "password": password,
            }
        })
        response = requests.post(url, headers=headers, data=data, verify=False)
        if response.status_code in (200, 201):
            token = response.headers.get("Authorization")
            if token:
                self._auth_token = token
                self._logger.info("Authenticated with CONCERTIM successfully")
            else:
                self._logger.error("Failed to obtain auth token from CONCERTIM API")
                raise Exception("Failed to obtain auth token from CONCERTIM API")
        else:
            self._logger.error("Authentication with CONCERTIM failed: ", response.text)
            raise Exception("Authentication with CONCERTIM failed")

    # Connects to the Gnocchi API
    def _connect_gnocchi(self):
        sess = session.Session(auth=self._auth)
        try:
            gnocchi = gnocchi_client.Client(session=sess)
            self._gnocchi = gnocchi
        except Exception as e:
            self._logger.error("Failed to authenticate Gnocchi with OpenStack: {}".format(str(e)))
            raise e
        self._logger.info("Authenticated and connected Gnocchi successfully")

    # Sends the metrics for each device to the CONCERTIM API
    def _send_metrics(self):
        # LIMIT TO ONE PROJECT FOR TESTING
        project_id_list = ["ef821aa9e576420c8768671d911a9766"]
        ceilometer_granularity = 300
        stop = datetime.now() - timedelta(minutes=60)
        start = stop - timedelta(minutes=10)
        
        for project_id in project_id_list:
            self._logger.info(f"Begin Sending Metrics for Project: {project_id}")
            project_query = {"and": [{"=":{"project_id":project_id}}, {"=":{"ended_at":None}}]}
            openstack_resources_list = self._gnocchi.resource.search(query=project_query, details=True)
            for resource in openstack_resources_list:
                # Metric Fetching based on resource
                if resource["type"] == "instance":

                    # CPU Load as a percent
                    self._logger.info(f"Calculating CPU Load for {resource['display_name']}")
                    cpu_metric_id = resource['metrics']['cpu']
                    ns_to_s_granularity = ceilometer_granularity * 1000000000.0
                    cpu_load_percent = self._gnocchi.aggregates.fetch(operations=f"(* (/ (aggregate rate:mean (metric {cpu_metric_id} mean)) {ns_to_s_granularity}) 100)", 
                                                                    resource_type="instance", start=start, stop=stop)["measures"]["aggregated"][0][2]
                    self._logger.debug(f"Sending CPU Load = {cpu_load_percent} to instance {resource['id']} ({resource['display_name']})")
                    concertim_helper.post_metric_to_concertim(concertimService=self, obj_to_update_name=resource['display_name'], metric_name=f"os.cpu_utilization", 
                                                                    metric_value=cpu_load_percent, metric_datatype="float", metric_slope="both", metric_units="%")
                    
                    # RAM Usage as a percent
                    self._logger.info(f"Calculating RAM Usage for {resource['display_name']}")
                    memory_metric_id = resource['metrics']['memory']
                    memory = self._gnocchi.metric.get_measures(metric=memory_metric_id, limit=1)[0][2]
                    memory_usage_metric_id = resource['metrics']['memory.usage']
                    memory_usage = self._gnocchi.metric.get_measures(metric=memory_usage_metric_id, start=start, stop=stop)[0][2]
                    ram_usage_percent = memory_usage/memory*100
                    self._logger.debug(f"Sending RAM Usage = {ram_usage_percent} to instance {resource['id']} ({resource['display_name']})")
                    concertim_helper.post_metric_to_concertim(concertimService=self, obj_to_update_name=resource['display_name'], metric_name=f"os.ram_usage", 
                                                                    metric_value=ram_usage_percent, metric_datatype="float", metric_slope="both", metric_units="%")

                elif resource["type"] == "instance_network_interface":
                    r_instance_network_interface = resource
                
                elif resource["type"] == "instance_disk":
                    x = resource

    # Check openstack to see if there are any new instances and update concertim if there are
    def _update_concertim(self):
        # LIMIT TO ONE PROJECT FOR TESTING
        project_query = {"and": [{"=":{"project_id":"ef821aa9e576420c8768671d911a9766"}}, {"=":{"ended_at":None}}]}
        new_rack_height = 42

        openstack_instance_list = self._gnocchi.resource.search(resource_type="instance", query=project_query, details=True)
        concertim_device_list = concertim_helper.get_concertim_devices(concertimService=self)
        concertim_rack_list = concertim_helper.get_concertim_racks(concertimService=self)
        new_device_list = []

        for instance in openstack_instance_list:
            corresponding_device = [d for d in concertim_device_list if d['name'] == instance["display_name"]]
            if not corresponding_device:
                self._logger.info(f"New Instance Found in Openstack - {instance['display_name']}")
                instance_vcpus = self._gnocchi.metric.get_measures(metric=instance["metrics"]["vcpus"])[0][2]
                new_device_list.append((instance["display_name"], instance["id"], instance_vcpus))

        concertim_helper.build_device_list(self,new_device_list)

    # Handles exceptions that occur during runtime
    def _handle_exception(self, e):
        self._logger.exception(e)

    # Starts the service
    def start(self):
        try:
            self.run()
        except Exception as e:
            self._handle_exception(e)
            self.stop()

    # Stops the service
    def stop(self):
        self._logger.info("Stopping the Concertim service")
        # clean up resources if needed
        raise SystemExit


