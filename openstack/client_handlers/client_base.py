# Local Imports
from utils.service_logger import create_logger
from openstack.exceptions import UnsupportedObject

class ClientHandler(object):
    def __init__(self, sess, log_file, log_level):
        self._LOG_FILE = log_file
        self._LOG_LEVEL = log_level
        self.__LOGGER = create_logger(__name__, self._LOG_FILE, self._LOG_LEVEL)
        self._SESSION = sess
        self.client = None

    # Delete object(s) from Openstack
    # Returns True on success and False on fail
    # Accepts Openstack Client-based Object references (not names or ids)
    def delete(self, *args):
        self.__LOGGER.debug(f"Attempting to delete objects from Openstack")
        failed = []
        unsupported = []
        client_tree = getattr(self.client, '__module__', None)
        client_root = client_tree.split('.')[0] if client_tree else None
        for item in args:
            item_tree = getattr(item, '__module__', None)
            item_root = item_tree.split('.')[0] if item_tree else None
            if not ((client_root and item_root) and (client_root == item_root)):
                self.__LOGGER.error(f"Attempted to delete a non-supported object - '{type(item)}:{item}' - Exception will be raised")
                unsupported.append(f"{type(item)}:{item}")
                continue
            ref = item.name if hasattr(item, 'name') else item.id
            try:
                self.__LOGGER.debug(f"Attempting to delete '{ref}'")
                module = item.__module__.split('.')[-1]
                delete_method = getattr(getattr(self.client, module), 'delete')
                self.__LOGGER.debug(f"Using {delete_method}")
                delete_method(item.id)
                self.__LOGGER.debug(f"Deleted '{ref}' successfully")
            except Exception as e:
                self.__LOGGER.warning(f"Could not delete '{item}' : {type(e).__name__} - {e}")
                failed.append(f"{item.__class__.__name__}:{ref}")
                continue
        if unsupported:
            raise UnsupportedObject(f"UNSUPPORTED : {unsupported}")
        if failed:
            self.__LOGGER.error(f"Failed to delete objects during most recent attempt : {failed} - check WARNINGs for more details")
            return False
        return True


    def close(self):
        self._SESSION = None
