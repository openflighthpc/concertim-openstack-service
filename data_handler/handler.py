# Local Imports
from utils.service_logger import create_logger
# concertim component objects
from concertim.components.device import ConcertimDevice
from concertim.components.rack import ConcertimRack
from concertim.components.template import ConcertimTemplate
from concertim.components.user import ConcertimUser

# Py Packages
import time
from datetime import datetime, timedelta
import sys

class DataHandler(object):
    def __init__(self, openstack, concertim, config_obj):
        self.__LOGGER = create_logger(__name__, '/var/log/concertim-openstack-service-opt.log', config_obj['log_level'])
        self.openstack_service = openstack
        self.concertim_service = concertim
        self.projects = []
        self.users = {}
        self.devices_racks = {}
        self.templates = {}
        self.__current_templates = []
        self.__current_racks = []
        self.__current_devices = []

    def send_metrics(self):
        self.__LOGGER.info('Sending Metrics')
        for project_id in self.devices_racks:
            resources = self.openstack_service.get_project_resources(project_id)
            for rack_id in self.devices_racks[project_id]:
                for instance_id in self.devices_racks[project_id][rack_id]['devices']:
                    self.handle_metrics(resources[instance_id])

    def update_concertim(self):
        self.__LOGGER.info('Updating Concertim')
        #print(self.concertim_service.list_templates())
        # Update Lists
        self.__update_projects_list() # Finished
        self.__update_users_dict() # Finished
        self.__update_templates_dict() # Finished
        self.__update_devices_racks_dict() # Finished

    def handle_metrics(self, instance_resource_dict):
        self.__LOGGER.debug(f"Processing metrics for instance:{instance_resource_dict['display_name']}")
        # 10 minute window starting from 1 and 10 min ago to 1 hour ago
        stop = datetime.now() - timedelta(minutes=60)
        start = stop - timedelta(minutes=1)

        for resource in instance_resource_dict["resources"]:
            # Metric Fetching based on resource
            if resource["type"] == "instance":
                # CPU Load as a percent
                cpu_load = self.openstack_service.get_cpu_load(resource, start, stop)
                self.concertim_service.send_metric(instance_resource_dict["display_name"], {'type': "double",'name': "os.instance.cpu_utilization",'value': cpu_load,'units': '%','slope': "both",'ttl': 3600})
                # RAM Usage as a percent
                ram_usage = self.openstack_service.get_ram_usage(resource, start, stop)
                self.concertim_service.send_metric(instance_resource_dict["display_name"], {'type': "double",'name': "os.instance.ram_usage",'value': ram_usage,'units': '%','slope': "both",'ttl': 3600})
            elif resource["type"] == "instance_network_interface":
                # Network usgae in bytes/s
                network_usage = self.openstack_service.get_network_usage(resource, start, stop)
                self.concertim_service.send_metric(instance_resource_dict["display_name"], {'type': "double",'name': "os.net.avg_usage",'value': network_usage,'units': 'B/s','slope': "both",'ttl': 3600})
            elif resource["type"] == "instance_disk":
                # Throughput in bytes/s
                throughput = self.openstack_service.get_throughput(resource, start, stop)
                self.concertim_service.send_metric(instance_resource_dict["display_name"], {'type': "double",'name': "os.disk.avg_throughput",'value': throughput,'units': 'B/s','slope': "both",'ttl': 3600})
                # IOPs in Ops/s
                iops = self.openstack_service.get_iops(resource, start, stop)
                self.concertim_service.send_metric(instance_resource_dict["display_name"], {'type': "double",'name': "os.disk.avg_iops",'value': iops,'units': 'Ops/s','slope': "both",'ttl': 3600})
        
    def __update_projects_list(self):
        updated_projects_list = self.openstack_service.get_concertim_projects()
        new_projects = list(set(updated_projects_list) - set(self.projects))
        if new_projects:
            self.__LOGGER.debug(f"New Openstack project(s) to manage found : {new_projects}")
        removed_projects = list(set(self.projects) - set(updated_projects_list))
        if removed_projects:
            self.__LOGGER.warning(f"Managed Project(s) have been deleted : {removed_projects}")
        self.projects = updated_projects_list
    
    def __update_users_dict(self):
        updated_user_list = self.concertim_service.list_users()
        for user in updated_user_list:
            if user['login'] == "admin" or str(user['id']) in self.users:
                continue
            self.__LOGGER.debug(f"New User found - creating User(ID: {user['id']}, project_id: {user['project_id']}, name: {user['name']}, login: {user['login']})")
            self.users[str(user['id'])] = ConcertimUser(str(user['id']),
                                                    user['project_id'],
                                                    user['name'],
                                                    user['login'])

    def __update_templates_dict(self):
        openstack_flavors = self.openstack_service.get_flavors()
        for flavor in openstack_flavors:
            if openstack_flavors[flavor]['id'] in self.templates:
                continue
            if openstack_flavors[flavor]['vcpus'] <= 1:
                size = 1
            elif openstack_flavors[flavor]['vcpus'] <= 2:
                size = 2
            elif openstack_flavors[flavor]['vcpus'] <= 4:
                size = 3
            else:
                size = 4
            description = f"{openstack_flavors[flavor]['name']} - {openstack_flavors[flavor]['ram']}MB RAM, {openstack_flavors[flavor]['disk']}GB disk, {openstack_flavors[flavor]['vcpus']} vCPU"
            self.__LOGGER.debug(f"New Flavor found - creating template(name: {openstack_flavors[flavor]['name']}, description: '{description}', size: {size})")
            template = ConcertimTemplate(openstack_flavors[flavor]['id'],
                                    openstack_flavors[flavor]['name'],
                                    openstack_flavors[flavor]['ram'],
                                    openstack_flavors[flavor]['disk'],
                                    openstack_flavors[flavor]['vcpus'],
                                    device_size=size)
            temp_in_con = None
            # try to create the new template in concertim
            # if there is a conflict, pull from concertim and check
            # if there is still no template, raise e
            try:
                temp_in_con = self.concertim_service.create_template({'name': openstack_flavors[flavor]['id'], 'description': description, 'height': size})
            except FileExistsError as e:
                self.__LOGGER.warning(f"The template '{template.flavor_id}' already exists. Searching concertim for the template.")
                temp_in_con = self.__search_local_templates(template)
                if not temp_in_con:
                    self.__LOGGER.exception(f"No template found after updating - please check concertim and restart process.")
                    raise SystemExit(e)
            except Exception as e:
                self.__LOGGER.exception(f"Unhandled Exception {e}")
                raise SystemExit(e)
            finally:
                template.template_id = temp_in_con['id']
                self.templates[openstack_flavors[flavor]['id']] = template

    def __update_devices_racks_dict(self):
        for project in self.projects:
            if project not in self.devices_racks:
                self.devices_racks[project] = {}
            openstack_instances = self.openstack_service.get_instances(project)
            for instance in openstack_instances:
                name_split = instance.name.split('.')
                if name_split[1] not in self.devices_racks[project]:
                    self.devices_racks[project][name_split[1]] = {'rack': None, 'devices': {}}
                    rack = self.__build_rack(instance)
                    self.devices_racks[project][name_split[1]]['rack'] = rack
                if instance.id not in self.devices_racks[project][name_split[1]]['devices']:
                    device = self.__build_device(instance)
                    self.devices_racks[project][name_split[1]]['devices'][instance.id] = device
                    self.devices_racks[project][name_split[1]]['rack'].devices.append(device)
    
    def __build_rack(self, instance):
        cluster_name = instance.name.split('.')[1]
        rack_name = cluster_name + '-' + instance.tenant_id[:5]
        height = 20
        owner = None
        for user_id in self.users:
            if self.users[user_id].project_id != instance.tenant_id:
                continue
            owner = self.users[user_id]
        self.__LOGGER.debug(f"New Cluster Found - Building new Rack(name: {rack_name}, owner: {owner.display_name}, height: {height})")
        rack = ConcertimRack(rack_name, owner, height, cluster_name, instance.tenant_id)
        rack_in_con = None
        rack_in_con_details = None
        rack_in_con_details_needed = False
        # try to create the new rack in concertim
        # if there is a conflict, pull from concertim and check
        # if there is still no rack, raise e
        try:
            rack_in_con = self.concertim_service.create_rack({'user_id': owner.user_id, 'name': rack_name, 'u_height': height})
        except FileExistsError as e:
            self.__LOGGER.warning(f"The rack '{rack_name}' already exists. Searching for rack.")
            rack_in_con = self.__search_local_racks(rack)
            if rack_in_con is not None:
                rack_in_con_details_needed = True
            else:
                self.__LOGGER.exception(f"No usable rack found after seaching - please check concertim and restart process.")
                raise SystemExit(e)
        except Exception as e:
            self.__LOGGER.exception(f"Unhandled Exception {e}")
            raise SystemExit(e)
        finally:
            rack.rack_id = rack_in_con['id']
            if rack_in_con_details_needed:
                self.__LOGGER.debug(f"Getting {rack_in_con['name']} details.")
                rack_in_con_details = self.concertim_service.show_rack(rack_in_con['id'])
                rack.occupied = self.__get_occupied(rack_in_con_details['devices'])
            owner.owned_racks = owner.owned_racks.append(rack)
            return rack

    def __build_device(self, instance):
        template_id = self.templates[instance.flavor['id']].template_id
        size = int(self.templates[instance.flavor['id']].device_size)
        name_split = instance.name.split('.')
        rack_name = name_split[1] + '-' + instance.tenant_id[:5]
        device_name = name_split[0] + '-' + instance.id[:5]
        rack = self.devices_racks[instance.tenant_id][name_split[1]]['rack']
        rack_id = rack.rack_id
        start_u = self.__find_spot_in_rack(rack, size)
        self.__LOGGER.debug(f"New Instance Found - Building new Deivce(name: {device_name}, rack: (name: {rack_name}, ID: {rack_id}, start_u: {start_u}), instance_id: {instance.id}, template_id: {template_id})")
        device = ConcertimDevice(instance.id, instance.name, device_name, instance.tenant_id, instance.flavor['id'], template_id, name_split[1])
        #get location for device
        device_in_con = None
        try:
            device_in_con = self.concertim_service.create_device({'template_id': template_id, 'description': instance.id, 'name': device_name, 'facing': 'f', 'rack_id': rack_id, 'start_u': start_u})
        except FileExistsError as e:
            self.__LOGGER.warning(f"The device '{device_name}' already exists. Searching for device.")
            device_in_con = self.__search_local_devices(device)
            if not device_in_con:
                self.__LOGGER.exception(f"No usable device found after searching - please check concertim and restart service")
                raise SystemExit(e)
        except Exception as e:
            self.__LOGGER.exception(f"Unhandled Exception {e}")
            raise SystemExit(e)
        finally:
            device.device_id = device_in_con['id']
            device.rack_id = device_in_con['location']['rack_id']
            device.rack_start_u = device_in_con['location']['start_u']
            self.devices_racks[instance.tenant_id][name_split[1]]['rack'].occupied.extend([*range(start_u, start_u+size)])
            return device

    def __search_local_templates(self, template_obj):
        temp_in_con = None
        for temp in self.__current_templates:
            if temp['name'] == template_obj.flavor_id:
                self.__LOGGER.debug(f"The template '{temp['name']}' was found in local templates")
                temp_in_con = temp
                break
        if not temp_in_con:
            self.__LOGGER.warning(f"No template found in the CURRENT stored templates, updating local concertim template list")
            self.__current_templates = self.concertim_service.list_templates()
            for temp in self.__current_templates:
                if temp['name'] == template_obj.flavor_id:
                    self.__LOGGER.debug(f"The template '{temp['name']}' was found in local templates")
                    temp_in_con = temp
                    break
        return temp_in_con

    def __search_local_racks(self, rack_obj):
        rack_in_con = None
        project_id = rack_obj.project_id
        for rack in self.__current_racks:
            if rack['name'] == rack_obj.rack_name and rack['owner']['project_id'] == project_id:
                self.__LOGGER.debug(f"Found usable rack {rack['name']} owned by {rack['owner']['name']} in local racks list")
                rack_in_con = rack
                break
        if not rack_in_con:
            self.__LOGGER.warning(f"No usable rack found in local racks. Updating local racks")
            self.__current_racks = self.concertim_service.list_racks()
            for rack in self.__current_racks:
                if rack['name'] == rack_obj.rack_name and rack['owner']['project_id'] == project_id:
                    self.__LOGGER.debug(f"Found usable rack {rack['name']} owned by {rack['owner']['name']} in local racks list")
                    rack_in_con = rack
                    break
        return rack_in_con

    def __search_local_devices(self, device_obj):
        device_in_con = None
        for device in self.__current_devices:
            if device['name'] == device_obj.device_name and device['description'] == device_obj.instance_id:
                self.__LOGGER.debug(f"Found device:{device['name']} in local device list in rack:{device['location']['rack_id']}")
                device_in_con = device
                break
        if not device_in_con:
            self.__LOGGER.warning(f"No matching device found in local device list. Updated local device list.")
            self.__current_devices = self.concertim_service.list_devices()
            for device in self.__current_devices:
                if device['name'] == device_obj.device_name and device['description'] == device_obj.instance_id:
                    self.__LOGGER.debug(f"Found device:{device['name']} in local device list in rack:{device['location']['rack_id']}")
                    device_in_con = device
                    break
        return device_in_con


    def __find_spot_in_rack(self, rack, size):
        self.__LOGGER.debug(f"Finding spot in rack:{rack.rack_name} for {size} slots")
        height = int(rack.rack_height)
        occupied = rack.occupied
        spot_found = False
        start_location = -1
        for rack_row in range(height, 0, -1):
            if (rack_row + size - 1) <= height and rack_row >= 1:
                fits = True
                for device_section in range(0, size):
                    row = (rack_row + device_section)
                    if row in occupied:
                        fits = False
                if fits:
                    start_location = rack_row
                    spot_found = True
        if spot_found:
            self.__LOGGER.debug(f"Empty space found")
            rack.occupied
            return start_location
        self.__LOGGER.debug(f"No empty rack space found - Resizing rack and trying again.")
        self.concertim_service.update_rack({'name': rack.rack_name, 'u_height': int(height + size)})
        return self.__find_spot_in_rack(rack, size)

    def __get_occupied(self, device_list):
        occupied = []
        for device in device_list:
            occupied.extend(list(range(device['location']['start_u'], device['location']['end_u']+1)))
        return occupied

    def stop(self):
        self.__LOGGER.info("Stopping all other services")
        self.openstack = None
        self.concertim = None