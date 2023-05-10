class ConcertimDevice:
    __slots__ = ('_template','_instance_id','_location','_device_description','_device_name','_device_id')
    def __init__(self, device_id, device_name, device_description, instance_id, template, location={}):
        self._device_id = device_id
        self._device_name = device_name
        self._device_description = device_description
        self._location = location
        self._instance_id = instance_id
        self._template = template

    @property
    def device_id(self):
        return self._device_id

    @property
    def device_name(self):
        return self._device_name

    @device_name.setter
    def device_name(self, new_device_name):
        self._device_name = new_device_name

    @property
    def device_description(self):
        return self._device_description

    @device_description.setter
    def device_description(self, new_device_description):
        self._device_description = new_device_description

    @property
    def location(self):
        return self._location

    @location.setter
    def location(self, new_location):
        self._location = new_location

    @property
    def instance_id(self):
        return self._instance_id

    @property
    def template(self):
        return self._template

    @template.setter
    def template(self, new_template):
        self._template = new_template