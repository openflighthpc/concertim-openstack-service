# Local Imports
from utils.service_logger import create_logger
from data_handler.base import BaseHandler
# Py Packages
import sys


class UserHandler(BaseHandler):
    DEFAULT_CLIENTS = ['keystone']
    def __init__(self, config_obj, log_file, enable_concertim=False, clients=None):
        self.clients = clients if clients else UserHandler.DEFAULT_CLIENTS
        super().__init__(config_obj, log_file, self.clients, enable_concertim=enable_concertim)
        self.__LOGGER = create_logger(__name__, self._LOG_FILE, self._CONFIG['log_level'])

    def create_user_project(self, username, password, email):
        self.__LOGGER.info(f"Creating Concertim-managed (CM_) user/project in Openstack for : {username}")
        children = []
        opsk_username = f"CM_{username}"
        opsk_project_name = f"{opsk_username}_proj"
        try:
            # Create new project
            if 'project_domain_name' in self._CONFIG['openstack']:
                new_project = self.openstack_service.create_new_cm_project(opsk_project_name,domain=self._CONFIG['openstack']['project_domain_name'])
            else:
                new_project = self.openstack_service.create_new_cm_project(opsk_project_name)
            children.append(new_project)
            # Create new user
            if 'user_domain_name' in self._CONFIG['openstack']:
                new_user = self.openstack_service.create_new_cm_user(opsk_username, password, email, new_project, domain=self._CONFIG['openstack']['user_domain_name'])
            else:
                new_user = self.openstack_service.create_new_cm_user(opsk_username, password, email, new_project)
            children.append(new_user)

            return new_user, new_project
        except Exception as e:
            self.__LOGGER.error(f"Encountered ERROR - Aborting")
            super().__scrub(*children)
            self.__LOGGER.error(f"Encountered error when creating new Concertim Managed User/Project {type(e).__name__} - {e} - {sys.exc_info()[2].tb_frame.f_code.co_filename} - {sys.exc_info()[2].tb_lineno}")
            raise e




    