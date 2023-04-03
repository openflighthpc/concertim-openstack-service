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
        raise Exception("No Authentication Token found in concertimService object - concertimService._auth_token is: " + concertimService._auth_token)
    try:
        response = requests.get(url, headers=headers, verify=False)
        concertimService._logger.info("Retrieved Templates Successfully")
        return response.json()
    except Exception as e:
        concertimService._logger.exception("Failed to retrieve templates from CONCERTIM API: ", e)
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
        raise Exception("No Authentication Token found in concertimService object - concertimService._auth_token is: " + concertimService._auth_token)
    try:
        response = requests.get(url, headers=headers, verify=False)
        concertimService._logger.info("Retrieved Devices Successfully")
        return response.json()
    except Exception as e:
        concertimService._logger.exception("Failed to retrieve devices from CONCERTIM API: ", e)
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
        raise Exception("No Authentication Token found in concertimService object - concertimService._auth_token is: " + concertimService._auth_token)
    try:
        response = requests.get(url, headers=headers, verify=False)
        concertimService._logger.info("Retrieved Racks Successfully")
        return response.json()

    except Exception as e:
        concertimService._logger.exception("Failed to retrieve racks from CONCERTIM API: ", e)
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
        raise Exception("No Authentication Token found in concertimService object - concertimService._auth_token is: " + concertimService._auth_token)
    try:
        response = requests.get(url, headers=headers, verify=False)
        concertimService._logger.info("Retrieved Device Information Successfully for device: ", device_id)
        return response.json()
    except Exception as e:
        concertimService._logger.exception("Failed to retrieve device information from CONCERTIM API: ", e)
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
        raise Exception("No Authentication Token found in concertimService object - concertimService._auth_token is: " + concertimService._auth_token)
    try:
        response = requests.get(url, headers=headers, verify=False)
        concertimService._logger.info("Retrieved Rack Information Successfully for rack: ", rack_id)
        return response.json()

    except Exception as e:
        concertimService._logger.exception("Failed to retrieve rack information from CONCERTIM API: ", e)
        raise e
        return

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
        raise Exception("No Authentication Token found in concertimService object - concertimService._auth_token is: " + concertimService._auth_token)
    try:
        response = requests.post(url, headers=headers, data=data, verify=False)
        if response.status_code in (200, 201):
            concertimService._logger.info("New Device Created Successfully")
            return response.json()
        else:
            raise Exception("Response returned non 200 or 201 status code: ", response.text)
    except Exception as e:
        concertimService._logger.exception("Failed to create new device in CONCERTIM API: ", e)

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
        raise Exception("No Authentication Token found in concertimService object - concertimService._auth_token is: ", concertimService._auth_token)
    try:
        response = requests.put(url, headers=headers, data=data, verify=False)
        concertimService._logger.info(f"Metric Successfully Added: added {metric_name} to {obj_to_update_name}")
        return response.json()
    except Exception as e:
        concertimService._logger.exception("Failed to put metric in CONCERTIM: ", e)
        raise e
        return
        