import conser.exceptions as EXCP
class ConcertimView(object):
    def __init__(self):
        self.racks = {}
        self.devices = {}
        self.users = {}
        self.templates = {}
        self.teams = {}

    def __repr__(self):
        return f"<ConcertimView: \
                    {{racks:{repr(self.racks)}, \
                    devices:{repr(self.devices)}, \
                    users:{repr(self.users)}, \
                    teams:{repr(self.teams)}, \
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

    def add_team(self, team):
        self.teams[team.id] = team

    def remove_team(self, team):
        del self.teams[team.id]

    def add_template(self, template):
        self.templates[template.id] = template

    def remove_template(self, template):
        del self.templates[template.id]

    def is_empty(self):
        if self.users or self.templates or self.racks or self.devices:
            return False
        return True

    # VIEW HELPERS
    def search(self, object_type, id_value, id_origin):
        """
        Function to search the view for an object that matches the given ID field.
        Returns the most completed matching object for the given object type

        REQUIRED:
            object_type: type of object to search for (rack, device, template, etc)
            id_value: the known ID field to search for
            id_origin: what the known ID is from, valid fields are [concertim, cloud, billing]
        """
        dict_to_search = None
        index_to_search = None
        return_item = None

        if object_type == 'racks' or object_type == 'rack':
            dict_to_search = self.racks
        elif object_type == 'devices' or object_type == 'device':
            dict_to_search = self.devices
        elif object_type == 'users' or object_type == 'user':
            dict_to_search = self.users
        elif object_type == 'templates' or object_type == 'template':
            dict_to_search = self.templates
        elif object_type == 'teams' or object_type == 'team':
            dict_to_search = self.teams
        else:
            raise EXCP.InvalidSearchAttempt(object_type)

        if id_origin == 'concertim':
            index_to_search = 0
        if id_origin == 'cloud':
            index_to_search = 1
        if id_origin == 'billing':
            if object_type not in ['rack', 'racks', 'user', 'users', 'team'. 'teams']:
                raise EXCP.InvalidSearchAttempt(f"{object_type}.{id_origin}")
            index_to_search = 2
        else:
            raise EXCP.InvalidSearchAttempt(id_origin)

        matches = [v for k,v in dict_to_search.items() if k[index_to_search] == id_value]
        if len(matches) == 1:
            return_item = matches[0]
        elif len(matches) > 1:
            for obj in matches:
                if not return_item:
                    return_item = obj
                if all(return_item.id):
                    break
                if all(obj.id):
                    return_item = obj
                    break
                return_empty_id_count = 0
                obj_empty_id_count = 0
                for i in range(len(return_item.id)):
                    if not return_item.id[i]:
                        return_empty_id_count += 1
                    if not obj.id[i]:
                        obj_empty_id_count += 1
                if obj_empty_id_count < return_empty_id_count:
                    return_item = obj
        return return_item

    def merge(self, other_view):
        """
        As of v1.2.0 merging consists of using all data from the other view, overwriting existing data
        """
        dicts_to_merge = ['templates', 'devices', 'racks', 'users']
        for dict_name in dicts_to_merge:
            getattr(self, dict_name) = getattr(other_view, dict_name)

    def delete_stale_items(self):
        """
        Function that loops over the current dicts and deletes any keys that have a more recent, matching key
        (if key is (1,None,None) and there exists (1,2,3) then delete the key)
        """
        dicts_to_merge = ['templates', 'devices', 'racks', 'users']
        # Loop over all dicts
        for dict_name in dicts_to_merge:
            # Get all partially filled keys and all completed keys
            partials = [k for k in getattr(self, dict_name) if not all(k)]
            completes = [k for k in getattr(self, dict_name) if all(k)]
            # Loop over the list of completed keys and partial keys - check if there are any matching keys
            # If a partial matching key exists, delete it from the dict
            for partial_id_tup in partials:
                for complete_id_tup in completes:
                    if self._check_partial_match(partial_id_tup, complete_id_tup):
                        del getattr(self, dict_name)[partial_id_tup]

    def _check_partial_match(self, partial_tup, complete_tup):
        matching = False
        for i in range(len(partial_tup)):
            if not partial_tup[i]:
                continue
            elif partial_tup[i] != complete_tup[i]:
                break
            elif partial_tup[i] == complete_tup[i]:
                matching = True
                break
        return matching



