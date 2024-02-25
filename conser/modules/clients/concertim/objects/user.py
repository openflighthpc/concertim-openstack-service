class ConcertimUser(object):
    def __init__(self, 
        concertim_id=None, 
        cloud_id=None, 
        billing_id=None,
        concertim_name=None, 
        cloud_name=None, 
        full_name=None, 
        email=None, 
        project_cloud_id=None, 
        description='', 
    ):
        self.id = tuple((concertim_id, cloud_id, billing_id))
        self.name = tuple((concertim_name, cloud_name))
        self.description = description
        self.full_name = full_name
        self.email = email
        self.project_cloud_id = project_cloud_id
        self.racks = []
        self.billing_period_start = ''
        self.billing_period_end = ''
        self.cost = 0.0

    def __repr__(self):
        return (
            f"<ConcertimUser:{{ \
                id:{repr(self.id)}, \
                name:{repr(self.name)}, \
                description:{repr(self.description)}, \
                full_name:{repr(self.full_name)}, \
                email:{repr(self.email)}, \
                project_cloud_id:{repr(self.project_cloud_id)}, \
                billing_period_start:{repr(self.billing_period_start)}, \
                billing_period_end:{repr(self.billing_period_end)}, \
                cost:{repr(self.cost)}, \
                racks:{repr(self.racks)}}}>"
        )

    def __eq__(self, other):
        if isinstance(other, ConcertimUser):
            return (
                self.id[0] == other.id[0] 
                and self.id[1] == other.id[1]
                and self.id[2] == other.id[2]
                and self.project_cloud_id == other.project_cloud_id
            )
        return NotImplemented

    def __ne__(self, other):
        temp = self.__eq__(other)
        if temp is NotImplemented:
            return NotImplemented
        return not temp

    def add_rack(self, rack_id_tup):
        self.racks.append(rack_id_tup)

    def remove_rack(self, rack_id_tup):
        self.racks.remove(rack_id_tup)
