# Local Imports
from utils.service_logger import create_logger
from openstack.client_handlers.client_base import ClientHandler
# Py Packages
import time
# Openstack Packages
import keystoneclient.v3.client as ks_client
import keystoneclient.exceptions

class KeystoneHandler(ClientHandler):
    def __init__(self, sess, log_file, log_level):
        super().__init__(sess, log_file, log_level)
        self.__LOGGER = create_logger(__name__, self.__LOG_FILE, self.__LOG_LEVEL)
        self.client = self.__get_client(self.__SESSION)

    def __get_client(self, sess):
        start_time = time.time()
        error = None
        while time.time() - start_time < 30:  # Try for up to 30 seconds
            try:
                client = ks_client.Client(session=sess)
                self.__LOGGER.debug("SUCCESS - Keystone client connected")
                return client # Exit if client creation is successful
            except Exception as e:
                self.__LOGGER.error(f"Failed to create Keystone client: {type(e).__name__} - {e} - Retrying...")
                error = e
                time.sleep(1)  # Wait for a second before retrying
        self.__LOGGER.error(f"Failed to create Keystone client after multiple attempts : {type(error).__name__} - {error}")
        raise error

    def get_projects(self, user=None):
        try:
            if user is not None:
                self.__LOGGER.debug(f"Getting projects for user : {user.name}")
                projects = self.client.projects.list(user=user)
                self.__LOGGER.debug(f"PROJECTS : {projects}")
                return projects
            self.__LOGGER.debug(f"Getting all projects")
            projects = self.client.projects.list()
            self.__LOGGER.debug(f"PROJECTS : {projects}")
            return projects
        except Exception as e:
            self.__LOGGER.error(f"An unexpected error : {type(e).__name__} - {e}")
            raise e
    
    def get_project(self, name):
        try:
            self.__LOGGER.debug(f"Getting Openstack Project : {name}")
            proj_list = self.client.projects.list(name=name)
            if not proj_list:
                self.__LOGGER.error(f"Project {name} not found, returning None")
                return None
            elif len(proj_list) > 1:
                self.__LOGGER.debug(f"Multiple Projects matching name {name} found, returning list of matching Projects")
                return proj_list
            else:
                project = proj_list[0]
                self.__LOGGER.debug(f"Project {project} found.")
                return project
        except Exception as e:
            self.__LOGGER.error(f"An unexpected error : {type(e).__name__} - {e}")
            raise e

    def get_domain(self, name):
        try:
            self.__LOGGER.debug(f"Getting Openstack Domain : {name}")
            domain_list = self.client.domains.list(name=name)
            if not domain_list:
                self.__LOGGER.error(f"Domain {name} not found, returning None")
                return None
            elif len(domain_list) > 1:
                self.__LOGGER.debug(f"Multiple Domains matching name {name} found, returning list of matching Domains")
                return domain_list
            else:
                domain = domain_list[0]
                self.__LOGGER.debug(f"Domain {domain} found.")
                return domain
        except Exception as e:
            self.__LOGGER.error(f"An unexpected error : {type(e).__name__} - {e}")
            raise e

    def get_users(self):
        try:
            self.__LOGGER.debug(f"Getting all users")
            users = self.client.users.list()
            self.__LOGGER.debug(f"USERS : {users}")
            return users
        except Exception as e:
            self.__LOGGER.error(f"An unexpected error : {type(e).__name__} - {e}")
            raise e

    def get_user(self, name):
        try:
            self.__LOGGER.debug(f"Getting Openstack User : {name}")
            users_list = self.client.users.list(name=name)
            if not users_list:
                self.__LOGGER.error(f"User {name} not found, returning None")
                return None
            elif len(users_list) > 1:
                self.__LOGGER.debug(f"Multiple User matching name {name} found, returning list of matching Users")
                return users_list
            else:
                user = users_list[0]
                self.__LOGGER.debug(f"User {user} found.")
                return user
        except Exception as e:
            self.__LOGGER.error(f"An unexpected error : {type(e).__name__} - {e}")
            raise e

    def get_role(self, name):
        try:
            self.__LOGGER.debug(f"Getting Openstack Role : {name}")
            roles_list = self.client.roles.list(name=name)
            if not roles_list:
                self.__LOGGER.error(f"Role {name} not found, returning None")
                return None
            elif len(roles_list) > 1:
                self.__LOGGER.debug(f"Multiple Roles matching name {name} found, returning list of matching Roles")
                return roles_list
            else:
                role = roles_list[0]
                self.__LOGGER.debug(f"Role {role} found.")
                return role
        except Exception as e:
            self.__LOGGER.error(f"An unexpected error : {type(e).__name__} - {e}")
            raise e

    def create_user(self, username, password, domain, email='', desc='', project=None):
        try:
            self.__LOGGER.debug(f"Creating new User '{username}' in domain '{domain}'")
            user = None
            if project:
                self.__LOGGER.debug(f"Adding {project.name} as default project for User: '{username}'")
                user = self.client.users.create(name=username,password=password,email=email,description=desc,domain=domain,default_project=project)
            else:
                user = self.client.users.create(name=username,password=password,email=email,description=desc,domain=domain)
            self.__LOGGER.debug(f"NEW USER: {user}")
            return user
        except Exception as e:
            self.__LOGGER.error(f"An unexpected error : {type(e).__name__} - {e}")
            raise e
    
    def create_project(self, name, domain, desc=''):
        try:
            self.__LOGGER.debug(f"Creating new project '{name}' in domain '{domain}'")
            project = self.client.projects.create(name=name,domain=domain,description=desc)
            self.__LOGGER.debug(f"NEW PROJECT: {project}")
            return project
        except Exception as e:
            self.__LOGGER.error(f"An unexpected error : {type(e).__name__} - {e}")
            raise e
    
    def add_user_to_project(self, user, project, role):
        try:
            self.__LOGGER.debug(f"Adding User:{user} to Project:{project} with Role:{role}")
            new_role = self.client.roles.grant(role=role, user=user, project=project)
            return new_role
        except Exception as e:
            self.__LOGGER.error(f"An unexpected error : {type(e).__name__} - {e}")
            raise e

    def close(self):
        self.__LOGGER.debug("Closing Keystone Client Connection")
        self.client = None
        super().close()