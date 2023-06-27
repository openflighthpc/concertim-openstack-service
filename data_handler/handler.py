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
        self.__default_rack_height = int(config_obj['concertim']['default_rack_height'])

        self.__concertim_racks = {}
        self.__concertim_devices = {}
        self.__concertim_rackstodevices = {}

        self.__populate_concertim_racks_devices()


    
    def __populate_concertim_racks_devices(self):
        
        self.__concertim_racks = {}
        self.__concertim_devices = {}
        self.__concertim_rackstodevices = {}

        concertim_racks = self.concertim_service.list_racks()
        self.__LOGGER.debug(f"Concertim Rack : {concertim_racks}")

        for rack in concertim_racks:
            if 'metadata' in rack and 'openstack_stack_id' in rack['metadata']:
                rack_os_stack_id = rack['metadata']['openstack_stack_id']

                self.__LOGGER.debug(f"Rack ID : {rack_os_stack_id}")
                # Populate stack IDs in __concertim_racks
                self.__concertim_racks[ rack_os_stack_id ] = rack

                devices = self.concertim_service.show_rack(ID = rack['id'])['devices']
                self.__LOGGER.debug(f"devices : {devices}")
                for device in devices:
                    if 'metadata' in device and 'openstack_instance_id' in device['metadata']:
                        device_os_instance_id = device ['metadata']['openstack_instance_id']

                        # Populate instance IDs in __concertim_devices
                        self.__concertim_devices[ device_os_instance_id ] = device 

                        # Populate stack to instance mapping in __concertim_rackstodevices
                        if rack_os_stack_id not in self.__concertim_rackstodevices:
                            self.__concertim_rackstodevices[rack_os_stack_id] = set()
                        
                        self.__concertim_rackstodevices[rack_os_stack_id].add(device_os_instance_id)


        self.__LOGGER.debug(f"Concertim Rack Object : {self.__concertim_racks}")
            
        self.__LOGGER.debug(f"Concertim Device Object : {self.__concertim_devices}")

        self.__LOGGER.debug(f"Concertim Rack to Device Object : {self.__concertim_rackstodevices}")

       


    # Send all metrics for concertim/openstack devices
    def send_metrics(self):
        self.__LOGGER.info('Sending Metrics')
        for project_id in self.devices_racks:
            resources = self.openstack_service.get_project_resources(project_id)
            for rack_id in self.devices_racks[project_id]:
                for instance_id in self.devices_racks[project_id][rack_id]['devices']:
                    self.handle_metrics(resources[instance_id])

    # Update concertim with Openstack info
    def update_concertim(self):
        self.__LOGGER.info('Updating Concertim')

        # Update Lists
        self.__update_projects_list() # Finished
        #self.__update_users() # Finished
        #self.__update_templates() # Finished
        self.__update_devices_racks() # Finished

    # Update Openstack with changes made in Concertim
    def update_openstack(self):
        self.__LOGGER.info('Updating Openstack')

        concertim_rack_set = set()

        concertim_racks = self.concertim_service.list_racks()
        self.__LOGGER.debug(f"Concertim Rack : {concertim_racks}")
        for rack in concertim_racks:
            if 'openstack_stack_id' in rack['metadata']:
                concertim_rack_set.add(rack['metadata']['openstack_stack_id'])

        self.__LOGGER.debug(f"Concertim Rack Set : {concertim_rack_set}")    
        


        openstack_stack_set = set()

        openstack_stacks = self.openstack_service.list_stacks()

        for stack in openstack_stacks:
            openstack_stack_set.add(stack.id)
            self.__LOGGER.debug(f"Openstack stack : {stack}")

        self.__LOGGER.debug(f"Openstack Stack Set : {openstack_stack_set}")    

        
        
    # Send all metrics for a given instance's resources
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
    
    # Update all openstack projects that have the OpenStack 'concertim' user as a member
    def __update_projects_list(self):
        updated_projects_list = self.openstack_service.get_concertim_projects()
        new_projects = list(set(updated_projects_list) - set(self.projects))
        if new_projects:
            self.__LOGGER.debug(f"New Openstack project(s) to manage found : {new_projects}")
        removed_projects = list(set(self.projects) - set(updated_projects_list))
        if removed_projects:
            self.__LOGGER.warning(f"Managed Project(s) have been deleted : {removed_projects}")
        self.projects = updated_projects_list
    
    # Update all users from concertim for local dict
    def __update_users(self):
        updated_user_list = self.concertim_service.list_users()
        for user in updated_user_list:
            if user['login'] == "admin" or str(user['id']) in self.users:
                continue
            self.__LOGGER.debug(f"New User found - creating User(ID: {user['id']}, project_id: {user['project_id']}, name: {user['name']}, login: {user['login']})")
            self.users[str(user['id'])] = ConcertimUser(str(user['id']),
                                                    user['project_id'],
                                                    user['name'],
                                                    user['login'])

    # Update all templates
    # Updates both local and in concertim
    def __update_templates(self):
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

    # Update all racks and devices
    # Updates both local and in concertim
    def __update_devices_racks(self):

        """  openstack_instance_set = set()

        for stack_id in self.__concertim_racks :

            stack_resources = self.openstack_service.list_stack_resources(stack_id = stack.id, type = 'OS::Nova::Server' )

            for resource in stack_resources:
                instance_id = resource['physical_resource_id']
                self.__LOGGER.debug(f"Instance ID : {instance_id}")
                openstack_instance_set.add(instance_id)

                if instance_id not in self.__concertim_devices:
                    # Add device to associated rack


        for instance_id in self.__concertim_devices:
            if instance_id not in openstack_instance_set:
                # Delete device from associated
            """
        
        self.__LOGGER.debug(f" *** Adding New Racks in Concertim ***")

        #Create set of stacks/racks already created in Concertim
        concertim_rack_set = set()
        for stack_id in self.__concertim_racks:
            concertim_rack_set.add(stack_id)

        #Create set of stacks created in Openstack
        openstack_stack_set = set()
        openstack_stacks = self.openstack_service.list_stacks()
        for stack in openstack_stacks:
            self.__LOGGER.debug(f"Stack : {stack}")    

            if stack.project in self.projects:
                openstack_stack_set.add(stack.id)
            else:
                continue

            if stack.id not in concertim_rack_set:
                self.__create_new_rack(stack)
            

        self.__populate_concertim_racks_devices()

        self.__LOGGER.debug(f"Concertim Rack Set  : {concertim_rack_set}")

        self.__LOGGER.debug(f"Openstack Stack Set  : {openstack_stack_set}")

        self.__LOGGER.debug(f" *** Deleting Stale Racks in Concertim ***")
        for rack_id in self.__concertim_racks:
            if rack_id not in openstack_stack_set:
                
                # Delete Devices
                if rack_id in self.__concertim_rackstodevices:
                    for device_id in self.__concertim_rackstodevices[rack_id]:
                        self.__LOGGER.debug(f" Deleteing Device {device_id}")
                        result = self.concertim_service.delete_device(self.__concertim_devices[device_id]['id'])
                        self.__LOGGER.debug(f"{result}")

                # Delete Rack
                self.__LOGGER.debug(f" Deleteing Rack {rack_id}")
                result = self.concertim_service.delete_rack(self.__concertim_racks[rack_id]['id'])
                self.__LOGGER.debug(f"{result}")

       

        
       
            
    
    def __create_new_rack(self, stack):

        self.__LOGGER.debug(f"Creating rack for stack id : {stack.id}")

        height = self.__default_rack_height

        rack_id = None

        try:
            rack_in_con = self.concertim_service.create_rack({ 'name': stack.stack_name, 'user_id' : '1', 'u_height': height, 'openstack_stack_id' : stack.id})

            self.__LOGGER.debug(f"{rack_in_con}")

            rack_id = rack_in_con['id']

        except FileExistsError as e:
            self.__LOGGER.debug(f" Rack already exists")
        except Exception as e:
            self.__LOGGER.debug(f"Unhandled Exception")

        stack_resources = self.openstack_service.list_stack_resources(stack_id = stack.id, type = 'OS::Nova::Server' )
        self.__LOGGER.debug(f"Stack resources : {stack_resources}")
        start_u = 1
        size = 2
        space = 1

        for resource in stack_resources:
            
            instance_id = resource.physical_resource_id
            self.__LOGGER.debug(f"Instance ID : {instance_id}")
            self.__create_new_device(rack_id, instance_id, start_u, size, space)

            start_u = start_u + size + space
            
        
        
    

   
    def __create_new_device(self, rack_id, openstack_instance_id, start_u, size, space):
        self.__LOGGER.debug(f"Creating device for instnace id : {openstack_instance_id}")

        try:

            device_in_con = self.concertim_service.create_device({'template_id': 3, 'description': openstack_instance_id, 'name': openstack_instance_id, 'facing': 'f', 'rack_id': rack_id, 'start_u': start_u, 'openstack_instance_id' : openstack_instance_id})
        except FileExistsError as e:
            self.__LOGGER.debug(f" Device already exists")
        except Exception as e:
            self.__LOGGER.debug(f"Unhandled Exception")

   
    def __delete_old_rack(self, stack_id):
        self.__LOGGER.debug(f"Deleting rack for stack id : {stack_id}")


    def __delete_device(self, rack_id, device_id):
        self.__LOGGER.debug(f"Deleting device")
    


    

    # Deletes the rack from both local lists and Concertim
    def __delete_rack(self, project_id, rack_name):
        self.__LOGGER.debug(f"Rack:{rack_name} was found to be EMPTY for project:{project_id}")
        rack = self.devices_racks[project_id][rack_name]['rack']
        del self.devices_racks[project_id][rack_name]
        self.__LOGGER.debug(f"Deleting Rack:(ID:{rack.rack_id}, NAME:{rack.rack_name})")
        result = self.concertim_service.delete_rack(rack.rack_id)
        return result

    # Deletes the device from both local lists and Concertim
    def __delete_device(self, project_id, rack_name, instance_id):
        self.__LOGGER.debug(f"Instance:{instance_id} was not found in project:{project_id}")
        device = self.devices_racks[project_id][rack_name]['devices'][instance_id]
        del self.devices_racks[project_id][rack_name]['devices'][instance_id]
        self.__LOGGER.debug(f"Deleting device:(ID:{device.device_id}, NAME:{device.device_name}) from rack:{rack_name}")
        result = self.concertim_service.delete_device(device.device_id)
        return result


    # Returns the rack object for the cluster if it is able to create
    def __build_rack(self, rack_name):
        
        height = self.__default_rack_height
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

    # Returns the device object for the instance if it is able to create
    def __build_device(self, rack_id, instance_name):
        template_id = self.templates[instance.flavor['id']].template_id
        size = int(self.templates[instance.flavor['id']].device_size)
        name_split = instance.name.split('.')
        rack_name = name_split[1] + '-' + instance.tenant_id[:5]
        device_name = name_split[0] + '-' + instance.id[:5]

        start_u = self.__find_spot_in_rack(rack, size)
        self.__LOGGER.debug(f"Building new Deivce(name: {device_name}, rack: (name: {rack_name}, ID: {rack_id}, start_u: {start_u}), instance_id: {instance.id}, template_id: {template_id})")
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

   
    # Returns the matching template found or None
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

    # Returns the matching rack found or None
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

    # Returns the matching device found or None
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

    # Returns the 'start_u' as an int for a device of 'size' in 'rack'
    def __find_spot_in_rack(self, rack_height, size):
        height = rack_height
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

    # Returns the list of occupied slots in a rack (ex. [1,5,27,28,29])
    def __get_occupied(self, device_list):
        occupied = []
        for device in device_list:
            occupied.extend(list(range(device['location']['start_u'], device['location']['end_u']+1)))
        return occupied

    def stop(self):
        self.__LOGGER.info("Stopping all other services")
        self.openstack = None
        self.concertim = None