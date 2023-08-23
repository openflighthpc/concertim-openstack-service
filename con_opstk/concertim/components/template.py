from con_opstk.concertim.components.component import ConcertimComponent

class ConcertimTemplate(ConcertimComponent):
    def __init__(self, concertim_id=None, openstack_id=None, concertim_name=None, openstack_name=None, ram=None, disk=None, vcpus=None, size=None, description=''):
        super().__init__(concertim_id=concertim_id, openstack_id=openstack_id, concertim_name=concertim_name, openstack_name=openstack_name, description=description)
        self.ram = ram
        self.disk = disk
        self.vcpus = vcpus
        self.size = size

    def __repr__(self):
        return (f"<ConcertimTemplate:{{id:{repr(self.id)}, name:{repr(self.name)}, description:{repr(self.description)}, size:{repr(self.size)}, "
                f"vcpus:{repr(self.vcpus)}, disk:{repr(self.disk)}, ram:{repr(self.ram)}}}>")
    
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
