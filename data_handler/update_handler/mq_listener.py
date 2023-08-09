# Local Imports
from utils.service_logger import create_logger
from data_handler.update_handler.update_base import UpdateHandler
# Py Packages
import sys
import json
import pika

class MqUpdateHandler(UpdateHandler):
    DEFAULT_QUEUE = 'notifications.info'
    DEFAULT_EVENT_TYPES = {
        'compute.instance': self.handle_instance_message, 
        'orchestration.stack': self.handle_stack_message
        }
    def __init__(self, config_obj, log_file, clients=None, queue=None, event_types=None):
        self.clients = clients if clients else UpdateHandler.DEFAULT_CLIENTS
        super().__init__(config_obj, log_file, self.clients)
        self.__LOGGER = create_logger(__name__, self._LOG_FILE, self._CONFIG['log_level'])
        self.queue = queue if queue else DEFAULT_QUEUE
        self.event_types = event_types if event_types else DEFAULT_EVENT_TYPES
        self.channel = self.__get_mq_channel()

    def __get_mq_channel(self):
        try:
            creds = self.__get_mq_creds()
            parameters = self.__get_mq_parameters(creds)
            connection = pika.BlockingConnection(parameters)
            channel = connection.channel()
            channel.basic_consume(queue=self.queue,
                                on_message_callback=self.handle_rmq_message,
                                auto_ack=True)
            return channel
        except Exception as e:
            self.__LOGGER.error(f"Cound not create MQ Channel - {type(e).__name__} - {e}")
            raise e

    def __get_mq_creds(self):
        try:
            mq_username = self._CONFIG['rmq']['rmq_username']
            mq_password = self._CONFIG['rmq']['rmq_password']
            return pika.PlainCredentials(mq_username,mq_password)
        except Exception as e:
            self.__LOGGER.error(f"Cound not create MQ Credentials - {type(e).__name__} - {e}")
            raise e
    
    def __get_mq_parameters(self, credentials):
        try:
            mq_address = self._CONFIG['rmq']['rmq_address']
            mq_port = self._CONFIG['rmq']['rmq_port']
            mq_path = self._CONFIG['rmq']['rmq_path']
            return pika.ConnectionParameters(mq_address, mq_port, mq_path, credentials)
        except Exception as e:
            self.__LOGGER.error(f"Cound not create MQ Parameters - {type(e).__name__} - {e}")
            raise e

    def start_listener(self):
        try:
            self.__LOGGER.info(f"Starting RabbitMQ Channel Consumer")
            self.channel.start_consuming()
            self.__LOGGER.info(f"Stopped RabbitMQ Channel Consumer")
            return False
        except Exception as e:
            self.__LOGGER.error(f"Cound not start listener - {type(e).__name__} - {e}")
            raise e

    def handle_rmq_message(self, ch, method, properties, body):
        try:
            message = None
            response = json.loads(body)
            try:
                message = json.loads(response['oslo.message'])
            except KeyError as e:
                self.__LOGGER.debug(f"Message did not contain 'oslo.message' key - Ignoring")
                return
            except Exception as e:
                self.__LOGGER.error(f"Failed to load message - {type(e).__name__} - {e} - Skipping")
                return
            self.__LOGGER.info(f"MQ message caught - Checking if supported - '{message['event_type']}'")
            #self.__LOGGER.debug(f"Message '{message['event_type']}' payload: {message['payload']}")
            function_list = [func for evnt_t, func in self.event_types if message['event_type'].startswith(evnt_t)]
            if function_list:
                if len(function_list) > 1:
                    self.__LOGGER.warning(f"Multiple functions found for '{message['event_type']}' - Using first function found - Functions:{function_list}")
                function = function_list[0]
                self.__LOGGER.debug(f"Loading latest View data")
                self.load_view()
                self.__LOGGER.info(f"Sending message to function:'{function}'")
                function(message)
            else:
                self.__LOGGER.info(f"Message event type '{message['event_type']}' not found in supported event types - Ignoring")
        except Exception as e:
            self.__LOGGER.error(f"Failed to handle message - {type(e).__name__} - {e} - {sys.exc_info()[2].tb_frame.f_code.co_filename} - {sys.exc_info()[2].tb_lineno}")
            raise e

    def handle_instance_message(self, msg):
        self.__LOGGER.debug(f"Starting - Handling instance message")
        self.__LOGGER.debug(f"Message : {msg}")
        payload = msg['payload']
        instance_id = payload['instance_id']
        inst_state = payload['state']
        inst_state_desc = payload['state_description']
        device = None
        # Look for matching instance/device in self.view
        for id_tup in self.view.devices:
            if id_tup[1] == instance_id:
                device = self.view.devices[id_tup]
                self.__LOGGER.debug(f"Matching ConcertimDevice found in View: {id_tup} - {device}")
                break
        if not device:
            self.__LOGGER.warning(f"No matching ConcertimDevice found in View for instannce: {instance_id} - Skipping update")
            return
        # Get state to send concertim
        what_to_check = inst_state_desc if inst_state_desc else inst_state
        con_state_list = [c_state for c_state, os_state_list in UpdateHandler.CONCERTIM_STATE_MAP['DEVICE'] if what_to_check in os_state_list]
        if con_state_list:
            con_state = con_state_list[0]
        else:
            con_state = 'FAILED'
        self.__LOGGER.debug(f"Instance state: '{instance_id}' - [state:{inst_state}, state_description:{inst_state_desc}, what_to_check:{what_to_check}, mapped_con_state:{con_state}]")
        # Did state change?
        if con_state == device.status:
            self.__LOGGER.info(f"Device status did not change: (NEW:{con_state} = OLD:{device.status}) - No update needed")
            return
        # State changed - update concertim and self.view
        self.__LOGGER.info(f"Updating Device '{device.id[0]}' status: {device.status} --> {con_state}")
        try:
            self.concertim_service.update_device(ID=device.id[0], variables_dict = {'name': device.concertim_name,\
                                            'description': device.description, \
                                            'status': con_state})
            self.view.devices[device.id].status = con_state
            self.save_view()
        except Exception as e:
            self.__LOGGER.error(f"Failed to update device - {type(e).__name__} - {e}")
            self.__LOGGER.warning(f"View not updated or saved due to update failure")
        self.__LOGGER.debug(f"Finished - Handling instance message")

    def handle_stack_message(self, msg):
        self.__LOGGER.debug(f"Starting - Handling stack message")
        self.__LOGGER.debug(f"Message : {msg}")
        payload = msg['payload']
        stack_id = payload['stack_identity']
        stack_state = payload['state']
        rack = None
        # Look for matching stack/rack in self.view
        for id_tup in self.view.racks:
            if id_tup[1] == stack_id:
                rack = self.view.racks[id_tup]
                self.__LOGGER.debug(f"Matching ConcertimRack found in View: {id_tup} - {rack}")
                break
        if not rack:
            self.__LOGGER.warning(f"No matching ConcertimRack found in View for stack: {stack_id} - Skipping update")
            return
        # Get state to send concertim
        con_state_list = [c_state for c_state, os_state_list in UpdateHandler.CONCERTIM_STATE_MAP['RACK'] if stack_state in os_state_list]
        if con_state_list:
            con_state = con_state_list[0]
        else:
            con_state = 'FAILED'
        self.__LOGGER.debug(f"Stack state: '{stack_id}' - [state:{stack_state}, mapped_con_state:{con_state}]")
        # Did state change?
        if con_state == rack.status:
            self.__LOGGER.info(f"Rack status did not change: (NEW:{con_state} = OLD:{rack.status}) - No update needed")
            return
        # State changed - update concertim and self.view
        self.__LOGGER.info(f"Updating Rack '{rack.id[0]}' status: {rack.status} --> {con_state}")
        try:
            self.concertim_service.update_rack(ID=rack.id[0], variables_dict = {'name': rack.concertim_name,\
                                            'description': rack.description, \
                                            'status': con_state})
            self.view.racks[rack.id].status = con_state
            self.save_view()
        except Exception as e:
            self.__LOGGER.error(f"Failed to update rack - {type(e).__name__} - {e}")
            self.__LOGGER.warning(f"View not updated or saved due to update failure")
        self.__LOGGER.debug(f"Finished - Handling stack message")

    def disconnect(self):
        self.__LOGGER.info(f"Disconnecting MQ services")
        try:
            self.channel.stop_consuming()
        except Exception as e:
            self.__LOGGER.error(f"Failed to stop consuming - {type(e).__name__} - {e}")
        try:
            self.channel.close()
        except Exception as e:
            self.__LOGGER.error(f"Failed to close channel - {type(e).__name__} - {e}")
        self.channel = None
        super().disconnect()


