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
        for device_id_tup, device in self.view.devices.items()
            #-- if both concertim and cloud id are present, get its metrics
            if not device_id_tup[0] or not device_id_tup[1]:
                self.__LOGGER.debug(f"Skipping metrics for device {device_id_tup}")
                continue
            self.__LOGGER.debug(f"Starting -- Updating metrics for device {device_id_tup}")
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
        self.__LOGGER.info(f"=====================================================================================\n" \
            f"Starting - Updating Concertim Front-end with Metrics data")
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

        time.sleep(MetricsHandler.METRICS_INTERVAL)
        self.__LOGGER.info(f"Finished - Updating Concertim Front-end with Metrics data" \
            f"=====================================================================================\n\n")

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