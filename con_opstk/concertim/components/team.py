from con_opstk.concertim.components.component import ConcertimComponent

class ConcertimTeam(ConcertimComponent):
    def __init__(self, concertim_id=None, concertim_name=None, openstack_name=None, openstack_project_id=None, description='', billing_acct_id=None):
        super().__init__(concertim_id=concertim_id, concertim_name=concertim_name, openstack_name=openstack_name, description=description)
        self.openstack_project_id = openstack_project_id
        self.racks = []
        self.billing_period_start = ''
        self.billing_period_end = ''
        self.cost = 0.0
        self.billing_acct_id = billing_acct_id

    def __repr__(self):
        return (f"<ConcertimTeam:{{id:{repr(self.id)}, name:{repr(self.name)}, description:{repr(self.description)}, "
                f"openstack_project_id:{repr(self.openstack_project_id)}, billing_acct_id:{repr(self.billing_acct_id)}, "
                f"billing_period_start:{repr(self.billing_period_start)}, billing_period_end:{repr(self.billing_period_end)}, cost:{repr(self.cost)}, racks:{repr(self.racks)}}}>")

    def __eq__(self, other):
        if isinstance(other, ConcertimTeam):
            return (self.id[0] == other.id[0]
                and self.id[1] == other.id[1]
                and self.openstack_project_id == other.openstack_project_id)
        return NotImplemented

    def __ne__(self, other):
        temp = self.__eq__(other)
        if temp is NotImplemented:
            return NotImplemented
        return not temp

    def add_rack(self, rack_concertim_id):
        self.racks.append(rack_concertim_id)

    def remove_rack(self, rack_concertim_id):
        self.racks.remove(rack_concertim_id)