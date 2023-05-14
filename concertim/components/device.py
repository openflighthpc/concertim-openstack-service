class ConcertimDevice:
    __slots__ = ('__template','__instance_id','__location','__device_description','__device_name','__device_id')
    def __init__(self, device_id, device_name, device_description, instance_id, template, location={}):
        self.__device_id = device_id
        self.__device_name = device_name
        self.__device_description = device_description
        self.__location = location
        self.__instance_id = instance_id
        self.__template = template

    @property
    def device_id(self):
        return self.__device_id

    @property
    def device_name(self):
        return self.__device_name

    @device_name.setter
    def device_name(self, new_device_name):
        self.__device_name = new_device_name

    @property
    def device_description(self):
        return self.__device_description

    @device_description.setter
    def device_description(self, new_device_description):
        self.__device_description = new_device_description

    @property
    def location(self):
        return self.__location

    @location.setter
    def location(self, new_location):
        self.__location = new_location

    @property
    def instance_id(self):
        return self.__instance_id

    @property
    def template(self):
        return self.__template

    @template.setter
    def template(self, new_template):
        self.__template = new_template