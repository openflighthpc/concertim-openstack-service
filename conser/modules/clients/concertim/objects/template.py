class ConcertimTemplate(object):
    def __init__(self, 
        concertim_id=None, 
        cloud_id=None, 
        concertim_name=None, 
        cloud_name=None, 
        ram=None, 
        disk=None, 
        vcpus=None, 
        size=None, 
        description=''
    ):
        self.id = tuple((concertim_id, cloud_id))
        self.name = tuple((concertim_name, cloud_name))
        self.description = description
        self.ram = ram
        self.disk = disk
        self.vcpus = vcpus
        self.size = size

    def __repr__(self):
        return (
            f"<ConcertimTemplate:{{ \
                id:{repr(self.id)}, \
                name:{repr(self.name)}, \
                description:{repr(self.description)}, \
                size:{repr(self.size)}, \
                vcpus:{repr(self.vcpus)}, \
                disk:{repr(self.disk)}, \
                ram:{repr(self.ram)}}}>"
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