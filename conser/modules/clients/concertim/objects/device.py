class ConcertimDevice(object):
    def __init__(self, 
        concertim_id=None, 
        cloud_id=None, 
        concertim_name=None, 
        cloud_name=None, 
        rack_id=None, 
        template=None, 
        location=None, 
        description='', 
        status=None
    ):
        self.id = tuple((concertim_id, cloud_id))
        self.name = tuple((concertim_name, cloud_name))
        self.description = description
        self.rack_id = rack_id
        self.template = template
        self.location = location
        self.status = status
        self.ips = []
        self.private_ips = ''
        self.public_ips = ''
        self.ssh_key = ''
        self.volume_details = {}
        self.login_user = ''
        self.cost = 0.0

    def __repr__(self):
        return (
            f"<ConcertimDevice:{{ \
                id:{repr(self.id)}, \
                name:{repr(self.name)}, \
                description:{repr(self.description)}, \
                status:{repr(self.status)}, \
                rack_id:{repr(self.rack_id)}, \
                template:{repr(self.template)}, \
                location:{repr(self.location)}, \
                ips:{repr(self.ips)}, \
                private_ips:{repr(self.private_ips)}, \
                public_ips:{repr(self.public_ips)}, \
                ssh_key:{repr(self.ssh_key)}, \
                login_user:{repr(self.login_user)}, \
                volume_details:{repr(self.volume_details)}, \
                cost:{repr(self.cost)}}}>"
        )

    def __eq__(self, other):
        if isinstance(other, ConcertimDevice):
            return (
                self.id[0] == other.id[0] 
                and self.id[1] == other.id[1]
                and self.rack_id == other.rack_id
                and self.ssh_key == other.ssh_key
                and self.private_ips == other.private_ips
                and self.public_ips == other.public_ips
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