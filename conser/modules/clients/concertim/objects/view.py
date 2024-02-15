import conser.exceptions as EXCP
class ConcertimView(object):
    def __init__(self):
        self.racks = {}
        self.devices = {}
        self.users = {}
        self.templates = {}

    def __repr__(self):
        return f"<ConcertimView: \
                    {{racks:{repr(self.racks)}, \
                    devices:{repr(self.devices)}, \
                    users:{repr(self.users)}, \
                    templates:{repr(self.templates)}}}>"

    def add_device(self, device):
        self.devices[device.id] = device

    def remove_device(self, device):
        del self.devices[device.id]

    def add_rack(self, rack):
        self.racks[rack.id] = rack

    def remove_rack(self, rack):
        del self.racks[rack.id]

    def add_user(self, user):
        self.users[user.id] = user

    def remove_user(self, user):
        del self.users[user.id]

    def add_template(self, template):
        self.templates[template.id] = template

    def remove_template(self, template):
        del self.templates[template.id]

    def is_empty(self):
        if self.users or self.templates or self.racks or self.devices:
            return False
        return True

    def search(self, object_type, id_field):
        """
        Function to search the view for an object that matches the given ID field.
        Returns a list of matching objects for the given object type

        REQUIRED:
            object_type: type of object to search for (rack, device, template, etc)
            id_field: the known ID field to search for
        """
        dict_to_search = None
        if object_type == 'racks' or object_type == 'rack':
            dict_to_search = self.racks
        elif object_type == 'devices' or object_type == 'device':
            dict_to_search = self.devices
        elif object_type == 'users' or object_type == 'user':
            dict_to_search = self.users
        elif object_type == 'templates' or object_type == 'template':
            dict_to_search = self.templates
        else:
            raise EXCP.InvalidSearchAttempt(object_type)

        matches = []
        for id_tup in dict_to_search:
            if id_field in id_tup:
                matches.append(dict_to_search[id_tup])

        return matches
