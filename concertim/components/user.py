
class ConcertimUser:
    __slots__ = ('__user_id', '__project_id', '__display_name', '__login_name', '__owned_racks')
    def __init__(self, user_id, project_id, display_name, login_name, owned_racks=[]):
        self.__user_id = user_id
        self.__project_id = project_id
        self.__display_name = display_name
        self.__login_name = login_name
        self.__owned_racks = owned_racks

    @property
    def user_id(self):
        return self.__user_id

    @property
    def project_id(self):
        return self.__project_id

    @project_id.setter
    def project_id(self, new_project_id):
        self.__project_id = new_project_id

    @property
    def display_name(self):
        return self.__display_name

    @property
    def login_name(self):
        return self.__login_name

    @property
    def owned_racks(self):
        return self.__owned_racks

    @owned_racks.setter
    def owned_racks(self, new_owned_racks):
        self.__owned_racks = new_owned_racks
