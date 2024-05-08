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

from abc import ABC, abstractmethod

class Component(ABC):
    """
    Basic Component representation:
            Components are objects that are used to handle the
            different aspects of a client when needed. (An
            example being Nova for Openstack)

            A Client will be made of 0 or more Components
    """

    @abstractmethod
    def get_connection_obj(self):
        """
        Function to create a connection to the Component
        """

    @abstractmethod
    def disconnect(self):
        """
        Function for disconnecting all streams before garbage collection.
        """

class QueueComponent(Component):
    """
    QueueComponent representation:
            QueueComponents are a specialized type of Component
            meant to handle communication with a Cloud Client's
            messaging queue if necessary.
    """

    @abstractmethod
    def get_connection_obj(self):
        """
        Function to create a connection channel to the Queue
        """

    @abstractmethod
    def start_listening(self):
        """
        Function that is first called on the Component
        to begin listening to the queue for messages
        """

    @abstractmethod
    def handle_message(self):
        """
        The main function of the Component. Used
        to house the logic for parsing the message and
        performing the necessary action in the Client.
        """
