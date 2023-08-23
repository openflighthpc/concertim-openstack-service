# Local imports
from con_opstk.data_handler.api_handler.api_handler import APIHandler
from con_opstk.openstack.exceptions import APIServerDefError, OpStkAuthenticationError
import con_opstk.app_definitions as app_paths
from con_opstk.utils.service_logger import SensitiveFormatter
# Py Packages
from flask import Flask, request, jsonify, make_response
from flask import Response
import logging
import keystoneauth1.exceptions.http
import novaclient.exceptions


formatter = SensitiveFormatter('%(asctime)s - [%(levelname)s] (%(module)s:%(funcName)-40s) - %(message)s')
log_file = app_paths.LOG_DIR + 'api_server.log'
fh = logging.FileHandler(log_file)
fh.setFormatter(formatter)

# Flask app
app = Flask('api')
app.logger.addHandler(fh)
app.logger.setLevel(logging.DEBUG)

@app.route('/create_user_project', methods=['POST'])
def create_user_project():
    config = {'log_level': 'debug', 'openstack': {}}
    app.logger.info(f"\nStarting - Creating new 'CM_' project and user in Openstack")
    try:
        req_data = request.get_json()
        app.logger.debug(req_data)
        if 'cloud_env' not in req_data:
            raise APIServerDefError("No Authentication data recieved.", 400)
        if 'username' not in req_data or 'password' not in req_data:
            raise APIServerDefError("Invalid user data. 'username' and 'password' are required.", 400)

        billing = False
        config['openstack'] = req_data['cloud_env']
        username = req_data['username']
        password = req_data['password']
        email = req_data['email'] if 'email' in req_data else ''
        if 'billing_enabled' in req_data['cloud_env'] and eval(req_data['cloud_env']['billing_enabled']):
            billing = True
        
        api_handler = APIHandler(config, log_file, billing_enabled=billing)
        app.logger.debug(f"Successfully created APIHandler")

        user, project = api_handler.create_user_project(username, password, email)
        app.logger.debug(f"Successfully created new User and Project in Openstack")

        resp = {"username": username, "user_id": user.id, "project_id": project.id}
        return make_response(resp,201)
    except APIServerDefError as e:
        response = {"error": type(e).__name__, "message": str(e)}
        app.logger.error(response)
        return jsonify(response), 400
    except OpStkAuthenticationError as e:
        response = {"error": type(e).__name__, "message": str(e)}
        app.logger.error(response)
        return jsonify(response), 401
    except Exception as e:
        response = {"error": f"An unexpected error occurred: {e.__class__.__name__}", "message": str(e)}
        stat_code = 500
        app.logger.error(response)
        if 'http_status' in dir(e):
            stat_code = e.http_status
        return jsonify(response), stat_code
    finally:
        app.logger.info(f"Finished - Creating new CM_ project and user in Openstack")
        app.logger.debug("Disconnecting Handler")
        api_handler.disconnect()
        api_handler = None

@app.route('/update_status/<type>/<id>', methods=['POST'])
def update_status(type, id):
    config = {'log_level': 'debug', 'openstack': {}}
    app.logger.info(f"\nStarting - Updating status for {type}:{id}")
    try:
        req_data = request.get_json()
        app.logger.debug(req_data)
        if 'cloud_env' not in req_data:
            raise APIServerDefError("No Authentication data received.", 400)
        if 'action' not in req_data:
            raise APIServerDefError("Invalid data. 'action' is required.", 400)

        config['openstack'] = req_data['cloud_env']
        action = req_data['action']

        api_handler = APIHandler(config, log_file, clients=['nova', 'heat'])
        app.logger.debug(f"Successfully created APIHandler")

        result = api_handler.update_status(type, id, action)
        # Check if update function returned a dict (will happen if type=racks and fallback was called)
        if isinstance(result, dict):
            if result['outcome'] == 'failure':
                return jsonify({"error": "Status change failure", "message": "; ".join(result["failure"])}), 409
            elif result['outcome'] == 'partial failure':
                return jsonify({"error": "Partial status change failure", "message": "; ".join(result["failure"])}), 207

        app.logger.debug(f"Successfully submitted {action} request for {type} {id}. Request id: {result}")
        resp = {"success": True}
        return jsonify(resp), 202
    except APIServerDefError as e:
        response = {"error": type(e).__name__, "message": str(e)}
        app.logger.error(response)
        return jsonify(response), 400
    except keystoneauth1.exceptions.http.Unauthorized as e:
        response = {"error": "Unauthorized", "message": "Unauthorized"}
        app.logger.error(response)
        return jsonify(response), 401
    except novaclient.exceptions.Conflict as e:
        response = {"error": "Conflict", "message": e.message}
        app.logger.error(response)
        return jsonify(response), 409
    except novaclient.exceptions.NotFound as e:
        response = {"error": "Not found", "message": e.message}
        app.logger.error(response)
        return jsonify(response), 404
    except OpStkAuthenticationError as e:
        response = {"error": type(e).__name__, "message": str(e)}
        app.logger.error(response)
        return jsonify(response), 400
    except Exception as e:
        response = {"error": f"An unexpected error occurred: {e.__class__.__name__}", "message": str(e)}
        stat_code = 500
        app.logger.error(response)
        if 'http_status' in dir(e):
            stat_code = e.http_status
        return jsonify(response), stat_code
    finally:
        app.logger.info(f"Finished - Updating status")
        app.logger.debug("Disconnecting Handler")
        try:
          api_handler.disconnect()
          api_handler = None
        except NameError:
          api_handler = None

@app.route('/key_pairs', methods=['POST'])
def create_keypair():
    config = {'log_level': 'debug', 'openstack': {}}
    app.logger.info(f"\nStarting - Creating keypair in Openstack")
    try:
        req_data = request.get_json()
        app.logger.debug(req_data)
        if 'cloud_env' not in req_data:
            raise APIServerDefError("No Authentication data received.", 400)
        if 'key_pair' not in req_data:
            raise APIServerDefError("Invalid data. 'key_pair' is required.", 400)

        config['openstack'] = req_data['cloud_env']
        key_pair = req_data['key_pair']

        api_handler = APIHandler(config, log_file, clients=['nova'])
        app.logger.debug(f"Successfully created APIHandler")

        result = api_handler.create_keypair(key_pair["name"], key_type=key_pair["key_type"], imported_pub_key=key_pair["public_key"])

        app.logger.debug(f"Successfully submitted create key pair request")

        resp = {"success": True, "key_pair": result}
        return jsonify(resp), 202
    except APIServerDefError as e:
        response = {"error": type(e).__name__, "message": str(e)}
        app.logger.error(response)
        return jsonify(response), 400
    except keystoneauth1.exceptions.http.Unauthorized as e:
        response = {"error": "Unauthorized", "message": "Unauthorized"}
        app.logger.error(response)
        return jsonify(response), 401
    except novaclient.exceptions.Conflict as e:
        response = {"error": "Conflict", "message": e.message}
        app.logger.error(response)
        return jsonify(response), 409
    except novaclient.exceptions.NotFound as e:
        response = {"error": "Not found", "message": e.message}
        app.logger.error(response)
        return jsonify(response), 404
    except OpStkAuthenticationError as e:
        response = {"error": type(e).__name__, "message": str(e)}
        app.logger.error(response)
        return jsonify(response), 400
    except Exception as e:
        response = {"error": f"An unexpected error occurred: {e.__class__.__name__}", "message": str(e)}
        stat_code = 500
        app.logger.error(response)
        if 'http_status' in dir(e):
            stat_code = e.http_status
        return jsonify(response), stat_code
    finally:
        app.logger.info(f"Finished - Creating keypair in Openstack")
        app.logger.debug("Disconnecting Handler")
        try:
          api_handler.disconnect()
          api_handler = None
        except NameError:
          api_handler = None

@app.route('/key_pairs', methods=['GET'])
def list_keypairs():
    config = {'log_level': 'debug', 'openstack': {}}
    app.logger.info(f"\nStarting - Listing keypairs")
    try:
        req_data = request.get_json()
        app.logger.debug(req_data)
        if 'cloud_env' not in req_data:
            raise APIServerDefError("No Authentication data received.", 400)

        config['openstack'] = req_data['cloud_env']

        api_handler = APIHandler(config, log_file, clients=['nova'])
        app.logger.debug(f"Successfully created APIHandler")

        result = api_handler.list_keypairs()

        app.logger.debug(f"Successfully obtained list of key pairs")

        resp = {"success": True, 'key_pairs': result}
        return jsonify(resp), 202
    except APIServerDefError as e:
        response = {"error": type(e).__name__, "message": str(e)}
        app.logger.error(response)
        return jsonify(response), 400
    except keystoneauth1.exceptions.http.Unauthorized as e:
        response = {"error": "Unauthorized", "message": "Unauthorized"}
        app.logger.error(response)
        return jsonify(response), 401
    except novaclient.exceptions.Conflict as e:
        response = {"error": "Conflict", "message": e.message}
        app.logger.error(response)
        return jsonify(response), 409
    except novaclient.exceptions.NotFound as e:
        response = {"error": "Not found", "message": e.message}
        app.logger.error(response)
        return jsonify(response), 404
    except OpStkAuthenticationError as e:
        response = {"error": type(e).__name__, "message": str(e)}
        app.logger.error(response)
        return jsonify(response), 400
    except Exception as e:
        response = {"error": f"An unexpected error occurred: {e.__class__.__name__}", "message": str(e)}
        stat_code = 500
        app.logger.error(response)
        if 'http_status' in dir(e):
            stat_code = e.http_status
        return jsonify(response), stat_code
    finally:
        app.logger.info(f"Finished - Listing keypairs")
        app.logger.debug("Disconnecting Handler")
        try:
          api_handler.disconnect()
          api_handler = None
        except NameError:
          api_handler = None

@app.route('/key_pairs', methods=['DELETE'])
def delete_keypairs():
    config = {'log_level': 'debug', 'openstack': {}}
    app.logger.info(f"\nStarting - Deleting keypair")
    try:
        req_data = request.get_json()
        app.logger.debug(req_data)
        if 'cloud_env' not in req_data:
            raise APIServerDefError("No Authentication data received.", 400)
        if 'keypair_name' not in req_data:
            raise APIServerDefError("No Keypair to delete given.", 400)

        config['openstack'] = req_data['cloud_env']

        api_handler = APIHandler(config, log_file, clients=['nova'])
        app.logger.debug(f"Successfully created APIHandler")

        result = api_handler.delete_keypair()

        app.logger.debug(f"Successfully deleted key pair {req_data['keypair_name']}")

        resp = {"success": True, 'key_pairs': result}
        return jsonify(resp), 202
    except APIServerDefError as e:
        response = {"error": type(e).__name__, "message": str(e)}
        app.logger.error(response)
        return jsonify(response), 400
    except keystoneauth1.exceptions.http.Unauthorized as e:
        response = {"error": "Unauthorized", "message": "Unauthorized"}
        app.logger.error(response)
        return jsonify(response), 401
    except novaclient.exceptions.Conflict as e:
        response = {"error": "Conflict", "message": e.message}
        app.logger.error(response)
        return jsonify(response), 409
    except novaclient.exceptions.NotFound as e:
        response = {"error": "Not found", "message": e.message}
        app.logger.error(response)
        return jsonify(response), 404
    except OpStkAuthenticationError as e:
        response = {"error": type(e).__name__, "message": str(e)}
        app.logger.error(response)
        return jsonify(response), 400
    except Exception as e:
        response = {"error": f"An unexpected error occurred: {e.__class__.__name__}", "message": str(e)}
        stat_code = 500
        app.logger.error(response)
        if 'http_status' in dir(e):
            stat_code = e.http_status
        return jsonify(response), stat_code
    finally:
        app.logger.info(f"Finished - Deleting keypair")
        app.logger.debug("Disconnecting Handler")
        try:
          api_handler.disconnect()
          api_handler = None
        except NameError:
          api_handler = None

@app.route('/')
def running():
    app.logger.info("\nRunning\n")
    return "\nRunning\n"

def run_app():
    app.run(host='0.0.0.0', port=42356)
