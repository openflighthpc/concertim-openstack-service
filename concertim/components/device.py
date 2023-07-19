from concertim.concertim import ConcertimData

class ConcertimDevice:
    def __init__(self, openstack_instance_id, openstack_instance_name, device_name, start_u, end_u, facing, depth, device_id, rack_id):
        self.__openstack_instance_id = openstack_instance_id
        self.__openstack_instance_name = openstack_instance_name
        self.__device_name = device_name
        self.__template_id = None
        self.__device_id = device_id
        self.__start_u = start_u
        self.__end_u = end_u
        self.__facing = facing
        self.__depth = depth
        self.__rack_id = rack_id
        self.__status = None

    def __repr__(self):
        lines = ['\n' + self.__class__.__name__ + ':']
        for key, val in vars(self).items():
            lines += '{}: {}'.format(key, val.__repr__()).split('\n')
        return '{' + '\n '.join(lines) + '}'
    
    @property
    def instance_id(self):
        return self.__instance_id

    @property
    def instance_name(self):
        return self.__instance_name

    @instance_name.setter
    def instance_name(self, value):
        self.__instance_name = value

    @property
    def status(self):
        return self.__status

    @instance_name.setter
    def status(self, value):
        self.__status = value

    @property
    def device_name(self):
        return self.__device_name

    @device_name.setter
    def device_name(self, value):
        self.__device_name = value

    @property
    def project_id(self):
        return self.__project_id

    @property
    def flavor_id(self):
        return self.__flavor_id

    @flavor_id.setter
    def flavor_id(self, value):
        self.__flavor_id = value
    
    @property
    def template_id(self):
        return self.__template_id

    @template_id.setter
    def template_id(self, value):
        self.__template_id = value

    @property
    def device_id(self):
        return self.__device_id

    @device_id.setter
    def device_id(self, value):
        self.__device_id = value

    @property
    def cluster_name(self):
        return self.__cluster_name

    @cluster_name.setter
    def cluster_name(self, value):
        self.__cluster_name = value

    @property
    def rack_id(self):
        return self.__rack_id

    @rack_id.setter
    def rack_id(self, value):
        self.__rack_id = value

    @property
    def start_u(self):
        return self.__start_u

    @start_u.setter
    def start_u(self, value):
        self.__start_u = value

    @property
    def depth(self):
        return self.__depth

    @depth.setter
    def depth(self, value):
        self.__depth = value
