# TODO:
# change 'device' logic to bridge instances in openstack and devices in concertim
# check gnocchi logic

import time
import json
import requests
import logging
import os
import gnocchiclient.v1.client as gnocchi_client
from keystoneauth1 import session
from keystoneauth1.identity import v3


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
        while True:
            self._update_devices()
            self._send_metrics()
            time.sleep(self._config["interval"])

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
        auth_url = self._config["auth_url"]
        auth = v3.Password(auth_url=auth_url,
                           username=self._config["user"],
                           password=self._config["password"],
                           project_name=self._config["project"],
                           user_domain_id="default",
                           project_domain_id="default")
        self._auth = auth        
        
    # Authenticates with the CONCERTIM API and obtains an authentication token
    def _authenticate_concertim(self, login, password):
        base_url = self._config["concertim_url"]
        url = f"{base_url}/users/sign_in.json"
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        data = {"user": {"login": login, "password": password}}
        response = requests.post(url, headers=headers, json=data)
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
            self._logger.error("Failed to authenticate with OpenStack: {}".format(str(e)))
            raise e
        self._logger.info("Authenticated successfully")

    # Updates the devices from the CONCERTIM API
    def _update_devices(self):
        devices = self._config["devices"]
        for device in devices:
            try:
                device_id = device["device_id"]
                response = requests.get(self._config["concertim_url"] + "/" + device_id, headers={"X-Auth-Token": self._auth_token})
                if response.status_code == 200:
                    device_data = response.json()
                    self._devices[device_id] = device_data
                else:
                    self._logger.error("Failed to get device data for device %s", device_id)
            except Exception as e:
                self._logger.error("Failed to update device %s: %s", device_id, e)

    # Sends the metrics for each device to the CONCERTIM API
    def _send_metrics(self):
        for device_id, device_data in self._devices.items():
            metrics = device_data.get("metrics", [])
            if not metrics:
                self._logger.warning("No metrics found for device %s", device_id)
                continue

            try:
                # Build the Gnocchi query to fetch aggregated metric data
                query = {"=": {"device_id": device_id}}
                for metric in metrics:
                    query["="][metric["name"]] = metric.get("filter")

                # Query Gnocchi for aggregated metric data
                metric_data = self._gnocchi.metric.get_measures(
                    metric=metrics[0]["name"],
                    query=query,
                    aggregation=metrics[0].get("aggregation", "mean"),
                    granularity=metrics[0].get("granularity", 300),
                    start="now-1h",
                    stop="now"
                )

                # Convert the metric data to the format expected by the CONCERTIM API
                metric_values = []
                for timestamp, value in metric_data:
                    metric_values.append({"timestamp": timestamp, "value": value})
                metrics_data = {"device_id": device_id, "metrics": [{ "name": metrics[0]["name"], "values": metric_values }]}
                headers = {"X-Auth-Token": self._auth_token, "Content-Type": "application/json"}
                response = requests.post(self._config["concertim_url"], headers=headers, json=metrics_data)

                if response.status_code == 200:
                    self._logger.info("Sent metrics for device %s", device_id)
                else:
                    self._logger.error("Failed to send metrics for device %s: %s", device_id, response.text)
            except Exception as e:
                self._logger.error("Failed to send metrics for device %s: %s", device_id, e)

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

