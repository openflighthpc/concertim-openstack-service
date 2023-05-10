class ConcertimRack:
    __slots__ = ('_rack_name','_owner','_devices','_rack_id','_rack_height','_cluster')
    def __init__(self, rack_name, owner, rack_id, rack_height, cluster, devices=[]):
        self._rack_name = rack_name
        self._owner = owner
        self._devices = devices
        self._rack_id = rack_id
        self._rack_height = rack_height
        self._cluster = cluster

    @property
    def rack_name(self):
        return self._rack_name

    @rack_name.setter
    def rack_name(self, new_rack_name):
        self._rack_name = new_rack_name

    @property
    def owner(self):
        return self._owner

    @property
    def devices(self):
        return self._devices

    @devices.setter
    def devices(self, new_devices):
        self._devices = new_devices

    @property
    def rack_id(self):
        return self._rack_id

    @property
    def rack_height(self):
        return self._rack_height

    @rack_height.setter
    def rack_height(self, new_rack_height):
        self._rack_height = new_rack_height

    @property
    def cluster(self):
        return self._cluster

    @cluster.setter
    def cluster(self, new_cluster):
        self._cluster = new_cluster
    
