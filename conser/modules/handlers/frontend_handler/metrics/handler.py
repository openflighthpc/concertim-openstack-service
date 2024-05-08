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
from conser.factory.abs_classes.handlers import Handler
import conser.exceptions as EXCP
import conser.utils.common as UTILS

# Py Packages
import time
from datetime import datetime, timedelta

class MetricsHandler(Handler):
    ############
    # DEFAULTS #
    ############
    # Interval = 15 to match Concertim MRD polling rate
    METRICS_INTERVAL = 15
    # Sliding window for metric value aggregates 
    DEFAULT_METRIC_WINDOW = 5
    ########
    # INIT #
    ########
    def __init__(self, clients_dict, log_file, log_level):
        self._LOG_LEVEL = log_level
        self._LOG_FILE = log_file
        self.__LOGGER = create_logger(__name__, self._LOG_FILE, self._LOG_LEVEL)
        self.clients = clients_dict
        self.view = None

    #############################
    # METRICS HANDLER FUNCTIONS #
    #############################

    def update_cluster_metrics(self):
        # EXIT CASES
        if not self.view or not self.view.devices:
            self.__LOGGER.info("No metrics to update, continuing at next interval")
            return

        # OBJECT LOGIC
        stop = datetime.utcnow()- timedelta(seconds=1)
        start = stop - timedelta(seconds=MetricsHandler.DEFAULT_METRIC_WINDOW)
        # SERVER DEVICES
        #-- loop over all devices in view
        for device_id_tup, device in self.view.devices.items():
            #-- if both concertim and cloud id are present, get its metrics
            if not device_id_tup[0] or not device_id_tup[1]:
                self.__LOGGER.debug(f"Skipping metrics for device {device_id_tup}")
                continue
            self.__LOGGER.debug(f"Starting -- Updating metrics for device {device_id_tup}")
            if device.details['type'] != 'Device::ComputeDetails':
                self.__LOGGER.debug(f"Device is not a server and is unsupported - skipping {device_id_tup}")
                continue
            metrics = self.clients['cloud'].get_metrics(
                resource_type='server',
                resource_id=device_id_tup[1],
                start=start,
                stop=stop
            )
            self.__LOGGER.debug(f"Attemping to send metrics {metrics}")
            #-- post metrics to concertim
            for m_name, m_dict in metrics.items():
                try:
                    self.clients['concertim'].send_metric(
                        ID=device_id_tup[0],
                        variables_dict={
                            'type': 'double',
                            'name': m_name,
                            'value': m_dict['value'],
                            'units': m_dict['unit'],
                            'slope': 'both',
                            'ttl': 3600
                        }
                    )
                except Exception as e:
                    self.__LOGGER.error(f"FAILED - Updating metric {m_name} for device {device_id_tup} - {e}")
                    continue
            self.__LOGGER.debug(f"Finished -- Updating metrics for device {device_id_tup}")

    ##############################
    # HANDLER REQUIRED FUNCTIONS #
    ##############################

    def run_process(self):
        """
        The main running loop of the Handler.
        """
        self.__LOGGER.info(f"=====================================================================================")
        self.__LOGGER.info(f"Starting - Updating Concertim Front-end with Metrics data")
        # EXIT CASES
        if 'concertim' not in self.clients or not self.clients['concertim']:
            raise EXCP.NoClientFound('concertim')
        if 'cloud' not in self.clients or not self.clients['cloud']:
            raise EXCP.NoClientFound('cloud')

        #-- Load current view
        try:
            self.view = UTILS.load_view()
        except Exception as e:
            self.__LOGGER.error(f"Could not load view - waiting for next loop")

        self.update_cluster_metrics()

        self.__LOGGER.info(f"Finished - Updating Concertim Front-end with Metrics data")
        self.__LOGGER.info(f"=====================================================================================\n\n")
        time.sleep(MetricsHandler.METRICS_INTERVAL)

    def disconnect(self):
        """
        Function for disconnecting all clients before garbage collection.
        """
        self.__LOGGER.info("Disconnecting Metrics Clients and Components")
        for name, client in self.clients.items():
            client.disconnect()
        self.clients = None

    ###########################
    # METRICS HANDLER HELPERS #
    ###########################