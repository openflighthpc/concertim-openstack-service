# Local Imports
from utils.service_logger import create_logger
from user_handler.handler import handle_new_user_project, UserProjectException
# Py packages
from flask import Flask, request, jsonify
from flask import Response
import yaml

def load_config(config_file):
    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)
    return config

__config_obj = load_config('/etc/concertim-openstack-service/config.yaml')
__LOGGER = create_logger(__name__, '/var/log/concertim-openstack-service/user-handler.log', __config_obj['log_level'])
app = Flask(__name__)

@app.route('/create_user_project', methods=['POST'])
def new_user_project():
    try:
        user_data = request.get_json()
        result, status = handle_new_user_project(user_data)
        return jsonify(result), status
    except UserProjectException as e:
        response = {"error": str(e)}
        return jsonify(response), 400
    except Exception as e:
        response = {"error": "An unexpected error occurred: {}".format(str(e))}
        return jsonify(response), 500

def run_app():
    app.run(host='0.0.0.0', port=42356)

