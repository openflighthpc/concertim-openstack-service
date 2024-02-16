from con_opstk.concertim.components.component import ConcertimComponent

class ConcertimUser(ConcertimComponent):
    def __init__(self, concertim_id=None, openstack_id=None, concertim_name=None, openstack_name=None, full_name=None, email=None, description=''):
        super().__init__(concertim_id=concertim_id, openstack_id=openstack_id, concertim_name=concertim_name, openstack_name=openstack_name, description=description)
        self.full_name = full_name
        self.email = email

    def __repr__(self):
        return (f"<ConcertimUser:{{id:{repr(self.id)}, name:{repr(self.name)}, description:{repr(self.description)}, "
                f"full_name:{repr(self.full_name)}, email:{repr(self.email)}}}>")

    def __eq__(self, other):
        if isinstance(other, ConcertimUser):
            return (self.id[0] == other.id[0]
                and self.id[1] == other.id[1])
        return NotImplemented

    def __ne__(self, other):
        temp = self.__eq__(other)
        if temp is NotImplemented:
            return NotImplemented
        return not temp
