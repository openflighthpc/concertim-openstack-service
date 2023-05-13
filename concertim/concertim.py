from utils.service_logger import create_logger

class ConcertimService(object):
    def __init__(self, config_obj):
        self._CONFIG = config_obj
        self._LOGGER = create_logger(__name__, '/var/log/concertim-openstack-service-opt.log', self._CONFIG['log_level'])
    
    def disconnect(self):
        self._LOGGER.info("Disconnecting Concertim Services")
        return