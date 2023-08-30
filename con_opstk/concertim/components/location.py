class Location(object):
    def __init__(self, start_u, end_u, facing):
        self.start_u = start_u
        self.end_u = end_u
        self.facing = facing

    def __repr__(self):
        return f"<Location:{{start_u:{repr(self.start_u)}, end_u:{repr(self.end_u)}, facing:{repr(self.facing)}}}>"