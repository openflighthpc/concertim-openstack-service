class ConcertimUser:
    __slots__ = ('_user_id', '_project_id', '_display_name', '_login_name', '_owned_racks')
    def __init__(self, user_id, project_id, display_name, login_name, owned_racks=[]):
        self._user_id = user_id
        self._project_id = project_id
        self._display_name = display_name
        self._login_name = login_name
        self._owned_racks = owned_racks

    @property
    def user_id(self):
        return self._user_id

    @property
    def project_id(self):
        return self._project_id

    @project_id.setter
    def project_id(self, new_project_id):
        self._project_id = new_project_id

    @property
    def display_name(self):
        return self._display_name

    @property
    def login_name(self):
        return self._login_name

    @property
    def owned_racks(self):
        return self._owned_racks

    @owned_racks.setter
    def owned_racks(self, new_owned_racks):
        self._owned_racks = new_owned_racks
