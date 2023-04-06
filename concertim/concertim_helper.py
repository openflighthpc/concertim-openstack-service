import json
import requests


# Returns the list of templates currently in CONCERTIM
def get_concertim_templates(concertimService):
    base_url = concertimService._config["concertim_url"]
    url = f"{base_url}/api/v1/templates"
    headers = {"Accept": "application/json"}
    if concertimService._auth_token is not None:
        headers["Authorization"] = concertimService._auth_token
    else:
        raise Exception(f"No Authentication Token found in concertimService object - concertimService._auth_token is: {concertimService._auth_token}")
    try:
        response = requests.get(url, headers=headers, verify=False)
        concertimService._logger.info("Retrieved Templates Successfully")
        return response.json()
    except Exception as e:
        concertimService._logger.exception(f"Failed to retrieve templates from CONCERTIM API: {e}")
        raise e
        return

# Returns the list of devices currently in CONCERTIM
def get_concertim_devices(concertimService):
    base_url = concertimService._config["concertim_url"]
    url = f"{base_url}/api/v1/devices"
    headers = {"Accept": "application/json"}
    if concertimService._auth_token is not None:
        headers["Authorization"] = concertimService._auth_token
    else:
        raise Exception(f"No Authentication Token found in concertimService object - concertimService._auth_token is: {concertimService._auth_token}")
    try:
        response = requests.get(url, headers=headers, verify=False)
        concertimService._logger.info("Retrieved Devices Successfully")
        return response.json()
    except Exception as e:
        concertimService._logger.exception(f"Failed to retrieve devices from CONCERTIM API: {e}")
        raise e
        return

# Returns the list of racks currently in CONCERTIM
def get_concertim_racks(concertimService):
    base_url = concertimService._config["concertim_url"]
    url = f"{base_url}/api/v1/racks"
    headers = {"Accept": "application/json"}
    if concertimService._auth_token is not None:
        headers["Authorization"] = concertimService._auth_token
    else:
        raise Exception(f"No Authentication Token found in concertimService object - concertimService._auth_token is: {concertimService._auth_token}")
    try:
        response = requests.get(url, headers=headers, verify=False)
        concertimService._logger.info("Retrieved Racks Successfully")
        return response.json()

    except Exception as e:
        concertimService._logger.exception(f"Failed to retrieve racks from CONCERTIM API: {e}")
        raise e
        return

# Returns the information of a device currently in CONCERTIM based on ID
def show_concertim_device(concertimService, device_id):
    base_url = url
    url = f"{base_url}/api/v1/devices/{device_id}"
    headers = {"Accept": "application/json"}
    if concertimService._auth_token is not None:
        headers["Authorization"] = concertimService._auth_token
    else:
        raise Exception(f"No Authentication Token found in concertimService object - concertimService._auth_token is: {concertimService._auth_token}")
    try:
        response = requests.get(url, headers=headers, verify=False)
        concertimService._logger.info(f"Retrieved Device Information Successfully for device: {device_id}")
        return response.json()
    except Exception as e:
        concertimService._logger.exception(f"Failed to retrieve device information from CONCERTIM API: {e}")
        raise e
        return

# Returns the information of a rack currently in CONCERTIM based on ID
def show_concertim_rack(concertimService, rack_id):
    base_url = concertimService._config["concertim_url"]
    url = f"{base_url}/api/v1/racks/{rack_id}"
    headers = {"Accept": "application/json"}
    if concertimService._auth_token is not None:
        headers["Authorization"] = concertimService._auth_token
    else:
        raise Exception(f"No Authentication Token found in concertimService object - concertimService._auth_token is: {concertimService._auth_token}")
    try:
        response = requests.get(url, headers=headers, verify=False)
        concertimService._logger.info(f"Retrieved Rack Information Successfully for rack: {rack_id}")
        return response.json()

    except Exception as e:
        concertimService._logger.exception(f"Failed to retrieve rack information from CONCERTIM API: {e}")
        raise e
        return

# Gets the template that should be used given the number of instance vcpus
def get_device_template(concertimService, instance_vcpus):
    available_templates = get_concertim_templates(concertimService)
    concertim_template = None
    for template in available_templates:
        if str(f"{instance_vcpus} VCPU") in template['description']:
            concertim_template = template
    if not concertim_template:
        # default to small
        concertim_template = available_templates[1]
    return concertim_template

# Finds an empty spot in the available racks that can fit the new device
def find_spot_in_rack(concertimService, device_template, occupied_rows_all_racks):
    new_rack_id = -1
    start_location = -1
    new_device_size = -1
    spot_found = False
    end_location = -1
    if device_template['name'] == "Small":
        new_device_size=1
    if device_template['name'] == "Medium":
        new_device_size=2
    if device_template['name'] == "Large":
        new_device_size=3
    if device_template['name'] == "Xlarge":
        new_device_size=4
    for rack in occupied_rows_all_racks:
        if spot_found:
            break
        rack_details = show_concertim_rack(concertimService, rack)
        rack_height = rack_details['u_height']
        for rack_row in range(rack_height, 0, -1):
            if (rack_row + new_device_size - 1) <= rack_height and rack_row >= 1:
                fits = True
                for device_space in range(0, new_device_size):
                    row = (rack_row + device_space)
                    if row in occupied_rows_all_racks[rack]:
                        fits = False
                if fits:
                    new_rack_id = rack
                    start_location = rack_row
                    end_location = (rack_row + new_device_size - 1)
                    spot_found= True
                    break
    if spot_found:
        concertimService._logger.info(f"Empty Rack Location found")
        return {"rack_id":new_rack_id, "start_u":start_location, "end_u":end_location}
    else:
        # build new rack
        return

# Build a concertim device from an openstack instance
def build_device_list(concertimService, device_list):
    concertimService._logger.info(f"Building New Devices in Concertim")
    rack_list = get_concertim_racks(concertimService)
    occupied_rows_all_racks = {}
    for rack in rack_list:
        rack_details = show_concertim_rack(concertimService, rack['id'])
        devices = rack_details['devices']
        occupied_rows = []
        for device in devices:
            occupied_rows.extend(list(range(device['location']['start_u'], device['location']['end_u']+1)))
        occupied_rows_all_racks[rack['id']] = occupied_rows
    
    for device in device_list:
        concertimService._logger.info(f"Finding Location for {device[0]}")
        new_device_template = get_device_template(concertimService, device[2])
        new_device_location = find_spot_in_rack(concertimService, new_device_template, occupied_rows_all_racks)
        concertimService._logger.debug(f"Building {device[0]} with template {new_device_template} at location {new_device_location}")
        occupied_rows_all_racks[rack['id']].extend(list(range(new_device_location['start_u'], new_device_location['end_u']+1)))
        create_concertim_device(concertimService, device_name=device[0], rack_id=new_device_location['rack_id'], start_location_id=new_device_location['start_u'], template_id=new_device_template['id'], device_description=device[1], facing='f')

# Create a device in CONCERTIM with the passed args (facing is either f or b for front or back respectively, default will be front)
def create_concertim_device(concertimService, device_name, rack_id, start_location_id, template_id, device_description, facing='f'):
    base_url = concertimService._config["concertim_url"]
    url = f"{base_url}/api/v1/nodes"
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    data = json.dumps({
        "template_id": template_id,
        "device": {
            "name": device_name,
            "description": device_description,
            "location": {
                "facing": facing,
                "rack_id": rack_id,
                "start_u": start_location_id
            }
        }
    })
    if concertimService._auth_token is not None:
        headers["Authorization"] = concertimService._auth_token
    else:
        raise Exception(f"No Authentication Token found in concertimService object - concertimService._auth_token is: {concertimService._auth_token}")
    try:
        response = requests.post(url, headers=headers, data=data, verify=False)
        if response.status_code in (200, 201):
            concertimService._logger.info("New Device Created Successfully")
            return response.json()
        else:
            raise Exception(f"Response returned non 200 or 201 status code: {response.text}")
    except Exception as e:
        concertimService._logger.exception(f"Failed to create new device in CONCERTIM API: {e}")

# Post a metric to concertim for a specific object (rack, device, etc)
#   obj_to_update_name  =   the name of the rack/device/etc in concertim
#   metric_name         =   the name of the metric to put in concertim
#   metric_value        =   value of above metric
#   metric_datatype     =   datatype for the metric_value
#   metric_units        =   units for above metric
#   metric_slope        =   for constant metric slope is "zero"    for metric that changes value slope is "both"
#   metric_ttl          =   not sure, some time thing, ttl default is 3600
def post_metric_to_concertim(concertimService, obj_to_update_name, metric_name, metric_value, metric_datatype, metric_units=" ", metric_slope="both", metric_ttl=3600):
    base_url = concertimService._config["concertim_url"]
    url = f"{base_url}/mrd/{obj_to_update_name}/metrics"
    headers = {"Content-Type": "application/json"}
    data = json.dumps({
        "type": metric_datatype, 
        "name": metric_name, 
        "value": metric_value, 
        "units": metric_units, 
        "slope": metric_slope, 
        "ttl": metric_ttl
    })
    if concertimService._auth_token is not None:
        headers["Authorization"] = concertimService._auth_token
    else:
        raise Exception(f"No Authentication Token found in concertimService object - concertimService._auth_token is: {concertimService._auth_token}")
    try:
        response = requests.put(url, headers=headers, data=data, verify=False)
        concertimService._logger.info(f"Metric Successfully Added: added {metric_name} to {obj_to_update_name}")
        return response.json()
    except Exception as e:
        concertimService._logger.exception(f"Failed to put metric in CONCERTIM: {e}")
        raise e
        return
        