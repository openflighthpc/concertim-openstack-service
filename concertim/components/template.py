class ConcertimTemplate:
    __slots__ = ('__template_id','__template_name','__template_description','__device_size','__flavor_id')
    def __init__(self, template_id, template_name, template_description, device_size, flavor_id):
        self.__template_id = template_id
        self.__template_name = template_name
        self.__template_description = template_description
        self.__device_size = device_size
        self.__flavor_id = flavor_id

    @property
    def template_id(self):
        return self.__template_id

    @property
    def template_name(self):
        return self.__template_name

    @template_name.setter
    def template_name(self, new_template_name):
        self.__template_name = new_template_name

    @property
    def template_description(self):
        return self.__template_description

    @template_description.setter
    def template_description(self, new_template_description):
        self.__template_description = new_template_description

    @property
    def device_size(self):
        return self.__device_size

    @device_size.setter
    def device_size(self, new_device_size):
        self.__device_size = new_device_size

    @property
    def flavor_id(self):
        return self.__flavor_id

