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
import time
# Openstack Packages
from neutronclient.v2_0 import client as n_client


class NeutronComponent(OpstkBaseComponent):
    def __init__(self, sess, log_file, log_level):
        super().__init__(sess, log_file, log_level)
        self.__LOGGER = create_logger(__name__, self._LOG_FILE, self._LOG_LEVEL)
        self.__LOGGER.info("CREATING NEUTRON COMPONENT")
        self.client = self.get_connection_obj(self._SESSION)

    def get_connection_obj(self, sess):
        start_time = time.time()
        error = None
        while time.time() - start_time < 30:  # Try for up to 30 seconds
            try:
                client = n_client.Client(session=sess)
                self.__LOGGER.debug("SUCCESS - Neutron client connected")
                return client # Exit if client creation is successful
            except Exception as e:
                self.__LOGGER.warning(f"Failed to create Neutron client: {type(e).__name__} - {e} - Retrying...")
                error = e
                time.sleep(1)  # Wait for a second before retrying
        self.__LOGGER.error(f"Failed to create Neutron client after multiple attempts : {type(error).__name__} - {error}")
        raise error

    def get_network(self, network_id):
        return self.client.show_network(network_id)

    def get_project_quotas(self, project_id):
        try:
            return self.client.show_quota(project_id)
        except Exception as e:
            self.__LOGGER.error(f"An unexpected error : {type(e).__name__} - {e}")
            raise e
