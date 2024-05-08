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
# Py Packages
import sys

class OpstkBaseComponent(Component):
    def __init__(self, sess, log_file, log_level):
        self._LOG_FILE = log_file
        self._LOG_LEVEL = log_level
        self.__LOGGER = create_logger(__name__, self._LOG_FILE, self._LOG_LEVEL)
        self._SESSION = sess
        self.client = None

    # Delete object(s) from Openstack
    # Returns True on success and False on fail
    # Accepts Openstack Client-based Object references (not names or ids)
    def delete(self, *args):
        try:
            self.__LOGGER.debug(f"Attempting to delete objects from Openstack")
            failed = []
            unsupported = []
            client_tree = getattr(self.client, '__module__', None)
            client_root = client_tree.split('.')[0] if client_tree else None
            for item in args:
                item_tree = getattr(item, '__module__', None)
                item_root = item_tree.split('.')[0] if item_tree else None
                if not ((client_root and item_root) and (client_root == item_root)):
                    self.__LOGGER.error(f"Attempted to delete a non-supported object - '{type(item)}:{item}' - Exception will be raised")
                    unsupported.append(f"{type(item)}:{item}")
                    continue
                ref = item.name if hasattr(item, 'name') else item.id
                try:
                    self.__LOGGER.debug(f"Attempting to delete '{ref}'")
                    module = item.__module__.split('.')[-1]
                    delete_method = getattr(getattr(self.client, module), 'delete')
                    self.__LOGGER.debug(f"Using {delete_method}")
                    delete_method(item.id)
                    self.__LOGGER.debug(f"Deleted '{ref}' successfully")
                except Exception as e:
                    self.__LOGGER.warning(f"Could not delete '{item}' : {type(e).__name__} - {e}")
                    failed.append(f"{item.__class__.__name__}:{ref}")
                    continue
            if unsupported:
                raise EXCP.UnsupportedObject(f"{unsupported}")
            if failed:
                self.__LOGGER.error(f"Failed to delete objects during most recent attempt : {failed} - check WARNINGs for more details")
                return False
            return True
        except Exception as e:
            self.__LOGGER.error(f"{type(e).__name__} - {e} - {sys.exc_info()[2].tb_frame.f_code.co_filename} - {sys.exc_info()[2].tb_lineno}")
            raise e


    def disconnect(self):
        self._SESSION = None
        self.client = None