from concertim.components.component import ConcertimComponent

class ConcertimUser(ConcertimComponent):
    def __init__(self, concertim_id=None, openstack_id=None, concertim_name=None, openstack_name=None, full_name=None, email=None, openstack_project_id=None, desc=''):
        super().__init__(concertim_id=concertim_id, openstack_id=openstack_id, concertim_name=concertim_name, openstack_name=openstack_name, description=desc)
        self.full_name = full_name
        self.email = email
        self.openstack_project_id = openstack_project_id
        self.racks = []

    def __repr__(self):
        opsk_info = super().get_openstack_definition()
        con_info = super().get_concertim_definition()
        return (f"ConcertimUser{{openstack_info:{repr(opsk_info)}, concertim_info:{repr(con_info)}, description:{repr(self.description)}, "
                f"full_name:{repr(self.full_name)}, email:{repr(self.email)}, openstack_project_id:{repr(self.openstack_project_id)},racks:{repr(self.racks)}}}")

    def __eq__(self, other):
        if isinstance(other, ConcertimUser):
            return (self.concertim_id == other.concertim_id 
                and self.openstack_id == other.openstack_id 
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