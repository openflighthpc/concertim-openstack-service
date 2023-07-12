# Local imports
from openstack.opstk_auth import OpenStackAuth, OpStkAuthenticationError
# Py Packages
from flask import Flask, request, jsonify, make_response
from flask import Response
import logging
import os
import yaml
# Openstack Packages
import keystoneclient.v3.client as ks_client

class UserHandlerException(Exception):
    pass

# Load the configuration
config=None
with open('/etc/concertim-openstack-service/config.yaml', 'r') as f:
    config = yaml.safe_load(f)

# Logger config
level = logging.getLevelName(config['log_level'])
formatter = logging.Formatter('%(asctime)s - [%(levelname)s] (%(module)s) - %(message)s')
fh = logging.FileHandler('/var/log/user_handler.log')
fh.setFormatter(formatter)

# Flask app
app = Flask('user_handler')
app.logger.addHandler(fh)
app.logger.setLevel(level)

@app.route('/create_user_project', methods=['POST'])
def create_user_project():
    try:
        scrub = []
        user_data = request.get_json()
        if 'cloud_env' not in user_data:
            raise UserHandlerException("No Authentication data recieved.")
        if 'username' not in user_data or 'password' not in user_data:
            raise UserHandlerException("Invalid user data. 'username' and 'password' are required.")

        username = f"concertim_{user_data['username']}"
        password = user_data['password']
        project_name = f"{username}_project"
        proj_domain = 'default'
        user_domain = 'default'
        if 'project_domain_name' in user_data['cloud_env']:
            domain = user_data['cloud_env']['project_domain_name']
        if 'user_domain_name' in user_data['cloud_env']:
            domain = user_data['cloud_env']['user_domain_name']

        # Connect Keystone
        app.logger.debug(f"Attempting to Connect to Keystone")
        sess = OpenStackAuth(user_data['cloud_env']).get_session()
        keystone = ks_client.Client(session=sess)
        app.logger.debug(f"Connected to Keystone Successfully")

        # Create new project
        app.logger.debug(f"Attempting to create new project {project_name}")
        project = keystone.projects.create(project_name, proj_domain)
        scrub.append(project)
        app.logger.debug(f"Created project {project}")

        # Create new user
        app.logger.debug(f"Attempting to create new user {username}")
        user = keystone.users.create(name=username,password=password,default_project=project,domain=user_domain)
        scrub.append(user)
        app.logger.debug(f"Created user {user}")

        # Add new user, concertim user, and admin user to project
        app.logger.debug(f"Attempting to add additional roles and users for Concertim")
        #### Get info from openstack
        mem_role = keystone.roles.list(name='member')[0]
        watcher_role = keystone.roles.list(name='watcher')[0]
        admin_role = keystone.roles.list(name='admin')[0]
        concertim_user = keystone.users.list(name='concertim')[0]
        admin_user = keystone.users.list(name='admin')[0]
        #### Add users/roles
        keystone.roles.grant(role=admin_role, user=user, project=project)
        keystone.roles.grant(role=watcher_role, user=concertim_user, project=project)
        keystone.roles.grant(role=mem_role, user=concertim_user, project=project)
        keystone.roles.grant(role=admin_role, user=admin_user, project=project)
        app.logger.debug(f"Successfully added additional roles and users to {project_name}")

        body = {"username": user_data['username'], "user_id": user.id, "project_id": project.id}
        return make_response(body,201)

    except UserHandlerException as e:
        response = {"error": type(e).__name__, "message": str(e)}
        app.logger.error(response)
        _scrub(scrub, keystone)
        return jsonify(response), 400
    except OpStkAuthenticationError as e:
        response = {"error": type(e).__name__, "message": str(e)}
        app.logger.error(response)
        _scrub(scrub, keystone)
        return jsonify(response), 450
    except IndexError as e:
        response = {"error": "MissingIdentityObject", "message": "one of the following keystone objects is missing in default domain: [user: admin, concertim], [role: member, admin, watcher]"}
        app.logger.error(response)
        _scrub(scrub, keystone)
        return jsonify(response), 451
    except Exception as e:
        response = {"error": "An unexpected error occurred: {}".format(type(e).__name__), "message": str(e)}
        stat_code = 500
        app.logger.error(response)
        if 'http_status' in dir(e):
            stat_code = e.http_status
        _scrub(scrub, keystone)
        return jsonify(response), stat_code

@app.route('/')
def running():
    app.logger.info('Running')
    return 'Running'

def run_app():
    app.run(host='0.0.0.0', port=42356)

def _scrub(orphans, client):
    app.logger.debug(f"Scrubbing orphaned objects")
    for orphan in orphans:
        try:
            app.logger.debug(f"Attempting to delete {orphan.name}")
            module = orphan.__module__.split('.')[-1]
            delete_method = getattr(getattr(client, module), 'delete')
            app.logger.debug(f"Using {delete_method}")
            delete_method(orphan.id)
            app.logger.debug(f"Deleted successfully")
        except Exception as e:
            app.logger.debug(f"Could not delete {orphan}: {e}")
            continue
