# Local imports
from data_handler.user_handler.user_handler import UserHandler
from openstack.exceptions import APIServerDefError
# Py Packages
from flask import Flask, request, jsonify, make_response
from flask import Response
import logging


formatter = logging.Formatter('%(asctime)s - [%(levelname)s] (%(module)s) - %(message)s')
log_file = '/var/log/concertim-openstack-service/api_server.log'
fh = logging.FileHandler(log_file)
fh.setFormatter(formatter)

# Flask app
app = Flask('user_handler')
app.logger.addHandler(fh)
app.logger.setLevel(logging.INFO)

@app.route('/create_user_project', methods=['POST'])
def create_user_project():
    config = {'log_level': 'debug', 'openstack': {}}
    try:
        req_data = request.get_json()
        if 'cloud_env' not in req_data:
            raise APIServerDefError("No Authentication data recieved.", 400)
        if 'username' not in req_data or 'password' not in req_data:
            raise APIServerDefError("Invalid user data. 'username' and 'password' are required.", 400)

        config['openstack'] = req_data['cloud_env']
        username = req_data['username']
        password = req_data['password']
        email = req_data['email'] if 'email' in req_data else ''
        
        user_handler = UserHandler(config, log_file)
        app.logger.info(f"Successfully created UserHandler")

        user, project = user_handler.create_user_project(username, password, email)
        app.logger.info(f"Successfully created new User and Project in Openstack")

        resp = {"username": username, "user_id": user.id, "project_id": project.id}
        return make_response(resp,201)
    except APIServerDefError as e:
        response = {"error": type(e).__name__, "message": str(e)}
        app.logger.error(response)
        return jsonify(response), 400
    except OpStkAuthenticationError as e:
        response = {"error": type(e).__name__, "message": str(e)}
        app.logger.error(response)
        return jsonify(response), 400
    except Exception as e:
        response = {"error": f"An unexpected error occurred: {type(e).__name__}", "message": str(e)}
        stat_code = 500
        app.logger.error(response)
        if 'http_status' in dir(e):
            stat_code = e.http_status
        return jsonify(response), stat_code
    finally:
        app.logger.debug("Disconnecting Handler")
        user_handler.disconnect()
        user_handler = None

@app.route('/')
def running():
    app.logger.info('Running')
    return 'Running'

def run_app():
    app.run(host='0.0.0.0', port=42356)