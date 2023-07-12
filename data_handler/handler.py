# Local Imports
from utils.service_logger import create_logger
# concertim component objects
from concertim.components.device import ConcertimDevice
from concertim.components.rack import ConcertimRack
from concertim.components.template import ConcertimTemplate
from concertim.components.user import ConcertimUser
from concertim.concertim import ConcertimData
from concertim.concertim import OpenstackConcertimMap

# Py Packages
import time
from datetime import datetime, timedelta
import sys
import pika
import json

class DataHandler(object):
    def __init__(self, openstack, concertim, config_obj, log_file):
        self.__LOGGER = create_logger(__name__, log_file, config_obj['log_level'])
        self.openstack_service = openstack
        self.concertim_service = concertim
        self.__default_rack_height = int(config_obj['concertim']['default_rack_height'])

       


        self.__concertim_data = None
        self.__openstack_concertim_map = None



    def __populate_concertim_racks_devices(self):
        
        self.__concertim_data = ConcertimData()
        self.__openstack_concertim_map = OpenstackConcertimMap()

        concertim_racks = self.concertim_service.list_racks()
        #self.__LOGGER.debug(f"Concertim Rack : {concertim_racks}")

        for rack in concertim_racks:
            if 'metadata' in rack and 'openstack_stack_id' in rack['metadata']:
                rack_os_stack_id = rack['metadata']['openstack_stack_id']
            else:
                continue

            if rack_os_stack_id not in self.__concertim_data.racks:
                #self.__LOGGER.debug(f"Rack ID : {rack['id']}")

                self.__concertim_data.racks[ rack['id'] ] =  \
                    ConcertimRack(rack_name=rack['name'],
                                  owner = rack['owner']['id'],
                                  rack_height = rack['u_height'],
                                  rack_id = rack['id'],
                                  openstack_stack_id = rack_os_stack_id,
                                  status = rack['metadata']['status']  )

            if rack_os_stack_id not in self.__openstack_concertim_map.stack_to_rack:
                self.__openstack_concertim_map.stack_to_rack[rack_os_stack_id] = rack['id'] 



            devices = self.concertim_service.show_rack(ID = rack['id'])['devices']
            #self.__LOGGER.debug(f"devices : {devices}")
            for device in devices:
                if 'metadata' in device and 'openstack_instance_id' in device['metadata']:
                    device_os_instance_id = device ['metadata']['openstack_instance_id']
                else:
                    continue

                if device_os_instance_id not in self.__concertim_data.devices:
                    # Populate instance IDs in __concertim_devices
                    self.__concertim_data.devices[ device['id'] ] = \
                        ConcertimDevice( openstack_instance_id = device['metadata']['openstack_instance_id'],
                            openstack_instance_name = device['metadata']['openstack_instance_id'],
                            device_name = device['name'],
                            device_id = device['id'],
                            start_u = device['location']['start_u'],
                            end_u = device['location']['end_u'],
                            facing = device['location']['facing'],
                            depth = device['location']['depth'],
                            rack_id = device['location']['rack_id']
                        )  
                
                    self.__concertim_data.racks[ rack['id'] ].devices.add(device['id'])

                if device_os_instance_id not in self.__openstack_concertim_map.instance_to_device:
                    self.__openstack_concertim_map.instance_to_device[device_os_instance_id] = device['id']




        #self.__LOGGER.debug(f"Concertim Rack Object : {self.__concertim_data.racks}")
            
        #self.__LOGGER.debug(f"Concertim Device Object : {self.__concertim_data.devices}")

        #self.__LOGGER.debug(f"Openstack Stack to Concertim Rack Object : {self.__openstack_concertim_map.stack_to_rack}")

        #self.__LOGGER.debug(f"Openstack Instance to Concertim Device Object : {self.__openstack_concertim_map.instance_to_device}")

       


    # Send all metrics for concertim/openstack devices
    '''
    def send_metrics(self):
        self.__LOGGER.info('Sending Metrics')
        for project_id in self.devices_racks:
            resources = self.openstack_service.get_project_resources(project_id)
            for rack_id in self.devices_racks[project_id]:
                for instance_id in self.devices_racks[project_id][rack_id]['devices']:
                    self.handle_metrics(resources[instance_id])
    '''

    # Update concertim with Openstack info
    def update_concertim(self):
        self.__LOGGER.info('Updating Concertim')
        self.__populate_concertim_racks_devices()
        # Update Lists
        #self.__update_projects_list() # Finished
        #self.__update_users() # Finished
        #self.__update_templates() # Finished
        #self.__update_devices_racks() # Finished

        credentials = pika.PlainCredentials('openstack', 'J4Hjk8kSG7CRuP1wVUsuB5lmDj53U9W5jr73IgVL')
        parameters = pika.ConnectionParameters('10.151.0.184',
                                            5672,
                                            '/',
                                            credentials)

        



        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()
        # Specify the name of the queue to consume from
        queue_name = 'notifications.info'
        channel.basic_consume(queue=queue_name,
                            on_message_callback=self.callback,
                            auto_ack=True)

        self.__LOGGER.debug(f"Openstack RMQ consumer enabled ")
        channel.start_consuming()
        self.__LOGGER.debug(f"Openstack RMQ consumer exited ")
    
    # This function will be called for every message in the queue
    def callback(self, ch, method, properties, body):


        response = json.loads(body)
        message = json.loads(response['oslo.message'])

        self.__LOGGER.debug(f"Call back function trigerred")
        self.__LOGGER.debug(f" Event type : {message['event_type']}")
        self.__LOGGER.debug(f"Event payload : {message['payload']}")

        instance_id = message['payload']['instance_id']
        instance_state = message['payload']['state'] + \
            " , " + message['payload']['state_description'] + \
            " , " + message['payload']['progress']

        self.__LOGGER.debug(f" Instance {instance_id} state -> {instance_state}")

        if instance_id in self.__openstack_concertim_map.instance_to_device:
            device_id = self.__openstack_concertim_map.instance_to_device[instance_id]

            device = self.concertim_service.show_device(device_id)
            self.__LOGGER.debug(f" device {device}")

            self.concertim_service.update_device(ID = device_id ,variables_dict = {'name' : device['name'],\
                                                'description': device['description'], \
                                                'status' : instance_state, \
                                                'openstack_instance_id' : device['metadata']['openstack_instance_id'] })
            


        
        
    # Send all metrics for a given instance's resources
    '''
    def handle_metrics(self, instance_resource_dict):
        self.__LOGGER.debug(f"Processing metrics for instance:{instance_resource_dict['display_name']}")
        # 5 minute window
        stop = datetime.utcnow()
        start = stop - timedelta(minutes=5)
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
    '''

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

        #Create set of stacks created in Openstack
        openstack_stack_set = set()
        openstack_stacks = self.openstack_service.list_stacks()

        self.__LOGGER.debug(f" *** Adding New Racks in Concertim ***")

        for stack in openstack_stacks:
            #self.__LOGGER.debug(f"Stack : {stack}")    

            #if stack.project in self.projects:
            
            openstack_stack_set.add(stack.id)
            #else:
            #    continue

            
            if stack.id not in self.__openstack_concertim_map.stack_to_rack:
                self.__create_new_rack(stack)
            
        self.__LOGGER.debug(f"Openstack Stack Set  : {openstack_stack_set}")
    
        # Repopulate Concertim Cache
        self.__populate_concertim_racks_devices()

        
        self.__LOGGER.debug(f" *** Deleting Stale Racks in Concertim ***")
        for stack_id in self.__openstack_concertim_map.stack_to_rack:
            if stack_id not in openstack_stack_set:
                
                rack_id = self.__openstack_concertim_map.stack_to_rack[stack_id]

                # Deleting Devices
                for device_id in self.__concertim_data.racks[rack_id].devices:
                    self.__delete_device(device_id)

                self.__delete_rack(rack_id) 
        
        # Repopulate Concertim Cache
        self.__populate_concertim_racks_devices()

        openstack_device_set = set()

        self.__LOGGER.debug(f" *** Adding New Devices in Concertim ***")
        for stack_id in openstack_stack_set:
            stack_resources = self.openstack_service.list_stack_resources(stack_id = stack_id, type = 'OS::Nova::Server' )
            self.__LOGGER.debug(f"Stack resources : {stack_resources}")
            
            size = 2
            depth = 1


            for instance in stack_resources:
                
                if instance.resource_type != 'OS::Nova::Server':
                    continue
                
                instance_id = instance.physical_resource_id


                if not self.openstack_service.nova.server_exists(instance_id):
                    continue
                
                
                openstack_device_set.add(instance_id)

                if instance_id in self.__openstack_concertim_map.instance_to_device:
                    continue

                self.__LOGGER.debug(f"Instance ID : {instance_id}")
                
                rack_id = self.__openstack_concertim_map.stack_to_rack[stack_id]

                start_u = self.__find_empty_slot(rack_id, depth)

                self.__create_new_device(rack_id, instance, start_u)
                self.__populate_concertim_racks_devices()

        self.__LOGGER.debug(f" *** Deleting Stale Devices in Concertim ***")

        for instance_id, device_id in self.__openstack_concertim_map.instance_to_device.items():
            if not self.openstack_service.nova.server_exists(instance_id):
                self.__delete_device(device_id)
                self.__populate_concertim_racks_devices()
           

    def __find_empty_slot(self, rack_id, depth):

        filled_slots = []
        for device_id in self.__concertim_data.racks[rack_id].devices:
            device = self.__concertim_data.devices[device_id]
            filled_slots.append(tuple((device.start_u, device.depth)))

        filled_slots.sort()
        self.__LOGGER.debug(f"Filled slots in Rack id {rack_id} : {filled_slots}")

        start_u = 1

        for start, depth in filled_slots:
            self.__LOGGER.debug(f" {start} , {depth}")
            start_u = start + depth

        return start_u


    def __create_new_rack(self, stack):

        self.__LOGGER.debug(f"Creating rack for stack id : {stack.id}")

        height = self.__default_rack_height

        rack_id = None

        try:
            rack_in_con = self.concertim_service.create_rack({ 'name': stack.stack_name, \
                                                            'user_id' : '1', \
                                                            'u_height': height, \
                                                            'openstack_stack_id' : stack.id, \
                                                            'status' : stack.stack_status })

            self.__LOGGER.debug(f"{rack_in_con}")

            rack_id = rack_in_con['id']

        except FileExistsError as e:
            self.__LOGGER.debug(f" Rack already exists")
        except Exception as e:
            self.__LOGGER.debug(f"Unhandled Exception : {e}")
            
           
    def __create_new_device(self, rack_id, instance, start_u, template_id = 3):

        
        self.__LOGGER.debug(f"Creating device for instance id : {instance.physical_resource_id}")

        try:

            device_in_con = self.concertim_service.create_device({'template_id': template_id, \
                                                                'description': instance.physical_resource_id, \
                                                                'name': instance.physical_resource_id, \
                                                                'facing': 'f', \
                                                                'rack_id': rack_id, \
                                                                'start_u': start_u, \
                                                                'openstack_instance_id' : instance.physical_resource_id,
                                                                'status' : instance.resource_status})
        except FileExistsError as e:
            self.__LOGGER.debug(f" Device already exists")
        except Exception as e:
            self.__LOGGER.debug(f"Unhandled Exception : {e}")

   
    def __delete_rack(self, rack_id):
        # Delete Rack
        self.__LOGGER.debug(f" Deleting Rack {rack_id}")
        result = self.concertim_service.delete_rack(rack_id)
        self.__LOGGER.debug(f"{result}")


    def __delete_device(self, device_id):
        self.__LOGGER.debug(f" Deleteing Device {device_id}")
        result = self.concertim_service.delete_device(device_id)
        self.__LOGGER.debug(f"{result}")
    


    

   

   
   
   
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