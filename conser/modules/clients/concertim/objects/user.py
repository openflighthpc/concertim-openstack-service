class ConcertimUser(object):
    def __init__(self, 
        concertim_id=None, 
        cloud_id=None, 
        billing_id=None,
        concertim_name=None, 
        cloud_name=None, 
        full_name=None, 
        email=None, 
        default_project_cloud_id=None, 
        description='', 
    ):
        self.id = tuple((concertim_id, cloud_id, billing_id))
        self.name = tuple((concertim_name, cloud_name))
        self.description = description
        self.full_name = full_name
        self.email = email
        self.default_project_cloud_id = default_project_cloud_id
        self.admin_projects_cloud_ids = []
        self.racks = []
        self.billing_period_start = ''
        self.billing_period_end = ''
        self.cost = 0.0
        self.credits = 0.0

    def __repr__(self):
        return (
            f"<ConcertimUser:{{ "
                f"id:{repr(self.id)}, "
                f"name:{repr(self.name)}, "
                f"description:{repr(self.description)}, "
                f"full_name:{repr(self.full_name)}, "
                f"email:{repr(self.email)}, "
                f"default_project_cloud_id:{repr(self.default_project_cloud_id)}, "
                f"admin_projects_cloud_ids:{repr(self.admin_projects_cloud_ids)}, "
                f"billing_period_start:{repr(self.billing_period_start)}, "
                f"billing_period_end:{repr(self.billing_period_end)}, "
                f"cost:{repr(self.cost)}, "
                f"credits:{repr(self.credits)}, "
                f"racks:{repr(self.racks)}}}>"
        )

    def __eq__(self, other):
        if isinstance(other, ConcertimUser):
            return (
                self.id[0] == other.id[0] 
                and self.id[1] == other.id[1]
                and self.id[2] == other.id[2]
                and self.default_project_cloud_id == other.default_project_cloud_id
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
