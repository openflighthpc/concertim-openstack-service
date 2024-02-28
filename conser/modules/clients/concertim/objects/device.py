from typing import Any


class ConcertimDevice(object):
    def __init__(self, 
        concertim_id=None, 
        cloud_id=None, 
        concertim_name=None, 
        cloud_name=None, 
        rack_id_tuple=None, 
        template=None, 
        location=None, 
        description='', 
        status=None
    ):
        self.id = tuple((concertim_id, cloud_id))
        self.name = tuple((concertim_name, cloud_name))
        self.description = description
        self.rack_id_tuple = rack_id_tuple
        self.template = template
        self.location = location
        self.status = status
        self.network_interfaces = []
        self.details = DeviceDetails()
        self.cost = 0.0
        self._delete_marker = True
        self._updated = False

    def __repr__(self):
        return (
            f"<ConcertimDevice:{{ \
                id:{repr(self.id)}, \
                name:{repr(self.name)}, \
                description:{repr(self.description)}, \
                status:{repr(self.status)}, \
                rack_id_tuple:{repr(self.rack_id_tuple)}, \
                template:{repr(self.template)}, \
                location:{repr(self.location)}, \
                network_interfaces:{repr(self.network_interfaces)}, \
                cost:{repr(self.cost)}}}, \
                details:{repr(self.details)} \
                >"
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


class DeviceDetails(object):

    def __init__(self, attrs) -> None:
        self._attrs = attrs

    def __getattribute__(self, name: str) -> Any:
        return self._attrs.get(name)

    def __setattr__(self, name: str, value: Any) -> None:
        self._attrs[name] = value

    def __repr__(self) -> str:
        return (f"<DeviceDetails
                  {'\n'.join(map(lambda k,v: f'{k}: {repr(v)}', self._attrs.entries()))}
                >")
