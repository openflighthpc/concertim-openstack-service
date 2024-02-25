# Local Imports
from conser.utils.service_logger import create_logger
from conser.modules.clients.cloud.openstack.components.base import OpstkBaseComponent
# Py Packages
import sys
import time
# Openstack Packages
import keystoneclient.v3.client as ks_client

class KeystoneComponent(OpstkBaseComponent):
    def __init__(self, sess, log_file, log_level):
        super().__init__(sess, log_file, log_level)
        self.__LOGGER = create_logger(__name__, self._LOG_FILE, self._LOG_LEVEL)
        self.__LOGGER.info("CREATING KEYSTONE COMPONENT")
        self.client = self.get_connection_obj(self._SESSION)

    def get_connection_obj(self, sess):
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

    def get_projects(self, user_obj=None):
        try:
            if user_obj is not None:
                self.__LOGGER.debug(f"Getting projects for user : {user_obj.name}")
                projects = self.client.projects.list(user=user_obj)
                self.__LOGGER.debug(f"PROJECTS : {projects}")
                return projects
            self.__LOGGER.debug(f"Getting all projects")
            projects = self.client.projects.list()
            self.__LOGGER.debug(f"PROJECTS : {projects}")
            return projects
        except Exception as e:
            self.__LOGGER.error(f"An unexpected error : {type(e).__name__} - {e}")
            raise e

    def get_project(self, ID):
        try:
            self.__LOGGER.debug(f"Getting Openstack Project : {ID}")
            project = self.client.projects.get(ID)
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

    def get_user(self, ID):
        try:
            self.__LOGGER.debug(f"Getting Openstack User : {ID}")
            user = self.client.users.get(ID)
            self.__LOGGER.debug(f"User {user} found.")
            return user
        except Exception as e:
            self.__LOGGER.error(f"An unexpected error : {type(e).__name__} - {e}")
            raise e

    def get_user_assignments(self, user_id):
        try:
            self.__LOGGER.debug(f"Getting Openstack User's role assignments : {ID}")
            ra = self.client.role_assignments.list(user=user_id)
            self.__LOGGER.debug(f"Roles for {user_id} found: {ra}")
            return ra
        except Exception as e:
            self.__LOGGER.error(f"An unexpected error : {type(e).__name__} - {e}")
            raise e

    def get_project_assignments(self, project_id):
        try:
            self.__LOGGER.debug(f"Getting Openstack Project's role assignments : {ID}")
            ra = self.client.role_assignments.list(project=project_id)
            self.__LOGGER.debug(f"Roles for {project_id} found: {ra}")
            return ra
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

    def get_role_by_id(self, ID):
        try:
            self.__LOGGER.debug(f"Getting Openstack Role : {ID}")
            role = self.client.roles.get(ID)
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

    def delete_user(self, user_id):
        try:
            self.__LOGGER.debug(f"Deleting User '{user_id}'")
            delete_attempt = self.client.users.delete(user=user_id)
            return True
        except Exception as e:
            self.__LOGGER.error(f"An unexpected error : {type(e).__name__} - {e}")
            raise e
    
    def update_user(self, user_id, **kwargs):
        try:
            fields = {k:v for k, v in kwargs.items() if v is not None}
            self.__LOGGER.debug(f"Updating User '{user_id}' fields {fields}")
            update_attempt = self.client.users.update(user=user_id, **fields)
            return True
        except Exception as e:
            self.__LOGGER.error(f"An unexpected error : {type(e).__name__} - {e}")
            raise e

    def update_project(self, project_id, **kwargs):
        try:
            fields = {k:v for k, v in kwargs.items() if v is not None}
            self.__LOGGER.debug(f"Updating Project '{project_id}' fields {fields}")
            update_attempt = self.client.users.update(project=project_id, **fields)
            return True
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

    def delete_project(self, project_id):
        try:
            self.__LOGGER.debug(f"Deleting '{project_id}'")
            delete_attempt = self.client.projects.delete(project=project_id)
            return True
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

    def disconnect(self):
        self.__LOGGER.debug("Disconnecting Keystone Component Connection")
        self.client = None
        super().disconnect()