# Local Imports
from con_opstk.utils.service_logger import create_logger
from con_opstk.data_handler.base import BaseHandler
from con_opstk.openstack.exceptions import APIServerDefError
# Py Packages
import sys
from novaclient.exceptions import ClientException as nova_ex
from heatclient.exc import BaseException as heat_ex


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

    def update_status(self, type, id, action):
        self.__LOGGER.info(f"Starting action {action} for {type} {id}")
        try:
            result = None
            if type == "devices":
                result = self.openstack_service.update_instance_status(id, action)
            elif type == "racks":
                result = self.openstack_service.update_stack_status(id, action)
            
            # Check if update function returned a client exception (will only happen if forbidden/unauth)
            if isinstance(result, nova_ex) or isinstance(result, heat_ex):
                return (403, "Could not complete action due to credentials provided")
            return result
        except Exception as e:
            self.__LOGGER.error(f"Encountered error when completing action [action:{action},type:{type},id:{id}] : {e.__class__.__name__} - {e} - {sys.exc_info()[2].tb_frame.f_code.co_filename} - {sys.exc_info()[2].tb_lineno}")
            raise e

    def create_keypair(self, name, key_type='ssh', imported_pub_key=None, user=None):
        self.__LOGGER.info(f"Starting creation of {key_type} key pair {name}")
        try:
            result = self.openstack_service.create_keypair(name, imported_pub_key=None, user=None, key_type='ssh')

            # Check if update function returned a client exception (will only happen if forbidden/unauth)
            if isinstance(result, nova_ex) or isinstance(result, heat_ex):
                return (403, "Could not complete action due to credentials provided")
            return result
        except Exception as e:
            self.__LOGGER.error(f"Encountered error when completing key pair creation : {e.__class__.__name__} - {e} - {sys.exc_info()[2].tb_frame.f_code.co_filename} - {sys.exc_info()[2].tb_lineno}")
            raise e

    