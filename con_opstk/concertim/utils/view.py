class ConcertimOpenstackView(object):
    def __init__(self):
        self.racks = {}
        self.devices = {}
        self.users = {}
        self.templates = {}

    def __repr__(self):
        return f"<ConcertimOpenstackView:{{racks:{repr(self.racks)}, devices:{repr(self.devices)}, users:{repr(self.users)}, templates:{repr(self.templates)}}}>"

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

    