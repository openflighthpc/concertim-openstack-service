from concertim.components.component import ConcertimComponent

class ConcertimDevice(ConcertimComponent):
    def __init__(self, concertim_id=None, openstack_id=None, concertim_name=None, openstack_name=None, rack_id=None, template=None, location=None, description='', status=None):
        super().__init__(concertim_id=concertim_id, openstack_id=openstack_id, concertim_name=concertim_name, openstack_name=openstack_name, description=description)
        self.rack_id = rack_id
        self.template = template
        self.location = location
        self.status = status
        self.ips = []
        self.ssh_key = ''
        self.volumes_attached = []

    def __repr__(self):
        opsk_info = super().get_openstack_definition()
        con_info = super().get_concertim_definition()
        return (f"ConcertimDevice{{openstack_info:{repr(opsk_info)}, concertim_info:{repr(con_info)}, description:{repr(self.description)}, status:{repr(self.status)}, "
                f"rack_id:{repr(self.rack_id)}, template:{repr(self.template)}, location:{repr(self.location)}, IPs:{repr(self.ips)}, ssh_key:{repr(self.ssh_key)}, "
                f"volumes_attached:{repr(self.volumes_attached)}}}")

    def __eq__(self, other):
        if isinstance(other, ConcertimDevice):
            return (self.concertim_id == other.concertim_id 
                and self.openstack_id == other.openstack_id 
                and self.rack_id == other.rack_id)
        return NotImplemented

    def __ne__(self, other):
        temp = self.__eq__(other)
        if temp is NotImplemented:
            return NotImplemented
        return not temp

    def add_metadata(self, **kwargs):
        for k,v in kwargs.items():
            self.metadata[str(k)] = v

    
