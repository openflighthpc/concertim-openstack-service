# Local Imports
from con_opstk.utils.service_logger import create_logger
from con_opstk.openstack.client_handlers.client_base import ClientHandler
# Py Packages
import sys
import time
# Openstack Packages
import novaclient.client as n_client
import novaclient.exceptions as nex
from novaclient.v2.servers import Server

class NovaHandler(ClientHandler):
    def __init__(self, sess, log_file, log_level):
        super().__init__(sess, log_file, log_level)
        self.__LOGGER = create_logger(__name__, self._LOG_FILE, self._LOG_LEVEL)
        self.client = self.__get_client(self._SESSION)

    def __get_client(self, sess):
        start_time = time.time()
        error = None
        while time.time() - start_time < 30:  # Try for up to 30 seconds
            try:
                client = n_client.Client(version='2', session=sess)
                self.__LOGGER.debug("SUCCESS - Nova client connected")
                return client # Exit if client creation is successful
            except Exception as e:
                self.__LOGGER.warning(f"Failed to create Nova client: {type(e).__name__} - {e} - Retrying...")
                error = e
                time.sleep(1)  # Wait for a second before retrying
        self.__LOGGER.error(f"Failed to create Nova client after multiple attempts : {type(error).__name__} - {error}")
        raise error

    def list_flavors(self):
        try:
            os_flavors = self.client.flavors.list(detailed=True)
            return os_flavors
        except Exception as e:
            self.__LOGGER.error(f"An unexpected error : {type(e).__name__} - {e}")
            raise e

    def list_servers(self, project_id=None, state=None):
        search_opts = {'all_tenants':1}
        if project_id:
            search_opts['project_id'] = project_id
        if state:
            search_opts['vm_state'] = state
        try:
            if project_id:
                self.__LOGGER.debug(f"Fetching servers for project : {project_id}")
                return self.client.servers.list(detailed=True, search_opts=search_opts)
            self.__LOGGER.debug("Fetching servers for all projects")
            return self.client.servers.list(detailed=True, search_opts=search_opts)
        except Exception as e:
            self.__LOGGER.error(f"An unexpected error : {type(e).__name__} - {e}")
            raise e

    def get_server(self, instance_id):
        try:
            return self.client.servers.get(instance_id)
        except Exception as e:
            self.__LOGGER.error(f"An unexpected error : {type(e).__name__} - {e}")
            raise e

    def get_server_group(self, group_id):
        try:
            return self.client.server_groups.get(group_id)
        except Exception as e:
            self.__LOGGER.error(f"An unexpected error : {type(e).__name__} - {e}")
            raise e

    #### DEL
    def server_exists(self, instance_id):
        try:
            ret = self.get_server(instance_id)
        except Exception as e:
            self.__LOGGER.debug(f"Server return exception : {e}")
            return False
        
        self.__LOGGER.debug(f"Server return status : {ret}")
        return True
    ####

    def switch_on_device(self, device_id):
        try:
            if isinstance(device_id, Server):
                instance = device_id
            else:
                instance = self.get_server(device_id)
            return self.client.servers.start(instance).request_ids
        except (nex.MethodNotAllowed, nex.Forbidden) as e:
            self.__LOGGER.error(f"Switch instance '{device_id}' ON not allowed with current credentials: {type(e).__name__} - {e}")
            return e
        except Exception as e:
            self.__LOGGER.debug(f"Device switch on exception : {e}")
            raise e

    def switch_off_device(self, device_id):
        try:
            if isinstance(device_id, Server):
                instance = device_id
            else:
                instance = self.get_server(device_id)
            return self.client.servers.stop(instance).request_ids
        except (nex.MethodNotAllowed, nex.Forbidden) as e:
            self.__LOGGER.error(f"Switch instance '{device_id}' OFF not allowed with current credentials: {type(e).__name__} - {e}")
            return e
        except Exception as e:
            self.__LOGGER.debug(f"Device switch off exception : {e}")
            raise e

    def suspend_device(self, device_id):
        try:
            if isinstance(device_id, Server):
                instance = device_id
            else:
                instance = self.get_server(device_id)
            return self.client.servers.suspend(instance).request_ids
        except (nex.MethodNotAllowed, nex.Forbidden) as e:
            self.__LOGGER.error(f"Suspend instance '{device_id}' not allowed with current credentials: {type(e).__name__} - {e}")
            return e
        except Exception as e:
            self.__LOGGER.debug(f"Device suspend exception : {e}")
            raise e

    def resume_device(self, device_id):
        try:
            if isinstance(device_id, Server):
                instance = device_id
            else:
                instance = self.get_server(device_id)
            return self.client.servers.resume(instance).request_ids
        except (nex.MethodNotAllowed, nex.Forbidden) as e:
            self.__LOGGER.error(f"Resume instance '{device_id}' not allowed with current credentials: {type(e).__name__} - {e}")
            return e
        except Exception as e:
            self.__LOGGER.debug(f"Device resume exception : {e}")
            raise e

    def destroy_device(self, device_id):
        try:
            if isinstance(device_id, Server):
                instance = device_id
            else:
                instance = self.get_server(device_id)
            return self.client.servers.delete(instance).request_ids
        except (nex.MethodNotAllowed, nex.Forbidden) as e:
            self.__LOGGER.error(f"Delete instance '{device_id}' not allowed with current credentials: {type(e).__name__} - {e}")
            return e
        except Exception as e:
            self.__LOGGER.debug(f"Device destroy exception : {e}")
            raise e

    # NOTE: only specify user if using an admin session
    def create_keypair(self, name, public_key=None, key_type='ssh', user=None):
        try:
            return self.client.keypairs.create(name, public_key=public_key, key_type=key_type, user_id=user)
        # TODO: except whatever is thrown if versioning is off
        except Exception as e:
            self.__LOGGER.error(f"An unexpected error : {type(e).__name__} - {e}")
            raise e

    # NOTE: only specify user if using an admin session
    def get_keypair(self, keypair, user=None):
        try:
            return self.client.keypairs.get(keypair, user_id=user)
        # TODO: except whatever is thrown if versioning is off
        except Exception as e:
            self.__LOGGER.error(f"An unexpected error : {type(e).__name__} - {e}")
            raise e

    # NOTE: only specify user if using an admin session
    def list_keypairs(self, keypair, user=None):
        try:
            return self.client.keypairs.list(keypair, user_id=user)
        # TODO: except whatever is thrown if versioning is off
        except Exception as e:
            self.__LOGGER.error(f"An unexpected error : {type(e).__name__} - {e}")
            raise e

    # NOTE: only specify user if using an admin session
    def delete_keypair(self, keypair, user=None):
        try:
            return self.client.keypairs.delete(keypair, user_id=user)
        # TODO: except whatever is thrown if versioning is off
        except Exception as e:
            self.__LOGGER.error(f"An unexpected error : {type(e).__name__} - {e}")
            raise e

    def close(self):
        self.__LOGGER.debug("Closing Nova Client Connection")
        self.client = None
        super().close()
