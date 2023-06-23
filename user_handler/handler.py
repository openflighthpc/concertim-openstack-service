# Local Imports
from utils.service_logger import create_logger
from openstack.opstk_auth import OpenStackAuth
from openstack.keystone import KeystoneHandler
# Py packages
import yaml

# Custom exception
class UserProjectException(Exception):
    pass

def load_config(config_file):
    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)
    return config

__log_file = '/var/log/concertim-openstack-service/user-handler.log'
__config_obj = load_config('/etc/concertim-openstack-service/config.yaml')
__LOGGER = create_logger(__name__, __log_file, __config_obj['log_level'])

def handle_new_user_project(user_data):
    if 'cloud_env' not in user_data:
        raise Exception("No Authentication data recieved.")
    if 'username' not in user_data or 'password' not in user_data:
        raise UserProjectException("Invalid user data. 'username' and 'password' are required.")
    
    username = user_data['username']
    password = user_data['password']
    project_name = f"{username}_project"

    # Create Keystone client (this authenticates the call as well)
    sess = OpenStackAuth(user_data['cloud_env']).get_session()
    keystone = KeystoneHandler(sess, __log_file, __config_obj['log_level'])

    # Create a new project
    project = keystone.create_project(project_name, __config_obj['openstack']['project_domain_name'])

    # Create a new user in project with admin rights for that project
    user = keystone.create_user(username, password, __config_obj['openstack']['user_domain_name'], project=project)
    keystone.add_user_to_project(user, project, 'admin')

    # Add 'concertim' user to project as member
    concertim_user = keystone._concertim_user
    keystone.add_user_to_project(concertim_user, project)

    # Return user_id and project_id with 201 status code for success
    return {"user_id": user.id, "project_id": project.id}, 201



