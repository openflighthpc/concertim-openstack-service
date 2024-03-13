class ConcertimUser(object):
    def __init__(self, 
        concertim_id=None, 
        cloud_id=None,
        concertim_name=None,
        cloud_name=None,
        full_name=None,
        email=None,
        description='', 
    ):
        self.id = tuple((concertim_id, cloud_id))
        self.name = tuple((concertim_name, cloud_name))
        self.description = description
        self.full_name = full_name
        self.email = email
        self.admin_projects_cloud_ids = []

    def __repr__(self):
        return (
            f"<ConcertimUser:{{ "
                f"id:{repr(self.id)}, "
                f"name:{repr(self.name)}, "
                f"description:{repr(self.description)}, "
                f"full_name:{repr(self.full_name)}, "
                f"email:{repr(self.email)}, "
                f"admin_projects_cloud_ids:{repr(self.admin_projects_cloud_ids)}}}>"
        )

    def __eq__(self, other):
        if isinstance(other, ConcertimUser):
            return (
                self.id[0] == other.id[0] 
                and self.id[1] == other.id[1]
                and self.id[2] == other.id[2]
            )
        return NotImplemented

    def __ne__(self, other):
        temp = self.__eq__(other)
        if temp is NotImplemented:
            return NotImplemented
        return not temp
