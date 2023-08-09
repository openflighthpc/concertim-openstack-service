class ConcertimComponent(object):
    def __init__(self, concertim_id=None, openstack_id=None, concertim_name=None, openstack_name=None, desc=''):
        self.id = (concertim_id,openstack_id)
        self.name = (concertim_name,openstack_name)
        self.description = desc

    def __repr__(self):
        opsk_info = self.get_openstack_definition()
        con_info = self.get_concertim_definition()
        return f"ConcertimComponent{{openstack_info:{repr(opsk_info)}, concertim_info:{repr(con_info)}, description:{repr(self.description)}}}"

    def __eq__(self, other):
        if isinstance(other, ConcertimComponent):
            return (self.concertim_id == other.concertim_id 
                and self.openstack_id == other.openstack_id)
        return NotImplemented

    def __ne__(self, other):
        temp = self.__eq__(other)
        if temp is NotImplemented:
            return NotImplemented
        return not temp

    def get_openstack_definition(self):
        return {'id':self.id[1],'name':self.name[1]}

    def get_concertim_definition(self):
        return {'id':self.id[0],'name':self.name[0]}