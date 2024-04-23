class ConcertimTeam(object):
    def __init__(self, 
        concertim_id=None, 
        cloud_id=None, 
        billing_id=None,
        concertim_name=None, 
        cloud_name=None, 
        description=''
    ):
        self.id = tuple((concertim_id, cloud_id, billing_id))
        self.name = tuple((concertim_name, cloud_name))
        self.description = description
        self.racks = []
        self.team_members = []
        self.team_admins = []
        self._primary_billing_user_cloud_id = None
        self.billing_period_start = ''
        self.billing_period_end = ''
        self.cost = 0.0
        self.credits = 0.0

    def __repr__(self):
        return (
            f"<ConcertimTeam:{{ "
                f"id:{repr(self.id)}, "
                f"name:{repr(self.name)}, "
                f"description:{repr(self.description)}, "
                f"team_members:{repr(self.team_members)}, "
                f"team_admins:{repr(self.team_admins)}, "
                f"_primary_billing_user_cloud_id:{repr(self._primary_billing_user_cloud_id)}, "
                f"billing_period_start:{repr(self.billing_period_start)}, "
                f"billing_period_end:{repr(self.billing_period_end)}, "
                f"credits:{repr(self.credits)}, "
                f"cost:{repr(self.cost)}}}>"
        )

    def __eq__(self, other):
        if isinstance(other, ConcertimUser):
            return (
                self.id[0] == other.id[0] 
                and self.id[1] == other.id[1]
                and self.id[2] == other.id[2]
                and self.team_members == other.team_members
                and self.team_admins == other.team_admins
            )
        return NotImplemented

    def __ne__(self, other):
        temp = self.__eq__(other)
        if temp is NotImplemented:
            return NotImplemented
        return not temp

    def add_member(self, user_id_tup):
        self.team_members.append(user_id_tup)

    def remove_member(self, user_id_tup):
        self.team_members.remove(user_id_tup)

    def add_admin(self, user_id_tup):
        self.team_admins.append(user_id_tup)

    def remove_admin(self, user_id_tup):
        self.team_admins.remove(user_id_tup)

    def add_rack(self, rack_concertim_id):
        self.racks.append(rack_concertim_id)

    def remove_rack(self, rack_concertim_id):
        self.racks.remove(rack_concertim_id)
