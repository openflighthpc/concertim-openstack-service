# This File contains helper methods to intereact with the Concertim REST API

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
        concertimService._log('I', "Retrieved Templates Successfully")
        return response.json()
    except Exception as e:
        concertimService._log('EX', f"Failed to retrieve templates from CONCERTIM API: {e}")
        raise e
        return

# Returns a list of the concertim accounts
def get_concertim_accounts(concertimService):
    base_url = concertimService._config["concertim_url"]
    url = f"{base_url}/api/v1/users"
    headers = {"Accept": "application/json"}
    if concertimService._auth_token is not None:
        headers["Authorization"] = concertimService._auth_token
    else:
        raise Exception(f"No Authentication Token found in concertimService object - concertimService._auth_token is: {concertimService._auth_token}")
    try:
        response = requests.get(url, headers=headers, verify=False)
        concertimService._log('I', "Retrieved Current User Successfully")
        return response.json()
    except Exception as e:
        concertimService._log('EX', f"Failed to retrieve templates from CONCERTIM API: {e}")
        raise e
        return

# Return the current user for concertim
def get_curr_concertim_user(concertimService):
    base_url = concertimService._config["concertim_url"]
    url = f"{base_url}/api/v1/users/current"
    headers = {"Accept": "application/json"}
    if concertimService._auth_token is not None:
        headers["Authorization"] = concertimService._auth_token
    else:
        raise Exception(f"No Authentication Token found in concertimService object - concertimService._auth_token is: {concertimService._auth_token}")
    try:
        response = requests.get(url, headers=headers, verify=False)
        concertimService._log('I', "Retrieved Current User Successfully")
        return response.json()
    except Exception as e:
        concertimService._log('EX', f"Failed to retrieve templates from CONCERTIM API: {e}")
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
        concertimService._log('I', "Retrieved Devices Successfully")
        return response.json()
    except Exception as e:
        concertimService._log('EX', f"Failed to retrieve devices from CONCERTIM API: {e}")
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
        concertimService._log('I', "Retrieved Racks Successfully")
        return response.json()

    except Exception as e:
        concertimService._log('EX', f"Failed to retrieve racks from CONCERTIM API: {e}")
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
        concertimService._log('I', f"Retrieved Device Information Successfully for device: {device_id}")
        return response.json()
    except Exception as e:
        concertimService._log('EX', f"Failed to retrieve device information from CONCERTIM API: {e}")
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
        concertimService._log('I', f"Retrieved Rack Information Successfully for rack: {rack_id}")
        return response.json()

    except Exception as e:
        concertimService._log('EX', f"Failed to retrieve rack information from CONCERTIM API: {e}")
        raise e
        return

# Moves a concertim device to a different rack location and/or orientation
def move_device(concertimService, device_id, rack_id, start_location_id, facing='f'):
    base_url = concertimService._config["concertim_url"]
    url = f"{base_url}/devices/{device_id}"
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    data = json.dumps({
                "device": {
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
        response = requests.patch(url, headers=headers, data=data, verify=False)
        if response.status_code in (200, 201):
            concertimService._log('I', "Device Moved Successfully")
            return response.json()
        else:
            raise Exception(f"Response returned non 200 or 201 status code: {response.text}")
    except Exception as e:
        concertimService._log('EX', f"Failed to move device in CONCERTIM API: {e}")
    
# Updates a device in concertim with either a new desc, a new name, or both
def update_device(concertimService, device_id, current_device_name, current_device_desc, new_device_name="", new_device_desc=""):
    device_name = None
    device_desc = ""
    if new_device_name == "":
        device_name = current_device_name
    else:
        device_name = new_device_name
    if new_device_desc != "":
        device_desc = new_device_desc
    else:
        device_desc = current_device_desc
    
    base_url = concertimService._config["concertim_url"]
    url = f"{base_url}/api/v1/devices/{device_id}"
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    data = json.dumps({
                        "device": {
                            "name": device_name,
                            "description": device_desc
                        }
                    })
    if concertimService._auth_token is not None:
        headers["Authorization"] = concertimService._auth_token
    else:
        raise Exception(f"No Authentication Token found in concertimService object - concertimService._auth_token is: {concertimService._auth_token}")
    
    try:
        response = requests.patch(url, headers=headers, data=data, verify=False)
        if response.status_code in (200, 201):
            concertimService._log('I', "Device Updated Successfully")
            return response.json()
        else:
            raise Exception(f"Response returned non 200 or 201 status code: {response.text}")
    except Exception as e:
        concertimService._log('EX', f"Failed to update device in CONCERTIM API: {e}")

# Updates a rack in concertim with either a new height, a new name, or both
def update_rack(concertimService, rack_id, current_rack_name, new_rack_name="", new_rack_height=0):
    rack_name = None
    rack_height = 0
    if new_rack_name == "":
        rack_name = current_rack_name
    else:
        rack_name = new_rack_name
    if new_rack_height != 0:
        rack_height = new_rack_height
    
    base_url = concertimService._config["concertim_url"]
    url = f"{base_url}/api/v1/racks/{rack_id}"
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    data = json.dumps({
                        "rack": {
                            "name": rack_name,
                            "u_height": rack_height
                        }
                    })
    if concertimService._auth_token is not None:
        headers["Authorization"] = concertimService._auth_token
    else:
        raise Exception(f"No Authentication Token found in concertimService object - concertimService._auth_token is: {concertimService._auth_token}")
    
    try:
        response = requests.patch(url, headers=headers, data=data, verify=False)
        if response.status_code in (200, 201):
            concertimService._log('I', "Rack Updated Successfully")
            return response.json()
        else:
            raise Exception(f"Response returned non 200 or 201 status code: {response.text}")
    except Exception as e:
        concertimService._log('EX', f"Failed to update rack in CONCERTIM API: {e}")
    
# Gets the template that should be used given the number of instance vcpus
def get_device_template(concertimService, instance_vcpus):
    available_templates = get_concertim_templates(concertimService)
    concertim_template = None
    size = 1
    # default to small
    for template in available_templates:
        if template['name'] == "Small":
            concertim_template = template
    
    for template in available_templates:
        if str(f"{instance_vcpus} VCPU") in template['description']:
            concertim_template = template
    if concertim_template['name'] == "Small":
        size=1
    if concertim_template['name'] == "Medium":
        size=2
    if concertim_template['name'] == "Large":
        size=3
    if concertim_template['name'] == "Xlarge":
        size=4
    return {"template": concertim_template, "size": size}

# Finds an empty spot in the available racks that can fit the new device
def find_spot_in_rack(concertimService, device_template, rack_state):
    rack_id = rack_state['id']
    start_location = -1
    spot_found = False
    end_location = -1
    new_device_size = device_template['size']

    rack_details = show_concertim_rack(concertimService, rack_state['id'])
    rack_height = rack_details['u_height']
    for rack_row in range(rack_height, 0, -1):
        if (rack_row + new_device_size - 1) <= rack_height and rack_row >= 1:
            fits = True
            for device_space in range(0, new_device_size):
                row = (rack_row + device_space)
                if row in rack_state['occupied']:
                    fits = False
            if fits:
                start_location = rack_row
                end_location = (rack_row + new_device_size - 1)
                spot_found= True

    if spot_found:
        concertimService._log('I', f"Empty Rack Location found")
        return {"rack_id": rack_id, "start_u":start_location, "end_u":end_location}
    else:
        concertimService._log('I', f"No Empty Rack Location found - Resizing Rack")
        update_rack(concertimService, rack_id, rack_state['name'], new_rack_height=int(rack_height + device_template['size']))
        return find_spot_in_rack(concertimService, device_template, rack_state)

# Returns a list of all occupied row_ids for a given rack
def get_rack_state(concertimService, rack_id):
    rack_details = show_concertim_rack(concertimService, rack_id)
    devices = rack_details['devices']
    occupied_rows = []
    for device in devices:
        occupied_rows.extend(list(range(device['location']['start_u'], device['location']['end_u']+1)))
    return {"name": rack_details['name'], "id": rack_details['id'], "occupied": occupied_rows}

# Builds all concertim devices from given openstack instances
def build_device_list(concertimService, device_list):
    concertimService._log('I', f"Building New Devices in Concertim")
    rack_list = get_concertim_racks(concertimService)
    
    for device in device_list:
        cluster_name = device[0].split('-', 1)[0]
        device_name = device[0].split('-', 1)[1]
        cluster_rack_exists = False
        rack_state = None
        new_device_template = get_device_template(concertimService, device[2])
        concertimService._log('I', f"Finding Location for {device[0]}")
        for rack in rack_list:
            if rack['name'] == cluster_name:
                concertimService._log('I', f"Found Existing Rack '{rack['name']}' for Cluster '{cluster_name}'")
                cluster_rack_exists = True
                rack_state = get_rack_state(concertimService, rack['id'])
        if not cluster_rack_exists:
            concertimService._log('I', f"No Existing Rack Found for Cluster '{cluster_name}' - Creating new Rack")
            new_rack = create_concertim_rack(concertimService, rack_name=cluster_name, rack_height=new_device_template['size'])
            rack_state = {"name": new_rack['name'], "id": new_rack['id'], "occupied":[]}
            rack_list.append(new_rack)
        new_device_location = find_spot_in_rack(concertimService, new_device_template, rack_state)
        concertimService._log('D', f"Building {device_name} with {new_device_template} at location {new_device_location}")
        create_concertim_device(concertimService, device_name=device_name, rack_id=new_device_location['rack_id'], start_location_id=new_device_location['start_u'], template_id=new_device_template['template']['id'], device_description=device[1], facing='f')

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
            concertimService._log('I', "New Device Created Successfully")
            return response.json()
        else:
            raise Exception(f"Response returned non 200 or 201 status code: {response.text}")
    except Exception as e:
        concertimService._log('EX', f"Failed to create new device in CONCERTIM API: {e}")

# Create a rack in CONCERTIM with the passed args
def create_concertim_rack(concertimService, rack_name, rack_height):
    base_url = concertimService._config["concertim_url"]
    url = f"{base_url}/api/v1/racks"
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    data = json.dumps({
                "name": rack_name,
                "u_height": rack_height
            })
    if concertimService._auth_token is not None:
        headers["Authorization"] = concertimService._auth_token
    else:
        raise Exception(f"No Authentication Token found in concertimService object - concertimService._auth_token is: {concertimService._auth_token}")
    try:
        response = requests.post(url, headers=headers, data=data, verify=False)
        if response.status_code in (200, 201):
            concertimService._log('I', "New Rack Created Successfully")
            return response.json()
        else:
            raise Exception(f"Response returned non 200 or 201 status code: {response.text}")
    except Exception as e:
        concertimService._log('EX', f"Failed to create new rack in CONCERTIM API: {e}")

# Delete a given device in Concertim
def delete_device(concertimService, device_id):
    base_url = concertimService._config["concertim_url"]
    url = f"{base_url}/api/v1/devices/{device_id}"
    headers = {"Accept": "application/json"}
    if concertimService._auth_token is not None:
        headers["Authorization"] = concertimService._auth_token
    else:
        raise Exception(f"No Authentication Token found in concertimService object - concertimService._auth_token is: {concertimService._auth_token}")
    try:
        response = requests.delete(url, headers=headers, verify=False)
        concertimService._log('I', "Device Successfully Deleted")
        return response.json()
    except Exception as e:
        concertimService._log('EX', f"Failed to delete device in CONCERTIM API: {e}")

# Delete a given rack in Concertim
def delete_rack(concertimService, rack_id, full_delete=False):
    base_url = concertimService._config["concertim_url"]
    url = f"{base_url}/api/v1/racks/{rack_id}"
    headers = {"Accept": "application/json"}
    rack_devices = show_concertim_rack(concertimService, rack_id)['devices']
    # Check if the rack is empty and if we should delete the devices in non-empty rack
    if len(rack_devices) is not 0 and not full_delete:
        concertimService._logger.error(f"Attempting to delete a non-empty rack: {rack_id} - delete devices or add full_delete=true")
    else:
         url = f"{url}?recurse=true"
    if concertimService._auth_token is not None:
        headers["Authorization"] = concertimService._auth_token
    else:
        raise Exception(f"No Authentication Token found in concertimService object - concertimService._auth_token is: {concertimService._auth_token}")
    try:
        response = requests.delete(url, headers=headers, verify=False)
        concertimService._log('I', "Rack Successfully Deleted")
        return response.json()
    except Exception as e:
        concertimService._log('EX', f"Failed to delete rack in CONCERTIM API: {e}")

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
        concertimService._log('I', f"Metric Successfully Added: added {metric_name} to {obj_to_update_name}")
        return response.json()
    except Exception as e:
        concertimService._log('EX', f"Failed to put metric in CONCERTIM: {e}")
        raise e
        return
        