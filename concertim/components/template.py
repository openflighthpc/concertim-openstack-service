from concertim.concertim import ConcertimData

class ConcertimTemplate:
    #__slots__ = ('__flavor_id', '__name', '__ram', '__disk', '__vcpus', '__template_id', '__device_size')
    def __init__(self, template_id, flavor_id, flavor_name, ram, disk, vcpus, device_size=''):
        
        self.__template_id = template_id
        self.__flavor_id = flavor_id
        self.__name = flavor_name
        self.__ram = ram
        self.__disk = disk
        self.__vcpus = vcpus
        self.__device_size = device_size

    def __repr__(self):
        lines = ['\n' + self.__class__.__name__ + ':']
        for key, val in vars(self).items():
            lines += '{}: {}'.format(key, val.__repr__()).split('\n')
        return '{' + '\n '.join(lines) + '}'
    
    @property
    def flavor_id(self):
        return self.__flavor_id

    @property
    def name(self):
        return self.__name

    @name.setter
    def name(self, new_template_name):
        self.__name = new_template_name

    @property
    def ram(self):
        return self.__ram

    @property
    def disk(self):
        return self.__disk

    @property
    def vcpus(self):
        return self.__vcpus

    @property
    def template_id(self):
        return self.__template_id

    @property
    def device_size(self):
        return self.__device_size

    @device_size.setter
    def device_size(self, new_device_size):
        self.__device_size = new_device_size

    @property
    def template_id(self):
        return self.__template_id

    @template_id.setter
    def template_id(self, new_template_id):
        self.__template_id = new_template_id
