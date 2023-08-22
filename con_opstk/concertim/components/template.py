from con_opstk.concertim.components.component import ConcertimComponent

class ConcertimTemplate(ConcertimComponent):
    def __init__(self, concertim_id=None, openstack_id=None, concertim_name=None, openstack_name=None, ram=None, disk=None, vcpus=None, size=None, description=''):
        super().__init__(concertim_id=concertim_id, openstack_id=openstack_id, concertim_name=concertim_name, openstack_name=openstack_name, description=description)
        self.ram = ram
        self.disk = disk
        self.vcpus = vcpus
        self.size = size

    def __repr__(self):
        opsk_info = super().get_openstack_definition()
        con_info = super().get_concertim_definition()
        return (f"ConcertimTemplate{{openstack_info:{repr(opsk_info)}, concertim_info:{repr(con_info)}, description:{repr(self.description)}, size:{repr(self.size)}, "
                f"vcpus:{repr(self.vcpus)}, disk:{repr(self.disk)}, ram:{repr(self.ram)}}}")
    
    def __eq__(self, other):
        if isinstance(other, ConcertimTemplate):
            return (self.concertim_id == other.concertim_id 
                and self.openstack_id == other.openstack_id)
        return NotImplemented

    def __ne__(self, other):
        temp = self.__eq__(other)
        if temp is NotImplemented:
            return NotImplemented
        return not temp
