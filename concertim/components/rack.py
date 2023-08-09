from concertim.components.component import ConcertimComponent

class ConcertimRack(ConcertimComponent):
    def __init__(self, concertim_id=None, openstack_id=None, concertim_name=None, openstack_name=None, user_id=None, height=42, description='', status=None):
        super().__init__(concertim_id=concertim_id, openstack_id=openstack_id, concertim_name=concertim_name, openstack_name=openstack_name, description=description)
        self.user_id = user_id
        self.height = height
        self.devices = []
        self.status = status
        self._occupied = []
        self.output = []
        self.metadata = {}

    def __repr__(self):
        opsk_info = super().get_openstack_definition()
        con_info = super().get_concertim_definition()
        return (f"ConcertimRack{{openstack_info:{repr(opsk_info)}, concertim_info:{repr(con_info)}, description:{repr(self.description)}, status:{repr(self.status)}, "
                f"user_id:{repr(self.user_id)}, height:{repr(self.height)}, devices:{repr(self.devices)}, output:{repr(self.output)}, "
                f"metadata:{repr(self.metadata)}, occupied:{repr(self._occupied)}}}")

    def __eq__(self, other):
        if isinstance(other, ConcertimRack):
            return (self.concertim_id == other.concertim_id 
                and self.openstack_id == other.openstack_id 
                and self.height == other.height)
        return NotImplemented

    def __ne__(self, other):
        temp = self.__eq__(other)
        if temp is NotImplemented:
            return NotImplemented
        return not temp

    def add_metadata(self, **kwargs):
        for k,v in kwargs.items():
            self.metadata[k] = v

    def add_device(self, device_concertim_id, location):
        self.devices.append(device_concertim_id)
        self._occupied.extend([x for x in range(location.start_u, location.end_u+1)])

    def remove_device(self, device_concertim_id, location):
        self.devices.remove(device_concertim_id)
        self._occupied.remove([x for x in range(location.start_u, location.end_u+1)])
