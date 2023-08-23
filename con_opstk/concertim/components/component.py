class ConcertimComponent(object):
    def __init__(self, concertim_id=None, openstack_id=None, concertim_name=None, openstack_name=None, description=''):
        self.id = tuple((concertim_id,openstack_id))
        self.name = tuple((concertim_name,openstack_name))
        self.description = description

    def __repr__(self):
        return f"<ConcertimComponent:{{id:{repr(self.id)}, name:{repr(self.name)}, description:{repr(self.description)}}}>"

    def __eq__(self, other):
        if isinstance(other, ConcertimComponent):
            return (self.id[0] == other.id[0] 
                and self.id[1] == other.id[1])
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