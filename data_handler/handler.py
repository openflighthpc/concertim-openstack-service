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
import json
import pika

class DataHandler(object):
    def __init__(self, openstack, concertim, config_obj, log_file):
        self.__LOGGER = create_logger(__name__, log_file, config_obj['log_level'])
        self.openstack_service = openstack
        self.concertim_service = concertim
        self.config = config_obj
        self.__default_rack_height = int(config_obj['concertim']['default_rack_height'])

       


        self.__concertim_data = None
        self.__openstack_concertim_map = None

        self.update_timestamp = datetime.now()


    def __populate_cache(self):
        self.__concertim_data = ConcertimData()
        self.__openstack_concertim_map = OpenstackConcertimMap()

        self.__populate_concertim_templates()

        self.__populate_concertim_users()

        self.__populate_concertim_racks_devices()

 

    def __populate_concertim_users(self):
        user_list = self.concertim_service.list_users()
        #self.__LOGGER.debug(f'{user_list}')
        
        for user in user_list:
            if user['login'] == "admin" or str(user['id']) in self.__concertim_data.users:
                continue
            self.__LOGGER.debug(f"New User found - creating User(ID: {user['id']}, project_id: {user['project_id']}, name: {user['name']}, login: {user['login']})")
            self.__concertim_data.users[str(user['id'])] = ConcertimUser(str(user['id']),
                                                    user['project_id'],
                                                    user['name'],
                                                    user['login'])

            if user['project_id'] is not None:
                self.__openstack_concertim_map.os_project_to_concertim_user[user['project_id']] = str(user['id']) 
            
        self.__LOGGER.debug(f'User Objects {self.__concertim_data.users}')
        self.__LOGGER.debug(f'User Mapping Objects {self.__openstack_concertim_map.os_project_to_concertim_user}')

    def __populate_concertim_racks_devices(self):
        
        
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
                                  status = rack['status']  )

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

    def __populate_concertim_templates(self):

        templates = self.concertim_service.list_templates()
        #self.__LOGGER.debug(f'{templates}')

        for template in templates:
            temp_obj = ConcertimTemplate(template_id = template['id'], \
                                        flavor_name = template['name'], \
                                        ram = template['ram'], \
                                        disk = template['disk'], \
                                        vcpus = template['vcpus'], \
                                        device_size = template['height'], \
                                        flavor_id = template['foreign_id'])
            
            #Creating Concertim object in local cache
            self.__concertim_data.templates[template['id']] = temp_obj

            # Creating Openstac flavor to Concertim Template mapping
            if template['foreign_id'] is not None:
                self.__openstack_concertim_map.flavor_to_template[template['foreign_id']] = template['id']


        self.__LOGGER.debug(f'Template Objects {self.__concertim_data.templates}')
        self.__LOGGER.debug(f'Template Mapping {self.__openstack_concertim_map.flavor_to_template}')


    # Update concertim with Openstack info
    def update_concertim(self):
        self.__LOGGER.info('Updating Concertim')       
        self.__populate_cache()
        

        # Update Lists
        #self.__update_projects_list() # Finished
        #self.__update_users() # Finished
        self.__update_templates() # Finished
        self.__update_devices_racks() # Finished

        self.update_timestamp =  datetime.now()
        

    def rmq_listener(self):

        credentials = pika.PlainCredentials(self.config['rmq']['rmq_username'], self.config['rmq']['rmq_password'])
        parameters = pika.ConnectionParameters(self.config['rmq']['rmq_address'],
                                            self.config['rmq']['rmq_port'],
                                            self.config['rmq']['rmq_path'],
                                            credentials)

        
        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()
        # Specify the name of the queue to consume from
        queue_name = 'notifications.info'
        channel.basic_consume(queue=queue_name,
                            on_message_callback=self.rmq_callback,
                            auto_ack=True)

        self.__LOGGER.debug(f"Openstack RMQ consumer enabled ")
        channel.start_consuming()
        self.__LOGGER.debug(f"Openstack RMQ consumer exited ")

    def rmq_callback(self, ch, method, properties, body):

        current_timestamp = datetime.now()
        self.__LOGGER.info(f'Previous timestamp {self.update_timestamp}')
        self.__LOGGER.info(f'Current timestamp {current_timestamp}')
        
        if (current_timestamp - self.update_timestamp).total_seconds() >= 10:
            time.sleep(5)
            self.update_concertim() 



        self.__LOGGER.debug(f"Call back function trigerred")
        #self.__LOGGER.debug(f"{body}")

        response = json.loads(body)

        message = json.loads(response['oslo.message'])
            
        self.__LOGGER.debug(f" Event type : {message['event_type']}")
        self.__LOGGER.debug(f"Event payload : {message['payload']}")

        if message['event_type'].startswith('compute.instance'):
            self.rmq_update_instance(message)
            
        if message['event_type'].startswith('orchestration.stack'):
            self.rmq_update_rack(message)

        
    
        
    def rmq_update_rack(self, message):
        # orchestration.stack.delete.end , 
        # orchestration.stack.create.end
        stack_id = message['payload']['stack_identity']
        stack_state = message['payload']['state']

        if stack_state == 'CREATE_COMPLETE' or stack_state == 'RESUME_COMPLETE':
            concertim_rack_status = 'ACTIVE'
        elif stack_state == 'CREATE_IN_PROGRESS' or stack_state == 'SUSPEND_IN_PROGRESS':
            concertim_rack_status = 'IN_PROGRESS'
        elif stack_state == 'SUSPEND_COMPLETE':
            concertim_rack_status = 'STOPPED'
        else:
            concertim_rack_status = 'FAILED'

        self.__LOGGER.debug(f" Heat {stack_id} state -> {stack_state}")

        if stack_id in self.__openstack_concertim_map.stack_to_rack:
            rack_id = self.__openstack_concertim_map.stack_to_rack[stack_id]

            try:
                rack = self.concertim_service.show_rack(rack_id)
            except Exception as e:
                self.__LOGGER.debug(f" Exception : {e}")
                return
            
            self.__LOGGER.debug(f" Rack {rack}")

            try:
                self.concertim_service.update_rack(ID=rack_id,variables_dict = {'name' : rack['name'], 'u_height' : rack['u_height'], 'status' : concertim_rack_status})
            except Exception as e:
                self.__LOGGER.debug(f"Exception : {e}")

    def rmq_update_instance(self, message):
        # compute.instance.power_off.start , compute.instance.power_off.end  
        # compute.instance.power_on.start , compute.instance.power_on.end
        instance_id = message['payload']['instance_id']
        instance_state = message['payload']['state']

        if instance_state == 'active':
            concertim_device_status = 'ACTIVE'
        elif instance_state == 'stopped' or instance_state == 'suspended':
            concertim_device_status = 'STOPPED'
        elif instance_state == 'building':
            concertim_device_status = 'IN_PROGRESS'
        else:
            concertim_device_status = 'FAILED'

        self.__LOGGER.debug(f" Instance {instance_id} state -> {instance_state}")

        if instance_id in self.__openstack_concertim_map.instance_to_device:
            device_id = self.__openstack_concertim_map.instance_to_device[instance_id]

            try:
                device = self.concertim_service.show_device(device_id)
            except Exception as e:
                self.__LOGGER.debug(f" Exception : {e}")
                return 
            
            #self.__LOGGER.debug(f" device {device}")

            try:
                self.concertim_service.update_device(ID = device_id ,variables_dict = {'name' : device['name'],\
                                                'description': device['description'], \
                                                'status' : concertim_device_status })
            except Exception as e:
                self.__LOGGER.debug(f" Exception : {e}")

        
        
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
    

    # Update all templates
    # Updates both local and in concertim
    def __update_templates(self):

        self.__LOGGER.debug(f"*** Creating Templates ***")
        openstack_flavors = self.openstack_service.get_flavors()
        openstack_flavor_set = set()

        self.__LOGGER.debug(f"Openstack flavor {openstack_flavors}")

        for flavor in openstack_flavors:

            openstack_flavor_set.add(openstack_flavors[flavor]['id'])
            if openstack_flavors[flavor]['id'] in self.__openstack_concertim_map.flavor_to_template:
                continue
            if openstack_flavors[flavor]['vcpus'] <= 1:
                device_height = 1
            elif openstack_flavors[flavor]['vcpus'] <= 2:
                device_height = 2
            elif openstack_flavors[flavor]['vcpus'] <= 4:
                device_height = 3
            else:
                device_height = 4
            description = f"{openstack_flavors[flavor]['name']} - {openstack_flavors[flavor]['ram']}MB RAM, {openstack_flavors[flavor]['disk']}GB disk, {openstack_flavors[flavor]['vcpus']} vCPU"
            self.__LOGGER.debug(f"New Flavor found - creating template(name: {openstack_flavors[flavor]['name']}, description: '{description}', size: {device_height})")
            
            temp_in_con = None
            # try to create the new template in concertim
            # if there is a conflict, pull from concertim and check
            # if there is still no template, raise e
            try:
                temp_in_con = self.concertim_service.create_template({'name': openstack_flavors[flavor]['name'], 'description': description, 'height': device_height, 'ram' : openstack_flavors[flavor]['ram'], 'disk' : openstack_flavors[flavor]['disk'], 'vcpus' : openstack_flavors[flavor]['vcpus'], 'foreign_id' : openstack_flavors[flavor]['id']})
            except FileExistsError as e:
                self.__LOGGER.warning(f"The template {openstack_flavors[flavor]['name']} already exists. Searching concertim for the template.")
                """ temp_in_con = self.__search_local_templates(template)
                if not temp_in_con:
                    self.__LOGGER.exception(f"No template found after updating - please check concertim and restart process.")
                    raise SystemExit(e) """
            except Exception as e:
                self.__LOGGER.exception(f"Unhandled Exception {e}")
                #raise SystemExit(e)
            finally:
                self.__populate_concertim_templates()

        self.__LOGGER.debug(f"Openstack falvor set {openstack_flavor_set}")
        for openstack_flavor_id in self.__openstack_concertim_map.flavor_to_template:
            if openstack_flavor_id not in openstack_flavor_set:
                self.__LOGGER.debug(f"*** Deleting stale Template from Concertim ***")
                try:
                    template_id = self.__openstack_concertim_map.flavor_to_template[openstack_flavor_id]

                    self.__LOGGER.debug(f"Deleting Template {template_id}")

                    self.concertim_service.delete_template(template_id)
                except Exception as e:
                    self.__LOGGER.exception(f"Unhandled Exception {e}")
                    #raise SystemExit(e)
                finally:
                    self.__populate_concertim_templates()
 
    # Update all racks and devices
    # Updates both local and in concertim
    def __update_devices_racks(self):

        #Create set of stacks created in Openstack
        openstack_stack_set = set()
        openstack_stacks = self.openstack_service.list_stacks()

        self.__LOGGER.debug(f" *** Adding New Racks in Concertim ***")

        for stack in openstack_stacks:
            self.__LOGGER.debug(f"Stack : {stack}")    

            if stack.project in self.__openstack_concertim_map.os_project_to_concertim_user:
                user_id = self.__openstack_concertim_map.os_project_to_concertim_user[stack.project]
                openstack_stack_set.add(stack.id)
            else:
                continue

            
            # Create new rack
            if stack.id not in self.__openstack_concertim_map.stack_to_rack:
                self.__create_new_rack(stack, user_id)
            
        self.__LOGGER.debug(f"Openstack Stack Set  : {openstack_stack_set}")
    
        # Repopulate Concertim Cache
        self.__populate_cache()

        
        self.__LOGGER.debug(f" *** Deleting Stale Racks in Concertim ***")
        for stack_id in self.__openstack_concertim_map.stack_to_rack:
            if stack_id not in openstack_stack_set:
                
                rack_id = self.__openstack_concertim_map.stack_to_rack[stack_id]

                # Deleting Devices
                for device_id in self.__concertim_data.racks[rack_id].devices:
                    self.__delete_device(device_id)

                self.__delete_rack(rack_id) 
        
        # Repopulate Concertim Cache
        self.__populate_cache()

        openstack_device_set = set()

        self.__LOGGER.debug(f" *** Adding New Devices in Concertim ***")
        for stack_id in openstack_stack_set:
            stack_resources = self.openstack_service.list_stack_resources(stack_id = stack_id, type = 'OS::Nova::Server' )
            self.__LOGGER.debug(f"Stack resources : {stack_resources}")
            
            if stack_id not in self.__openstack_concertim_map.stack_to_rack:
                continue


            for instance in stack_resources:
                
                if instance.resource_type != 'OS::Nova::Server':
                    continue
                
                instance_id = instance.physical_resource_id


                if not self.openstack_service.nova.server_exists(instance_id):
                    continue
                
                instance_info = self.openstack_service.nova.get_server(instance_id)
                self.__LOGGER.debug(f"Instance flavor ID : {instance_info.flavor['id']}")

                instance_flavor_id = instance_info.flavor['id']

                template_id = self.__openstack_concertim_map.flavor_to_template[instance_flavor_id]
                template = self.__concertim_data.templates[ template_id ]



                openstack_device_set.add(instance_id)

                if instance_id in self.__openstack_concertim_map.instance_to_device:
                    continue

                self.__LOGGER.debug(f"Instance ID : {instance_id}")
                
                rack_id = self.__openstack_concertim_map.stack_to_rack[stack_id]

                start_u = self.__find_empty_slot(rack_id, template.device_size)

                self.__create_new_device(rack_id, instance, instance_info, start_u, template.template_id)
                #self.__populate_concertim_racks_devices()
                # Repopulate Concertim Cache
                self.__populate_cache()

        

        self.__LOGGER.debug(f" *** Deleting Stale Devices in Concertim ***")

        for instance_id, device_id in self.__openstack_concertim_map.instance_to_device.items():
            if not self.openstack_service.nova.server_exists(instance_id):
                self.__delete_device(device_id)
                #self.__populate_concertim_racks_devices()
                # Repopulate Concertim Cache
                self.__populate_cache()
           
        
    


    def __create_new_rack(self, stack, user_id):

        self.__LOGGER.debug(f"Creating rack for stack id : {stack.id}")

        height = self.__default_rack_height

        rack_id = None

        status = stack.stack_status

        if status == 'CREATE_COMPLETE':
            concertim_rack_status = 'ACTIVE'
        elif status == 'CREATE_IN_PROGRESS':
            concertim_rack_status = 'IN_PROGRESS'
        else:
            concertim_rack_status = 'FAILED'

        try:
            rack_in_con = self.concertim_service.create_rack({ 'name': stack.stack_name, \
                                                            'user_id' : user_id, \
                                                            'u_height': height, \
                                                            'openstack_stack_id' : stack.id, \
                                                            'status' : concertim_rack_status, \
                                                            'openstack_stack_info' : str(stack)[7:-1] })

            self.__LOGGER.debug(f"{rack_in_con}")

            rack_id = rack_in_con['id']

        except FileExistsError as e:
            self.__LOGGER.debug(f" Rack already exists : {e}")
        except Exception as e:
            self.__LOGGER.debug(f"Unhandled Exception : {e}")
            
    def __create_new_device(self, rack_id, instance, instance_info, start_u, template_id):

        
        self.__LOGGER.debug(f"Creating device for instance id : {instance.physical_resource_id}")

        status = instance.resource_status

        if status == 'CREATE_COMPLETE':
            concertim_device_status = 'ACTIVE'
        elif status == 'CREATE_IN_PROGRESS':
            concertim_device_status = 'IN_PROGRESS'
        else:
            concertim_device_status = 'FAILED'
        self.__LOGGER.debug(f"Creating device for instance  : {instance_info.__dict__}")
        try:

            device_in_con = self.concertim_service.create_device({'template_id': template_id, \
                                                                'description': instance.physical_resource_id, \
                                                                'name': instance.physical_resource_id, \
                                                                'facing': 'f', \
                                                                'rack_id': rack_id, \
                                                                'start_u': start_u, \
                                                                'openstack_instance_id' : instance.physical_resource_id,
                                                                'status' : concertim_device_status, \
                                                                'openstack_instance_info' : instance_info.__dict__['_info']['addresses']})
        except FileExistsError as e:
            self.__LOGGER.debug(f" Device already exists : {e}")
        except Exception as e:
            self.__LOGGER.debug(f" Exception : {e}")

   
    def __delete_rack(self, rack_id):
        # Delete Rack
        self.__LOGGER.debug(f" Deleting Rack {rack_id}")
        try:
            result = self.concertim_service.delete_rack(rack_id)
            self.__LOGGER.debug(f"{result}")
        except Exception as e:
            self.__LOGGER.debug(f"Unhandled Exception : {e}")

    def __delete_device(self, device_id):
        self.__LOGGER.debug(f" Deleteing Device {device_id}")

        try:
            result = self.concertim_service.delete_device(device_id)
            self.__LOGGER.debug(f"{result}")
        except Exception as e:
            self.__LOGGER.debug(f" Exception : {e}")

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
            start_u = start + depth + 1

        return start_u 
    


    

   

   
   


    ####################################################   
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