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

class ConcertimTemplate(object):
    def __init__(self, 
        concertim_id=None, 
        cloud_id=None, 
        concertim_name=None, 
        cloud_name=None, 
        ram=None, 
        disk=None,
        vcpus=None,
        height=None,
        description='',
        tag=None,
        hourly_cost=None,
    ):
        self.id = tuple((concertim_id, cloud_id))
        self.name = tuple((concertim_name, cloud_name))
        self.description = description
        self.ram = ram
        self.disk = disk
        self.vcpus = vcpus
        self.height = height
        self.tag = tag
        self.hourly_cost = hourly_cost
        self._updated=False

    def __repr__(self):
        return (
            f"<ConcertimTemplate:{{ "
                f"id:{repr(self.id)}, "
                f"name:{repr(self.name)}, "
                f"description:{repr(self.description)}, "
                f"height:{repr(self.height)}, "
                f"vcpus:{repr(self.vcpus)}, "
                f"disk:{repr(self.disk)}, "
                f"ram:{repr(self.ram)}, "
                f"hourly_cost:{repr(self.hourly_cost)}, "
                f"tag:{repr(self.tag)}}}>"
        )
    
    def __eq__(self, other):
        if isinstance(other, ConcertimTemplate):
            return (self.id[0] == other.id[0] 
                and self.id[1] == other.id[1])
        return NotImplemented

    def __ne__(self, other):
        temp = self.__eq__(other)
        if temp is NotImplemented:
            return NotImplemented
        return not temp
