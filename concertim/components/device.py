class ConcertimDevice:
    __slots__ = ('__instance_id', '__instance_name', '__device_name', '__project_id', '__flavor_id', '__template_id','__device_id', '__cluster_name', '__rack_id', '__rack_start_u')
    def __init__(self, instance_id, instance_name, device_name, project_id, flavor_id, template_id, cluster_name):
        self.__instance_id = instance_id
        self.__instance_name = instance_name
        self.__device_name = device_name
        self.__project_id = project_id
        self.__flavor_id = flavor_id
        self.__template_id = template_id
        self.__device_id = None
        self.__cluster_name = cluster_name
        self.__rack_id = None
        self.__rack_start_u = None

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
    def device_name(self):
        return self.__instance_name

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
    def rack_start_u(self):
        return self.__rack_start_u

    @rack_start_u.setter
    def rack_start_u(self, value):
        self.__rack_start_u = value
