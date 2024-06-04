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

class ConcertimDevice(object):
    def __init__(self,
        concertim_id=None,
        cloud_id=None,
        type=None,
        concertim_name=None,
        cloud_name=None,
        rack_id_tuple=None,
        template=None,
        location=None,
        description='',
        status=None,
        cost=0.0,
        created_at=None,
    ):
        self.id = tuple((concertim_id, cloud_id))
        self.name = tuple((concertim_name, cloud_name))
        self.type = type
        self.description = description
        self.rack_id_tuple = rack_id_tuple
        self.template = template
        self.location = location
        self.status = status
        self.network_interfaces = []
        self.cost = cost
        self.created_at = created_at

        self.details = {}

        self._delete_marker = True
        self._updated = False

    def __repr__(self):
        return (
            f"<ConcertimDevice:{{ "
                f"id:{repr(self.id)}, "
                f"name:{repr(self.name)}, "
                f"type: {repr(self.type)}, "
                f"created: {repr(self.created_at)}, "
                f"description:{repr(self.description)}, "
                f"status:{repr(self.status)}, "
                f"rack_id_tuple:{repr(self.rack_id_tuple)}, "
                f"template:{repr(self.template)}, "
                f"location:{repr(self.location)}, "
                f"network_interfaces:{repr(self.network_interfaces)}, "
                f"cost:{repr(self.cost)}, "
                f"details:{repr(self.details)}}}>"
        )

    def __eq__(self, other):
        if isinstance(other, ConcertimDevice):
            return (
                self.id[0] == other.id[0] 
                and self.id[1] == other.id[1]
                and self.rack_id_tuple == other.rack_id_tuple
            )
        return NotImplemented

    def __ne__(self, other):
        temp = self.__eq__(other)
        if temp is NotImplemented:
            return NotImplemented
        return not temp

    def add_metadata(self, **kwargs):
        for k,v in kwargs.items():
            self.metadata[str(k)] = v
