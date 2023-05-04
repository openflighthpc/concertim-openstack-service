class ConcertimTemplate:
    def __init__(self, template_id, template_name, template_description, device_size, flavor_id):
        self._template_id = template_id
        self._template_name = template_name
        self._template_description = template_description
        self._device_size = device_size
        self._flavor_id = flavor_id

    @property
    def template_id(self):
        return self._template_id

    @property
    def template_name(self):
        return self._template_name

    @template_name.setter
    def template_name(self, new_template_name):
        self._template_name = new_template_name

    @property
    def template_description(self):
        return self._template_description

    @template_description.setter
    def template_description(self, new_template_description):
        self._template_description = new_template_description

    @property
    def device_size(self):
        return self._device_size

    @device_size.setter
    def device_size(self, new_device_size):
        self._device_size = new_device_size

    @property
    def flavor_id(self):
        return self._flavor_id

