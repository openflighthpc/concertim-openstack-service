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
from conser.modules.clients.cloud.openstack.components.base import OpstkBaseComponent
# Py Packages
import sys
import time
# Openstack Packages
import novaclient.client as n_client
import novaclient.exceptions as nex
from novaclient.v2.servers import Server

class NovaComponent(OpstkBaseComponent):
    def __init__(self, sess, log_file, log_level):
        super().__init__(sess, log_file, log_level)
        self.__LOGGER = create_logger(__name__, self._LOG_FILE, self._LOG_LEVEL)
        self.__LOGGER.info("CREATING NOVA COMPONENT")
        self.client = self.get_connection_obj(self._SESSION)

    def get_connection_obj(self, sess):
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

    def switch_on_instance(self, instance_id):
        try:
            return self.client.servers.start(instance_id)
        except (nex.MethodNotAllowed, nex.Forbidden) as e:
            self.__LOGGER.error(f"Switch instance '{instance_id}' ON not allowed with current credentials: {type(e).__name__} - {e}")
            return e
        except Exception as e:
            self.__LOGGER.debug(f"Device switch on exception : {e}")
            raise e

    def switch_off_instance(self, instance_id):
        try:
            return self.client.servers.stop(instance_id)
        except (nex.MethodNotAllowed, nex.Forbidden) as e:
            self.__LOGGER.error(f"Switch instance '{instance_id}' OFF not allowed with current credentials: {type(e).__name__} - {e}")
            return e
        except Exception as e:
            self.__LOGGER.debug(f"Device switch off exception : {e}")
            raise e

    def suspend_instance(self, instance_id):
        try:
            return self.client.servers.suspend(instance_id)
        except (nex.MethodNotAllowed, nex.Forbidden) as e:
            self.__LOGGER.error(f"Suspend instance '{instance_id}' not allowed with current credentials: {type(e).__name__} - {e}")
            return e
        except Exception as e:
            self.__LOGGER.debug(f"Device suspend exception : {e}")
            raise e

    def resume_instance(self, instance_id):
        try:
            return self.client.servers.resume(instance_id)
        except (nex.MethodNotAllowed, nex.Forbidden) as e:
            self.__LOGGER.error(f"Resume instance '{instance_id}' not allowed with current credentials: {type(e).__name__} - {e}")
            return e
        except Exception as e:
            self.__LOGGER.debug(f"Device resume exception : {e}")
            raise e

    def destroy_instance(self, instance_id):
        try:
            return self.client.servers.delete(instance_id)
        except (nex.MethodNotAllowed, nex.Forbidden) as e:
            self.__LOGGER.error(f"Delete instance '{instance_id}' not allowed with current credentials: {type(e).__name__} - {e}")
            return e
        except Exception as e:
            self.__LOGGER.debug(f"Device destroy exception : {e}")
            raise e

    def create_keypair(self, name, public_key=None, key_type='ssh', user_id=None):
        try:
            # key_type not supported for novaclient - add handling
            # user_id also not supported
            return self.client.keypairs.create(name, public_key=public_key)
        except Exception as e:
            self.__LOGGER.error(f"An unexpected error : {type(e).__name__} - {e}")
            raise e

    def get_keypair(self, keypair_name, user_id=None):
        try:
            return self.client.keypairs.get(keypair_name, user_id=user_id)
        except Exception as e:
            self.__LOGGER.error(f"An unexpected error : {type(e).__name__} - {e}")
            raise e

    def list_keypairs(self):
        try:
            return self.client.keypairs.list()
        except Exception as e:
            self.__LOGGER.error(f"An unexpected error : {type(e).__name__} - {e}")
            raise e

    def delete_keypair(self, keypair):
        try:
            return self.client.keypairs.delete(keypair)
        except Exception as e:
            self.__LOGGER.error(f"An unexpected error : {type(e).__name__} - {e}")
            raise e

    def get_cloud_stats(self):
        try:
            return self.client.hypervisor_stats.statistics()
        except Exception as e:
            self.__LOGGER.error(f"An unexpected error : {type(e).__name__} - {e}")
            raise e

    def get_project_quotas(self, project_id):
        try:
            return self.client.quotas.get(project_id)
        except Exception as e:
            self.__LOGGER.error(f"An unexpected error : {type(e).__name__} - {e}")
            raise e

    def disconnect(self):
        self.__LOGGER.debug("Disconnecting Nova Component Connection")
        self.client = None
        super().disconnect()