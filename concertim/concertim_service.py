# TODO:
# change 'device' logic to bridge instances in openstack and devices in concertim

import time
import json
import requests
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
        self._devices = {}
        self._auth_token = None

    # Runs the main service loop
    def run(self):
        self._authenticate_openstack()
        self._connect_gnocchi()
        self._authenticate_concertim(self._config["concertim_username"], self._config["concertim_password"])
        #while True:
        #    self._send_metrics()
        #    time.sleep(self._config["interval"])
        
        #print(concertim_helper.get_concertim_devices(concertimService=self))
        #print(concertim_helper.show_concertim_device(concertimService=self, device_id=6))
        #print(concertim_helper.get_concertim_templates(concertimService=self))
        #print(concertim_helper.create_concertim_device(concertimService=self, device_name="test-device-1", 
        #                                               rack_id=1, start_location_id=30, template_id=2, 
        #                                               device_description="Testing creating from python concertim openstack service", 
        #                                               facing="f"))
        #print(concertim_helper.create_concertim_device(concertimService=self, device_name="test-device-2", 
        #                                               rack_id=1, start_location_id=20, template_id=4, 
        #                                               device_description="Testing creating from python concertim openstack service", 
        #                                               facing="f"))
        #print(concertim_helper.post_metric_to_concertim(concertimService=self, obj_to_update_name="test-device-1",
        #                                                metric_name="os.test.metric", metric_value=5, metric_datatype="int32", metric_slope="both"))
        #print(self._gnocchi.status.get(details=True))
        #print(self._gnocchi.resource.list(sorts=["project_id:desc"]))
        #print(self._gnocchi.metric.list(limit=1))
        self._send_metrics()


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
            self._logger.error("Authentication with CONCERTIM failed: %s", response.text)
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
        query_resource = {"=":{"project_id":"ef821aa9e576420c8768671d911a9766"}}
        resource_list = self._gnocchi.resource.search(resource_type="instance",query=query_resource)
        #print(resource_list)
        metrics = resource_list[0]['metrics']
        vcpus_details = self._gnocchi.metric.get(metric=metrics['cpu'])
        #print(vcpus_details)
        now = datetime.now()
        hour_ago = now - timedelta(hours=1)
        vcpu_amount = self._gnocchi.metric.get_measures(metric=metrics['cpu'], start=hour_ago, stop=now)
        print(vcpu_amount)

        #for resource in resource_list:
        #    for metric in resource['metrics']:
        #        unit = self._gnocchi.metric.get(metric=metrics[metric])['unit']
        #        amount = int(self._gnocchi.metric.get_measures(metric=metrics[metric])[0][2])
        #        print(f"Amount is {amount} for {metric} in {unit}")
        #        if metric == "vcpus":
        #            concertim_helper.post_metric_to_concertim(concertimService=self, obj_to_update_name="test-device-1", 
        #                                                    metric_name="os."+metric, metric_value=amount, metric_datatype="int32", 
        #                                                    metric_slope="zero", metric_units=unit)
        #            print("Sent vcpus metric to test-device-1")

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


