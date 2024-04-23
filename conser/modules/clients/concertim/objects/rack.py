class ConcertimRack(object):
    def __init__(self, 
        concertim_id=None, 
        cloud_id=None, 
        billing_id=None,
        concertim_name=None, 
        cloud_name=None, 
        team_id_tuple=None,
        height=42, 
        description='', 
        status=None
    ):
        self.id = tuple((concertim_id, cloud_id, billing_id))
        self.name = tuple((concertim_name, cloud_name))
        self.description = description
        self.team_id_tuple = team_id_tuple
        self.height = height
        self.devices = []
        self._base_name = ''
        self.status = status
        self._status_reason = ''
        self._occupied = []
        self.output = []
        self._creation_output = ''
        self._project_cloud_id = ''
        self.network_details = {}
        self.metadata = {}
        self.cost = 0.0
        self._detailed_cost={}
        self._resources = {
                           'servers': {},
                           'volumes': {},
                           'networks': {},
                           'other': {}
                          }
        self._delete_marker = True
        self._updated = False

    def __repr__(self):
        return (
            f"<ConcertimRack:{{" 
                f"id:{repr(self.id)}, " 
                f"name:{repr(self.name)}, " 
                f"_base_name:{repr(self._base_name)}, " 
                f"_project_cloud_id:{repr(self._project_cloud_id)}, " 
                f"description:{repr(self.description)}, " 
                f"status:{repr(self.status)}, " 
                f"_status_reason:{repr(self._status_reason)}, " 
                f"team_id_tuple:{repr(self.team_id_tuple)}, "
                f"height:{repr(self.height)}, " 
                f"devices:{repr(self.devices)}, " 
                f"output:{repr(self.output)}, " 
                f"network_details:{repr(self.network_details)}, " 
                f"metadata:{repr(self.metadata)}, " 
                f"cost:{repr(self.cost)}, " 
                f"_detailed_cost:{repr(self._detailed_cost)}, " 
                f"_occupied:{repr(self._occupied)}, " 
                f"_resources:{repr(self._resources)}, " 
                f"_creation_output:{repr(self._creation_output)}}}>"
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