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
        description='',
        tag=None
    ):
        self.id = tuple((concertim_id, cloud_id))
        self.name = tuple((concertim_name, cloud_name))
        self.description = description
        self.ram = ram
        self.disk = disk
        self.vcpus = vcpus
        self.size = size
        self.tag = tag
        self._updated=False

    def __repr__(self):
        return (
            f"<ConcertimTemplate:{{ "
                f"id:{repr(self.id)}, "
                f"name:{repr(self.name)}, "
                f"description:{repr(self.description)}, "
                f"size:{repr(self.size)}, "
                f"vcpus:{repr(self.vcpus)}, "
                f"disk:{repr(self.disk)}, "
                f"ram:{repr(self.ram)}, "
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
