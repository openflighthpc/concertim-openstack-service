# Local Imports
from utils.service_logger import create_logger

# Py Packages
import time

# Openstack Packages
import keystoneclient.v3.client as ks_client

class KeystoneHandler:
    def __init__(self, sess, log_level):
        self.__LOGGER = create_logger(__name__, '/var/log/concertim-openstack-service-opt.log', log_level)
        self.client = self.__get_client(sess)
        self._concertim_user = self.get_user('concertim')

    def __get_client(self, sess):
        start_time = time.time()
        while time.time() - start_time < 30:  # Try for up to 30 seconds
            try:
                client = ks_client.Client(session=sess)
                self.__LOGGER.debug("SUCCESS - Keystone client connected")
                return client # Exit if client creation is successful
            except Exception as e:
                self.__LOGGER.error(f"Failed to create Keystone client: {e}. Retrying...")
                time.sleep(1)  # Wait for a second before retrying

        raise Exception("Failed to create Keystone client after multiple attempts.")
    
    def close(self):
        self.__LOGGER.debug("Closing Keystone Client Connection")
        self.client = None

    def get_projects(self, user=None):
        if user is not None:
            self.__LOGGER.debug(f"Getting projects for user : {user.name}")
            projects = self.client.projects.list(user=user)
            self.__LOGGER.debug(f"PROJECTS : {projects}")
            return projects
        self.__LOGGER.debug(f"Getting all projects")
        projects = self.client.projects.list()
        self.__LOGGER.debug(f"PROJECTS : {projects}")
        return projects

    def get_users(self):
        self.__LOGGER.debug(f"Getting all users")
        users = self.client.users.list()
        self.__LOGGER.debug(f"USERS : {users}")
        return users

    def get_user(self, name):
        self.__LOGGER.debug(f"Getting Openstack User : {name}")
        user = self.client.users.list(name=name)[0]
        self.__LOGGER.debug(f"USER : {user}")
        return user