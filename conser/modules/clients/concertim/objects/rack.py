class ConcertimRack(object):
    def __init__(self, 
        concertim_id=None, 
        cloud_id=None, 
        billing_id=None,
        concertim_name=None, 
        cloud_name=None, 
        user_id=None, 
        height=42, 
        description='', 
        status=None
    ):
        self.id = tuple((concertim_id, cloud_id, billing_id))
        self.name = tuple((concertim_name, cloud_name))
        self.description = description
        self.user_id = user_id
        self.height = height
        self.devices = []
        self.status = status
        self._occupied = []
        self.output = []
        self._creation_output = ''
        self.network_details = {}
        self.metadata = {}
        self.cost = 0.0

    def __repr__(self):
        return (
            f"<ConcertimRack:{{ \
                id:{repr(self.id)}, \
                name:{repr(self.name)}, \
                description:{repr(self.description)}, \
                status:{repr(self.status)}, \
                user_id:{repr(self.user_id)}, \ 
                height:{repr(self.height)}, \
                devices:{repr(self.devices)}, \
                output:{repr(self.output)}, \
                network_details:{repr(self.network_details)}, \
                metadata:{repr(self.metadata)}, \
                cost:{repr(self.cost)}, \
                _occupied:{repr(self._occupied)}, \
                _creation_output:{repr(self._creation_output)}}}>"
        )

    def __eq__(self, other):
        if isinstance(other, ConcertimRack):
            return (
                self.id[0] == other.id[0] 
                and self.id[1] == other.id[1]
                and self.id[2] == other.id[2]
                and self.height == other.height
            )
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