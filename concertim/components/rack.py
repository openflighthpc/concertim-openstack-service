class ConcertimRack:
    __slots__ = ('__rack_name','__owner','__devices','__rack_id','__rack_height', '__project_id', '__cluster','__occupied')
    def __init__(self, rack_name, owner, rack_height, cluster, project_id, rack_id='', devices=[]):
        self.__rack_name = rack_name
        self.__owner = owner
        self.__devices = devices
        self.__rack_id = rack_id
        self.__rack_height = rack_height
        self.__project_id = project_id
        self.__cluster = cluster
        self.__occupied = []

    @property
    def rack_name(self):
        return self.__rack_name

    @rack_name.setter
    def rack_name(self, new_rack_name):
        self.__rack_name = new_rack_name

    @property
    def owner(self):
        return self.__owner

    @property
    def devices(self):
        return self.__devices

    @devices.setter
    def devices(self, new_devices):
        self.__devices = new_devices

    @property
    def project_id(self):
        return self.__project_id

    @project_id.setter
    def project_id(self, value):
        self.__project_id = value

    @property
    def rack_id(self):
        return self.__rack_id

    @rack_id.setter
    def rack_id(self, new_rack_id):
        self.__rack_id = new_rack_id

    @property
    def rack_height(self):
        return self.__rack_height

    @rack_height.setter
    def rack_height(self, new_rack_height):
        self.__rack_height = new_rack_height

    @property
    def cluster(self):
        return self.__cluster

    @cluster.setter
    def cluster(self, new_cluster):
        self.__cluster = new_cluster

    @property
    def occupied(self):
        return self.__occupied

    @occupied.setter
    def occupied(self, value):
        self.__occupied = value
    
