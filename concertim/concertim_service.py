# The Main Openstack -> Concertim service that send openstack data to concertim

# Python packages
import json
import time
from datetime import datetime, timedelta
import logging
import os
import traceback

# Disable insecure warnings  
import requests
requests.packages.urllib3.disable_warnings() 

# Local imports
import concertim_helper

# Openstack packages
from keystoneauth1 import session
from keystoneauth1.identity import v3
import keystoneclient.v3.client as keystone_client
import gnocchiclient.v1.client as gnocchi_client


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
        self._keystone = None
        self._auth_token = None

    # If 'run' is for prod scenarios, this is for unit testing 
    def test(self):
        self._authenticate_openstack()
        self._connect_gnocchi()
        self._conncet_keystone()
        self._authenticate_concertim(self._config["concertim_username"], self._config["concertim_password"])
        #print(concertim_helper.create_concertim_device(concertimService=self, device_name="concertim-instance-4", rack_id=1, start_location_id=38, template_id=5, device_description="Made UP instance", facing="f"))
        print(concertim_helper.get_concertim_templates(concertimService=self))
        #print(concertim_helper.delete_rack(concertimService=self, rack_id='8', full_delete=True))
        #print(concertim_helper.get_curr_concertim_user(concertimService=self))
        #print(concertim_helper.get_concertim_accounts(concertimService=self))


        # IN WHILE LOOP
        #os_project_list = self._get_project_list()
        #concertim_accounts = concertim_helper.get_concertim_accounts(concertimService=self)
        #delimiter = '-'
        #missing_accounts = self._get_missing(os_projects=os_project_list, con_accounts=concertim_accounts, delimiter=delimiter)
        #all_accounts = None
        all_accounts = ['ef821aa9e576420c8768671d911a9766']
        
        #if len(missing_accounts) != 0:
            # handle missing accounts

        for project in all_accounts:
            self._update_concertim(project_id=project)
            self._send_metrics(project_id=project)

    # Runs the main service loop
    def run(self):
        self._authenticate_openstack()
        self._connect_gnocchi()
        self._conncet_keystone()
        self._authenticate_concertim(self._config["concertim_username"], self._config["concertim_password"])
        while True:
            os_project_list = self._get_project_list()
            for project in os_project_list:
                self._update_concertim(project_id=project)
                self._send_metrics(project_id=project)
            time.sleep(300)

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
                self._log('I', "Authenticated with CONCERTIM successfully")
            else:
                self._log('EX', "Failed to obtain auth token from CONCERTIM API")
                raise Exception("Failed to obtain auth token from CONCERTIM API")
        else:
            self._log('EX', f"Authentication with CONCERTIM failed: {response}")
            raise Exception("Authentication with CONCERTIM failed")

    # Connects to the Gnocchi API
    def _connect_gnocchi(self):
        sess = session.Session(auth=self._auth)
        try:
            gnocchi = gnocchi_client.Client(session=sess)
            self._gnocchi = gnocchi
        except Exception as e:
            self._log('EX', f"Failed to authenticate Gnocchi with OpenStack: {e}")
            raise e
        self._log('I', "Authenticated and connected Gnocchi successfully")

    # Conncets to the Keystone API
    def _conncet_keystone(self):
        sess = session.Session(auth=self._auth)
        try:
            keystone = keystone_client.Client(session=sess)
            self._keystone = keystone
        except Exception as e:
            self._log('ER', f"Failed to authenticate with Keystone: {e}")
            raise e
        self._log('I', "Authenticated and connected to Keystone successfully")

    # Return the list of all project_ids in Openstack
    def _get_project_list(self):
        os_project_list = self._keystone.projects.list()
        project_list = []
        for project in os_project_list:
            project_list.append(project.id)
        return project_list

    # Sends the metrics for each device to the CONCERTIM API
    def _send_metrics(self, project_id):
        self._log('I', f"Begin Sending Metrics for Project: {project_id}")
        project_query = {"and": [{"=":{"project_id":project_id}}, {"=":{"ended_at":None}}]}
        openstack_resources_list = self._gnocchi.resource.search(query=project_query, details=True)
        sorted_resource_list = self._sort_resource_list(resource_list=openstack_resources_list)

        for openstack_instance in sorted_resource_list:
            self._process_instance(instance_dict=sorted_resource_list[openstack_instance])

    # Sort Openstack project resources and group by instance_id
    def _sort_resource_list(self, resource_list):
        grouped_resources = {}
        for resource in resource_list:
            display_name = None
            if "instance_id" in resource:
                instance_id = resource["instance_id"]
            elif "id" in resource and resource["type"] == "instance":
                instance_id = resource["id"]
                display_name = resource["display_name"]
            else:
                continue
            if instance_id not in grouped_resources:
                grouped_resources[instance_id] = {"display_name":None,"resources":[]}
            if display_name is not None:
                grouped_resources[instance_id]["display_name"] = display_name
            grouped_resources[instance_id]["resources"].append(resource)
        return grouped_resources

    # Return a dictionary of missing accounts and where they are missing from
    # store missing accounts as {'acct_id': 'concertim|openstack'} 
    # will use the app it is missing FROM
    def _get_missing(self, os_projects, con_accounts, delimiter):
        con_acct_projects = [acct['fullname'].split(delimiter)[1] for acct in con_accounts]
        missing_accounts = {}
        for proj_id in os_projects:
            if proj_id not in con_acct_projects:
                missing_accounts[proj_id] = 'concertim'
        for proj_id in con_acct_projects:
            if proj_id not in os_projects:
                missing_accounts[proj_id] = 'openstack'
        return missing_accounts

    # Process an openstack instance's resources and send them to Concertim
    def _process_instance(self, instance_dict):
        # 10 minute window starting from 1 and 10 min ago to 1 hour ago
        stop = datetime.now() - timedelta(minutes=60)
        start = stop - timedelta(minutes=10)

        for resource in instance_dict["resources"]:
            # Metric Fetching based on resource
            if resource["type"] == "instance":
                # CPU Load as a percent
                self._post_cpu_load(resource=resource, display_name=instance_dict["display_name"].split('-',1)[1], start=start, stop=stop)
                # RAM Usage as a percent
                self._post_ram_usage(resource=resource, display_name=instance_dict["display_name"].split('-',1)[1], start=start, stop=stop)
            elif resource["type"] == "instance_network_interface":
                # Network usgae in bytes/s
                self._post_network_usage(resource=resource, display_name=instance_dict["display_name"].split('-',1)[1], start=start, stop=stop)
            elif resource["type"] == "instance_disk":
                # Throughput in bytes/s
                self._post_throughput(resource=resource, display_name=instance_dict["display_name"].split('-',1)[1], start=start, stop=stop)
                # IOPs in Ops/s
                self._post_iops(resource=resource, display_name=instance_dict["display_name"].split('-',1)[1], start=start, stop=stop)

    # Check openstack to see if there are any new instances and update concertim if there are
    def _update_concertim(self, project_id):
        project_query = {"and": [{"=":{"project_id":project_id}}, {"=":{"ended_at":None}}]}

        openstack_instance_list = self._gnocchi.resource.search(resource_type="instance", query=project_query, details=True)
        concertim_device_list = concertim_helper.get_concertim_devices(concertimService=self)
        concertim_rack_list = concertim_helper.get_concertim_racks(concertimService=self)
        new_device_list = []

        # THIS BLOCK NEEDS REWORK: 
        # not very robust
        for instance in openstack_instance_list:
            concertim_device_found = [d for d in concertim_device_list if d['name'] == instance["display_name"].split('-',1)[1]]
            if not concertim_device_found:
                self._log('I', f"New Instance Found in Openstack - {instance['display_name']}")
                instance_vcpus = self._gnocchi.metric.get_measures(metric=instance["metrics"]["vcpus"])[0][2]
                new_device_list.append((instance["display_name"], instance["id"], instance_vcpus))
        ###

        if len(new_device_list) == 0:
            self._log('I', f"All Openstack Instances are present in Concertim")
            return

        # Build all new devices found for project
        concertim_helper.build_device_list(self,new_device_list)

    # Post CPU Load as a Percent to Concertim for a given resource and date range
    def _post_cpu_load(self, resource, display_name, start, stop):
        self._log('I', f"Calculating CPU Load for {display_name}")
        cpu_metric_id = resource['metrics']['cpu']
        ns_to_s_granularity = int(self._config["ceilometer_granularity"]) * 1000000000.0
        cpu_load_percent = self._gnocchi.aggregates.fetch(operations=f"(* (/ (aggregate rate:mean (metric {cpu_metric_id} mean)) {ns_to_s_granularity}) 100)", 
                                                          resource_type="instance", start=start, stop=stop)["measures"]["aggregated"][0][2]
        self._log('D', f"Sending CPU Load = {cpu_load_percent} to instance {resource['id']} ({display_name})")
        concertim_helper.post_metric_to_concertim(concertimService=self, obj_to_update_name=display_name, metric_name=f"os.instance.cpu_utilization", 
                                                    metric_value=cpu_load_percent, metric_datatype="float", metric_slope="both", metric_units="%")
    
    # Post RAM Usage as as Percent to Concertim for a given resource and date range
    def _post_ram_usage(self, resource, display_name, start, stop):
        self._log('I', f"Calculating RAM Usage for {display_name}")
        memory_metric_id = resource['metrics']['memory']
        memory = self._gnocchi.metric.get_measures(metric=memory_metric_id, limit=1)[0][2]
        memory_usage_metric_id = resource['metrics']['memory.usage']
        memory_usage = self._gnocchi.metric.get_measures(metric=memory_usage_metric_id, start=start, stop=stop)[0][2]
        ram_usage_percent = memory_usage/memory*100
        self._log('D', f"Sending RAM Usage = {ram_usage_percent} to instance {resource['id']} ({display_name})")
        concertim_helper.post_metric_to_concertim(concertimService=self, obj_to_update_name=display_name, metric_name=f"os.instance.ram_usage", 
                                                    metric_value=ram_usage_percent, metric_datatype="float", metric_slope="both", metric_units="%")
    
    # Post average throughput in byte/s for the given resource and date range
    def _post_throughput(self, resource, display_name, start, stop):
        self._log('I', f"Calculating Throughput for {display_name}")
        disk_read_metric = resource['metrics']['disk.device.read.bytes']
        disk_write_metric = resource['metrics']['disk.device.write.bytes']
        disk_read_measure = self._gnocchi.metric.get_measures(metric=disk_read_metric, aggregation="rate:mean", start=start, stop=stop)[0][2]
        disk_write_measure = self._gnocchi.metric.get_measures(metric=disk_write_metric, aggregation="rate:mean", start=start, stop=stop)[0][2]
        throughput = (disk_write_measure + disk_read_measure) / int(self._config["ceilometer_granularity"])
        self._log('D', f"Sending Throughput = {throughput} to instance {resource['id']} ({display_name})")
        concertim_helper.post_metric_to_concertim(concertimService=self, obj_to_update_name=display_name, metric_name=f"os.disk.avg_throughput", 
                                                    metric_value=throughput, metric_datatype="float", metric_slope="both", metric_units="B/s")

    # Post average IOPs in Ops/s for the given resource and date range
    def _post_iops(self, resource, display_name, start, stop):
        self._log('I', f"Calculating IOPs for {display_name}")
        disk_read_metric = resource['metrics']['disk.device.read.requests']
        disk_write_metric = resource['metrics']['disk.device.write.requests']
        disk_read_measure = self._gnocchi.metric.get_measures(metric=disk_read_metric, aggregation="rate:mean", start=start, stop=stop)[0][2]
        disk_write_measure = self._gnocchi.metric.get_measures(metric=disk_write_metric, aggregation="rate:mean", start=start, stop=stop)[0][2]
        iops = (disk_write_measure + disk_read_measure) / int(self._config["ceilometer_granularity"])
        self._log('D', f"Sending IOPs = {iops} to instance {resource['id']} ({display_name})")
        concertim_helper.post_metric_to_concertim(concertimService=self, obj_to_update_name=display_name, metric_name=f"os.disk.avg_iops", 
                                                    metric_value=iops, metric_datatype="float", metric_slope="both", metric_units="Ops/s")

    # Post average network usage in B/s for the given resource and date range
    def _post_network_usage(self, resource, display_name, start, stop):
        self._log('I', f"Calculating Network Usage for {display_name}")
        net_in_metric = resource['metrics']['network.incoming.bytes']
        net_out_metric = resource['metrics']['network.outgoing.bytes']
        net_in_measure = self._gnocchi.metric.get_measures(metric=net_in_metric, aggregation="rate:mean", start=start, stop=stop)[0][2]
        net_out_measure = self._gnocchi.metric.get_measures(metric=net_out_metric, aggregation="rate:mean", start=start, stop=stop)[0][2]
        usage_rate = (net_in_measure + net_out_measure) / int(self._config["ceilometer_granularity"])
        self._log('D', f"Sending Network Usage = {usage_rate} to instance {resource['id']} ({display_name})")
        concertim_helper.post_metric_to_concertim(concertimService=self, obj_to_update_name=display_name, metric_name=f"os.net.avg_usage", 
                                                    metric_value=usage_rate, metric_datatype="float", metric_slope="both", metric_units="B/s")

    # Logging helper method - logs at specified level but indents to show current depth
    def _log(self, level, message):
        indentation_level = len(traceback.extract_stack()) - 4
        if any([info in level for info in ['I', 'i','info', 'INFO', 'Info']]):
            self._logger.info(('{i} {m}'.format(i = '  ' * indentation_level, m=message)))
        elif any([debug in level for debug in ['D', 'd', 'debug', 'DEBUG', 'Debug']]):
            self._logger.debug(('{i} {m}'.format(i = '  ' * indentation_level, m=message)))
        elif any([error in level for error in ['er', 'ER', 'error', 'ERROR', 'Error']]):
            self._logger.error(('{i} {m}'.format(i = '  ' * indentation_level, m=message)))
        elif any([exc in level for exc in ['ex', 'EX', 'exception', 'EXCEPTION', 'Exception', 'EXC', 'Exc', 'exc']]):
            self._logger.exception(('{i} {m}'.format(i = '  ' * indentation_level, m=message)))
        else:
            self._logger.log(level=level, msg=('{i} {m}'.format(i = '  ' * indentation_level, m=message)))

    # Starts the service
    def start(self):
        self._log('I', "Starting the Concertim Service")
        try:
            #self.run()
            self.test()
            self.stop()
        except Exception as e:
            self._log('EX', e)
            self.stop()

    # Stops the service
    def stop(self):
        self._log('I', "Stopping the Concertim service")
        # clean up resources if needed
        raise SystemExit


