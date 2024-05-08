"""
==============================================================================
 Copyright (C) 2024-present Alces Flight Ltd.

 This file is part of Concertim Openstack Service.

 This program and the accompanying materials are made available under
 the terms of the Eclipse Public License 2.0 which is available at
 <https://www.eclipse.org/legal/epl-2.0>, or alternative license
 terms made available by Alces Flight Ltd - please direct inquiries
 about licensing to licensing@alces-flight.com.

 Concertim Openstack Service is distributed in the hope that it will be useful, but
 WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, EITHER EXPRESS OR
 IMPLIED INCLUDING, WITHOUT LIMITATION, ANY WARRANTIES OR CONDITIONS
 OF TITLE, NON-INFRINGEMENT, MERCHANTABILITY OR FITNESS FOR A
 PARTICULAR PURPOSE. See the Eclipse Public License 2.0 for more
 details.

 You should have received a copy of the Eclipse Public License 2.0
 along with Concertim Openstack Service. If not, see:

  https://opensource.org/licenses/EPL-2.0

 For more information on Concertim Openstack Service, please visit:
 https://github.com/openflighthpc/concertim-openstack-service
==============================================================================
"""

# Local Imports
from conser.utils.service_logger import create_logger
import conser.exceptions as EXCP
from conser.factory.abs_classes.components import Component
import conser.utils.common as UTILS

# Py Packages
import pika
import json

class RMQComponent(Component):
    def __init__(self, queue_config, log_file, log_level):
        self._LOG_FILE = log_file
        self._LOG_LEVEL = log_level
        self.__LOGGER = create_logger(__name__, self._LOG_FILE, self._LOG_LEVEL)
        self.__LOGGER.info("CREATING RABBIT MQ COMPONENT")
        self.event_types = [
            'compute.instance',
            'orchestration.stack'
        ]
        self.queue = 'notifications.info'
        self.client = self.get_connection_obj(queue_config)

    def get_connection_obj(self, config_dict):
        # Get creds
        mq_username = config_dict['rmq_username']
        mq_password = config_dict['rmq_password']
        creds = pika.PlainCredentials(mq_username, mq_password)
        # Get Params
        mq_address = config_dict['rmq_address']
        mq_port = config_dict['rmq_port']
        mq_path = config_dict['rmq_path']
        parameters = pika.ConnectionParameters(mq_address, mq_port, mq_path, creds)
        # Get channel
        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()
        channel.basic_consume(
            queue=self.queue,
            on_message_callback=self.filter_rmq_message,
            auto_ack=True
        )
        return channel

    def start_listening(self):
        self.__LOGGER.info(f"Starting Rabbit MQ Channel Consumer")
        self.client.start_consuming()
        self.__LOGGER.info(f"Stopped Rabbit MQ Channel Consumer\n")

    def filter_rmq_message(self, ch, method, properties, body):
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
        self.__LOGGER.debug(f"MQ message caught - Checking if supported - '{message['event_type']}'")
        self.__LOGGER.debug(f"Creating RESYNC HOLD file")
        UTILS.check_resync_hold()
        for evnt_t in self.event_types:
            if message['event_type'].startswith(evnt_t):
                self.__LOGGER.debug(f"Creating RESYNC FLAG file")
                UTILS.create_resync_flag()
                self.__LOGGER.debug(f"Deleting RESYNC HOLD file")
                UTILS.delete_resync_hold()
                return
        self.__LOGGER.debug(f"Deleting RESYNC HOLD file")
        UTILS.delete_resync_hold()
        self.__LOGGER.debug(f"Message event type '{message['event_type']}' not found in supported event types - Ignoring")


    def disconnect(self):
        self.__LOGGER.info(f"Disconnecting Rabbit MQ services")
        try:
            self.client.stop_consuming()
        except Exception as e:
            self.__LOGGER.error(f"Failed to stop consuming - {type(e).__name__} - {e}")
        try:
            self.client.close()
        except Exception as e:
            self.__LOGGER.error(f"Failed to close channel - {type(e).__name__} - {e}")
        self.client = None