# Local imports
from con_opstk.data_handler.api_handler.api_handler import APIHandler
from con_opstk.openstack.exceptions import APIServerDefError, OpStkAuthenticationError
import con_opstk.app_definitions as app_paths
from con_opstk.utils.service_logger import SensitiveFormatter
# Py Packages
from flask import Flask, request, jsonify, make_response
from flask import Response
import logging
import importlib
# Openstack
import keystoneauth1.exceptions.http
import novaclient.exceptions

# Logging setup
formatter = SensitiveFormatter('[%(asctime)s] - %(levelname)-8s: %(module)-12s: %(funcName)-26s===>  %(message)s')
log_file = app_paths.LOG_DIR + 'api_server.log'
fh = logging.FileHandler(log_file)
fh.setFormatter(formatter)

# Flask app
app = Flask('api')
app.logger.addHandler(fh)
app.logger.setLevel(logging.DEBUG)

# Env config file
config_file = None

# Billing Services
BILLING_SERVICES = {'killbill': 'KillbillService', 'hostbill': 'HostbillService'}
BILLING_IMPORT_PATH = {'killbill': 'con_opstk.billing.killbill.killbill', 'hostbill': 'con_opstk.billing.hostbill.hostbill'}
        

@app.route('/create_user_project', methods=['POST'])
def create_user_project():
    config = {'log_level': config_file['log_level'], 'openstack': {}}
    app.logger.info(f"Starting - Creating new 'CM_' project and user in Openstack")
    try:
        req_data = request.get_json()
        app.logger.debug(req_data)
        if 'cloud_env' not in req_data:
            raise APIServerDefError("No Authentication data recieved.", 400)
        if 'username' not in req_data or 'password' not in req_data:
            raise APIServerDefError("Invalid user data. 'username' and 'password' are required.", 400)

        # Setup Config
        config['openstack'] = req_data['cloud_env']
        config['billing_platform'] = config_file['billing_platform']
        config[config_file['billing_platform']] = config_file[config_file['billing_platform']]

        username = req_data['username']
        password = req_data['password']
        email = req_data['email'] if 'email' in req_data else ''
        
        api_handler = APIHandler(config, log_file, billing_enabled=True)
        app.logger.debug(f"Successfully created APIHandler")

        user, project = api_handler.create_user_project(username, password, email)
        app.logger.debug(f"Successfully created new User and Project in Openstack")

        billing_acct_id = api_handler.create_new_billing_acct(username, email)
        app.logger.debug(f"Successfully created new Account in {config['billing_platform']}")

        resp = {"username": username, "user_id": user.id, "project_id": project.id, "billing_acct_id": billing_acct_id}
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
        try:
            api_handler.disconnect()
            api_handler = None
        except NameError:
            api_handler = None

@app.route('/update_status/<type>/<id>', methods=['POST'])
def update_status(type, id):
    config = {'log_level': config_file['log_level'], 'openstack': {}}
    app.logger.info(f"Starting - Updating status for {type}:{id}")
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
    config = {'log_level': config_file['log_level'], 'openstack': {}}
    app.logger.info(f"Starting - Creating keypair in Openstack")
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
    config = {'log_level': config_file['log_level'], 'openstack': {}}
    app.logger.info(f"Starting - Listing keypairs")
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
    config = {'log_level': config_file['log_level'], 'openstack': {}}
    app.logger.info(f"Starting - Deleting keypair")
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

        result = api_handler.delete_keypair(req_data['keypair_name'])

        app.logger.debug(f"Successfully deleted key pair {req_data['keypair_name']}")

        resp = {"success": True, 'key_pair_name': req_data['keypair_name']}
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


@app.route('/get_user_invoice', methods=['POST'])
def get_user_invoice():
    app.logger.info(f"Starting - Getting user current invoice")
    try:
        req_data = request.get_json()
        app.logger.debug(req_data)
        if 'invoice' not in req_data or 'billing_acct_id' not in req_data['invoice']:
            raise APIServerDefError("No Billling Account data recieved.", 400)
        if 'invoice' not in req_data or 'target_date' not in req_data['invoice']:
            raise APIServerDefError("No Invoice Date data recieved.", 400)

        #ImportedHandler = importlib.import_module(BILLING_HANDLERS[config_file['billing_platform']])
        billing_app = config_file['billing_platform']
        ImportedService = getattr(importlib.import_module(BILLING_IMPORT_PATH[billing_app]), BILLING_SERVICES[billing_app])

        billing_service = ImportedService(config_file, log_file)
        app.logger.debug(f"Successfully created {config_file['billing_platform']} service")

        invoice = billing_service.generate_invoice_html(req_data['invoice']['billing_acct_id'], req_data['invoice']['target_date'])

        resp = {"invoice_html": invoice}
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
        app.logger.info(f"Finished - Getting user invoice")
        app.logger.debug("Disconnecting Handler")
        try:
            billing_handler.disconnect()
            billing_handler = None
        except NameError:
            billing_handler = None


@app.route('/')
def running():
    app.logger.info("Running\n")
    return "Running\n"

def run_app(config_obj):
    global config_file
    config_file = config_obj
    app.run(host='0.0.0.0', port=42356)
