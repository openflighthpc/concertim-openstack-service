# Local imports
from con_opstk.data_handler.api_handler.api_handler import APIHandler
from con_opstk.data_handler.utils.auth import authenticate_headers
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
import sys
import json
import traceback 


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
        

@app.route('/create_user', methods=['POST'])
def create_user():
    config = {'log_level': config_file['log_level'], 'openstack': {}}
    app.logger.info(f"Starting - Creating new user in Openstack")
    try:

        req_data = request.get_json()
        app.logger.debug(req_data)
        if 'cloud_env' not in req_data:
            raise APIServerDefError("No Authentication data recieved.", 400)
        if 'username' not in req_data or 'password' not in req_data:
            raise APIServerDefError("Invalid user data. 'username' and 'password' are required.", 400)

        # Setup Config
        config['openstack'] = req_data['cloud_env']

        username = req_data['username']
        password = req_data['password']
        email = req_data['email'] if 'email' in req_data else ''

        api_handler = APIHandler(config, log_file)
        app.logger.debug(f"Successfully created APIHandler")

        user = api_handler.create_user(username, password, email)
        app.logger.debug(f"Successfully created new User")


        resp = {"username": username, "user_id": user.id}
        return make_response(resp,201)
    except APIServerDefError as e:
        response = {"error": type(e).__name__, "message": str(e), "traceback" : traceback.format_exc()}
        app.logger.error(response)
        return jsonify(response), 400
    except OpStkAuthenticationError as e:
        response = {"error": type(e).__name__, "message": str(e), "traceback" : traceback.format_exc()}
        app.logger.error(response)
        return jsonify(response), 401
    except Exception as e:
        response = {"error": f"An unexpected error occurred: {e.__class__.__name__}", "message": str(e), "traceback" : traceback.format_exc()}
        stat_code = 500
        app.logger.error(response)
        if 'http_status' in dir(e):
            stat_code = e.http_status
        return jsonify(response), stat_code
    finally:
        app.logger.info(f"Finished - Creating new CM_ user in Openstack")
        app.logger.debug("Disconnecting Handler")
        try:
            api_handler.disconnect()
            api_handler = None
        except NameError:
            api_handler = None

@app.route('/create_team', methods=['POST'])
def create_team():
    config = {'log_level': config_file['log_level'], 'openstack': {}}
    app.logger.info(f"Starting - Creating new 'CM_' team project in Openstack and Billing account")
    try:
        if not authenticate_headers(request.headers, app.logger):
            resp = {"message" : "Request not authenticated"}
            return make_response(resp, 401)
        
        req_data = request.get_json()
        app.logger.debug(req_data)
        if 'cloud_env' not in req_data:
            raise APIServerDefError("No Authentication data recieved.", 400)
        if 'name' not in req_data:
            raise APIServerDefError("Invalid user data. 'name' is required.", 400)

        # Setup Config
        config['openstack'] = req_data['cloud_env']
        config['billing_platform'] = config_file['billing_platform']
        config[config_file['billing_platform']] = config_file[config_file['billing_platform']]

        name = req_data['name']
        
        api_handler = APIHandler(config, log_file, billing_enabled=True)
        app.logger.debug(f"Successfully created APIHandler")

        project, billing_account_id = api_handler.create_team_project(name)
        app.logger.debug(f"Successfully created new team details")


        resp = {"name": name, "project_id": project.id, "billing_account_id": billing_account_id}
        return make_response(resp,201)
    except APIServerDefError as e:
        response = {"error": type(e).__name__, "message": str(e), "traceback" : traceback.format_exc()}
        app.logger.error(response)
        return jsonify(response), 400
    except OpStkAuthenticationError as e:
        response = {"error": type(e).__name__, "message": str(e), "traceback" : traceback.format_exc()}
        app.logger.error(response)
        return jsonify(response), 401
    except Exception as e:
        response = {"error": f"An unexpected error occurred: {e.__class__.__name__}", "message": str(e), "traceback" : traceback.format_exc()}
        stat_code = 500
        app.logger.error(response)
        if 'http_status' in dir(e):
            stat_code = e.http_status
        return jsonify(response), stat_code
    finally:
        app.logger.info(f"Finished - Creating new CM_ team project in Openstack and Billing Account")
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
        if not authenticate_headers(request.headers, app.logger):
            resp = {"message" : "Request not authenticated"}
            return make_response(resp, 401)
        
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
        response = {"error": type(e).__name__, "message": str(e), "traceback" : traceback.format_exc()}
        app.logger.error(response)
        return jsonify(response), 400
    except keystoneauth1.exceptions.http.Unauthorized as e:
        response = {"error": "Unauthorized", "message": "Unauthorized", "traceback" : traceback.format_exc()}
        app.logger.error(response)
        return jsonify(response), 401
    except novaclient.exceptions.Conflict as e:
        response = {"error": "Conflict", "message": e.message, "traceback" : traceback.format_exc()}
        app.logger.error(response)
        return jsonify(response), 409
    except novaclient.exceptions.NotFound as e:
        response = {"error": "Not found", "message": e.message, "traceback" : traceback.format_exc()}
        app.logger.error(response)
        return jsonify(response), 404
    except OpStkAuthenticationError as e:
        response = {"error": type(e).__name__, "message": str(e), "traceback" : traceback.format_exc()}
        app.logger.error(response)
        return jsonify(response), 400
    except Exception as e:
        response = {"error": f"An unexpected error occurred: {e.__class__.__name__}", "message": str(e), "traceback" : traceback.format_exc()}
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
        if not authenticate_headers(request.headers, app.logger):
            resp = {"message" : "Request not authenticated"}
            return make_response(resp, 401)
        
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
        response = {"error": type(e).__name__, "message": str(e), "traceback" : traceback.format_exc()}
        app.logger.error(response)
        return jsonify(response), 400
    except keystoneauth1.exceptions.http.Unauthorized as e:
        response = {"error": "Unauthorized", "message": "Unauthorized", "traceback" : traceback.format_exc()}
        app.logger.error(response)
        return jsonify(response), 401
    except novaclient.exceptions.Conflict as e:
        response = {"error": "Conflict", "message": e.message, "traceback" : traceback.format_exc()}
        app.logger.error(response)
        return jsonify(response), 409
    except novaclient.exceptions.NotFound as e:
        response = {"error": "Not found", "message": e.message, "traceback" : traceback.format_exc()}
        app.logger.error(response)
        return jsonify(response), 404
    except OpStkAuthenticationError as e:
        response = {"error": type(e).__name__, "message": str(e), "traceback" : traceback.format_exc()}
        app.logger.error(response)
        return jsonify(response), 400
    except Exception as e:
        response = {"error": f"An unexpected error occurred: {e.__class__.__name__}", "message": str(e), "traceback" : traceback.format_exc()}
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
        if not authenticate_headers(request.headers, app.logger):
            resp = {"message" : "Request not authenticated"}
            return make_response(resp, 401)
        
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
        response = {"error": type(e).__name__, "message": str(e), "traceback" : traceback.format_exc()}
        app.logger.error(response)
        return jsonify(response), 400
    except keystoneauth1.exceptions.http.Unauthorized as e:
        response = {"error": "Unauthorized", "message": "Unauthorized", "traceback" : traceback.format_exc()}
        app.logger.error(response)
        return jsonify(response), 401
    except novaclient.exceptions.Conflict as e:
        response = {"error": "Conflict", "message": e.message, "traceback" : traceback.format_exc()}
        app.logger.error(response)
        return jsonify(response), 409
    except novaclient.exceptions.NotFound as e:
        response = {"error": "Not found", "message": e.message, "traceback" : traceback.format_exc()}
        app.logger.error(response)
        return jsonify(response), 404
    except OpStkAuthenticationError as e:
        response = {"error": type(e).__name__, "message": str(e), "traceback" : traceback.format_exc()}
        app.logger.error(response)
        return jsonify(response), 400
    except Exception as e:
        response = {"error": f"An unexpected error occurred: {e.__class__.__name__}", "message": str(e), "traceback" : traceback.format_exc()}
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
        if not authenticate_headers(request.headers, app.logger):
            resp = {"message" : "Request not authenticated"}
            return make_response(resp, 401)
        
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
        response = {"error": type(e).__name__, "message": str(e), "traceback" : traceback.format_exc()}
        app.logger.error(response)
        return jsonify(response), 400
    except keystoneauth1.exceptions.http.Unauthorized as e:
        response = {"error": "Unauthorized", "message": "Unauthorized", "traceback" : traceback.format_exc()}
        app.logger.error(response)
        return jsonify(response), 401
    except novaclient.exceptions.Conflict as e:
        response = {"error": "Conflict", "message": e.message, "traceback" : traceback.format_exc()}
        app.logger.error(response)
        return jsonify(response), 409
    except novaclient.exceptions.NotFound as e:
        response = {"error": "Not found", "message": e.message, "traceback" : traceback.format_exc()}
        app.logger.error(response)
        return jsonify(response), 404
    except OpStkAuthenticationError as e:
        response = {"error": type(e).__name__, "message": str(e), "traceback" : traceback.format_exc()}
        app.logger.error(response)
        return jsonify(response), 400
    except Exception as e:
        response = {"error": f"An unexpected error occurred: {e.__class__.__name__}", "message": str(e), "traceback" : traceback.format_exc()}
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
        if not authenticate_headers(request.headers, app.logger):
            resp = {"message" : "Request not authenticated"}
            return make_response(resp, 401)
        
        req_data = request.get_json()
        app.logger.debug(req_data)
        if 'invoice' not in req_data or 'billing_account_id' not in req_data['invoice']:
            raise APIServerDefError("No Billling Account data recieved.", 400)
        if 'invoice' not in req_data or 'target_date' not in req_data['invoice']:
            raise APIServerDefError("No Invoice Date data recieved.", 400)

        api_handler = APIHandler(config_file, log_file, billing_enabled=True)
        app.logger.debug(f"Successfully created APIHandler")

        invoice = api_handler.get_latest_invoice(req_data['invoice']['billing_account_id'])

        response = {"invoice_html": invoice['data']}
        return make_response(response, invoice['status'])
    except APIServerDefError as e:
        response = {"error": type(e).__name__, "message": str(e), "traceback" : traceback.format_exc()}
        app.logger.error(response)
        return jsonify(response), 400
    except OpStkAuthenticationError as e:
        response = {"error": type(e).__name__, "message": str(e), "traceback" : traceback.format_exc()}
        app.logger.error(response)
        return jsonify(response), 401
    except Exception as e:
        response = {"error": f"An unexpected error occurred: {e.__class__.__name__}", "message": str(e), "traceback" : traceback.format_exc()}
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


@app.route('/get_draft_invoice', methods=['POST'])
def get_draft_invoice():
    app.logger.info(f"Starting - Getting user draft invoice")
    try:
        if not authenticate_headers(request.headers, app.logger):
            resp = {"message" : "Request not authenticated"}
            return make_response(resp, 401)
       
        req_data = request.get_json()
        app.logger.debug(req_data)
        if 'invoice' not in req_data or 'billing_account_id' not in req_data['invoice']:
            raise APIServerDefError("No Billling Account data recieved.", 400)
        if 'invoice' not in req_data or 'target_date' not in req_data['invoice']:
            raise APIServerDefError("No Invoice Date data recieved.", 400)

        api_handler = APIHandler(config_file, log_file, billing_enabled=True)
        app.logger.debug(f"Successfully created APIHandler")

        response = api_handler.get_draft_invoice(req_data['invoice']['billing_account_id'])

        resp = {"draft_invoice": response['data']}
        return make_response(resp, response['status'])
    
    except APIServerDefError as e:
        response = {"error": type(e).__name__, "message": str(e), "traceback" : traceback.format_exc()}
        app.logger.error(response)
        return jsonify(response), 400
    except OpStkAuthenticationError as e:
        response = {"error": type(e).__name__, "message": str(e), "traceback" : traceback.format_exc()}
        app.logger.error(response)
        return jsonify(response), 401
    except Exception as e:
        response = {"error": f"An unexpected error occurred: {e.__class__.__name__}", "message": str(e), "traceback" : traceback.format_exc()}
        stat_code = 500
        app.logger.error(response)
        if 'http_status' in dir(e):
            stat_code = e.http_status
        return jsonify(response), stat_code
    finally:
        app.logger.info(f"Finished - Getting user draft invoice")
        app.logger.debug("Disconnecting Handler")
        try:
            billing_handler.disconnect()
            billing_handler = None
        except NameError:
            billing_handler = None

@app.route('/add_credits', methods=['POST'])
def add_credits():
    app.logger.info(f"Starting - Adding credits to Billing platform")
    try:
        if not authenticate_headers(request.headers, app.logger):
            resp = {"message" : "Request not authenticated"}
            return make_response(resp, 401)
        
        req_data = request.get_json()
        app.logger.debug(req_data)
        if 'credits' not in req_data or 'credits_to_add' not in req_data['credits']:
            raise APIServerDefError("No Credit data recieved.", 400)
        
        if 'credits' not in req_data or 'billing_account_id' not in req_data['credits']:
            raise APIServerDefError("No Credit data recieved.", 400)
        
        api_handler = APIHandler(config_file, log_file, billing_enabled=True)
        app.logger.debug(f"Successfully created APIHandler")

        response = api_handler.add_credits(req_data['credits']['billing_account_id'], req_data['credits']['credits_to_add'])

        resp = {"credits": response['data']}
        return make_response(resp, response['status'])
    
    except APIServerDefError as e:
        response = {"error": type(e).__name__, "message": str(e), "traceback" : traceback.format_exc()}
        app.logger.error(response)
        return jsonify(response), 400
    except OpStkAuthenticationError as e:
        response = {"error": type(e).__name__, "message": str(e), "traceback" : traceback.format_exc()}
        app.logger.error(response)
        return jsonify(response), 401
    except Exception as e:
        response = {"error": f"An unexpected error occurred: {e.__class__.__name__}", "message": str(e), "traceback" : traceback.format_exc()}
        stat_code = 500
        app.logger.error(response)
        if 'http_status' in dir(e):
            stat_code = e.http_status
        return jsonify(response), stat_code
    finally:
        app.logger.info(f"Finished - Adding Credits")
        app.logger.debug("Disconnecting Handler")
        try:
            billing_handler.disconnect()
            billing_handler = None
        except NameError:
            billing_handler = None

@app.route('/get_credits', methods=['POST'])
def get_credits():
    app.logger.info(f"Starting - Getting Credits for account")
    try:
        if not authenticate_headers(request.headers, app.logger):
            resp = {"message" : "Request not authenticated"}
            return make_response(resp, 401)
        
        req_data = request.get_json()
        app.logger.debug(req_data)
        
        if 'credits' not in req_data or 'billing_account_id' not in req_data['credits']:
            raise APIServerDefError("No Billing account id recieved.", 400)
        
        api_handler = APIHandler(config_file, log_file, clients=None, billing_enabled=True)
        app.logger.debug(f"Successfully created APIHandler")

        response = api_handler.get_credits(req_data['credits']['billing_account_id'])

        resp = {"credits": response['data']}
        return make_response(resp, response['status'])
    
    except APIServerDefError as e:
        response = {"error": type(e).__name__, "message": str(e), "traceback" : traceback.format_exc()}
        app.logger.error(response)
        return jsonify(response), 400
    except OpStkAuthenticationError as e:
        response = {"error": type(e).__name__, "message": str(e), "traceback" : traceback.format_exc()}
        app.logger.error(response)
        return jsonify(response), 401
    except Exception as e:
        response = {"error": f"An unexpected error occurred: {e.__class__.__name__}", "message": str(e), "traceback" : traceback.format_exc()}
        stat_code = 500
        app.logger.error(response)
        if 'http_status' in dir(e):
            stat_code = e.http_status
        return jsonify(response), stat_code
    finally:
        app.logger.info(f"Finished - Getting Credits for account")
        app.logger.debug("Disconnecting Handler")
        try:
            billing_handler.disconnect()
            billing_handler = None
        except NameError:
            billing_handler = None

@app.route('/create_order', methods=['POST'])
def create_order():
    app.logger.info(f"Starting - Creating Order")
    try:
        if not authenticate_headers(request.headers, app.logger):
            resp = {"message" : "Request not authenticated"}
            return make_response(resp, 401)
        
        req_data = request.get_json()
        app.logger.debug(req_data)
        if 'order' not in req_data or 'billing_account_id' not in req_data['order']:
            raise APIServerDefError("No account id data recieved.", 400)
        
        #if 'order' not in req_data or 'os_stack_id' not in req_data['order']:
        #    raise APIServerDefError("OS Stack ID not received.", 400)
        
        api_handler = APIHandler(config_file, log_file, clients=None, billing_enabled=True)
        app.logger.debug(f"Successfully created APIHandler")

        response = api_handler.create_order(req_data['order']['billing_account_id'])

        resp = {"order": response['data']}
        return make_response(resp, response['status'])
    
    except APIServerDefError as e:
        response = {"error": type(e).__name__, "message": str(e), "traceback" : traceback.format_exc()}
        app.logger.error(response)
        return jsonify(response), 400
    except OpStkAuthenticationError as e:
        response = {"error": type(e).__name__, "message": str(e), "traceback" : traceback.format_exc()}
        app.logger.error(response)
        return jsonify(response), 401
    except Exception as e:
        response = {"error": f"An unexpected error occurred: {e.__class__.__name__}", "message": str(e), "traceback" : traceback.format_exc()}
        stat_code = 500
        app.logger.error(response)
        if 'http_status' in dir(e):
            stat_code = e.http_status
        return jsonify(response), stat_code
    finally:
        app.logger.info(f"Finished - Creating Order")
        app.logger.debug("Disconnecting Handler")
        try:
            billing_handler.disconnect()
            billing_handler = None
        except NameError:
            billing_handler = None

@app.route('/delete_order', methods=['POST'])
def delete_order():
    app.logger.info(f"Starting - Deleting Order")
    try:
        if not authenticate_headers(request.headers, app.logger):
            resp = {"message" : "Request not authenticated"}
            return make_response(resp, 401)
        
        req_data = request.get_json()
        app.logger.debug(req_data)
        if 'order' not in req_data or 'order_id' not in req_data['order']:
            raise APIServerDefError("No order id data recieved.", 400)
        
       
        api_handler = APIHandler(config_file, log_file, clients=None, billing_enabled=True)
        app.logger.debug(f"Successfully created APIHandler")

        response = api_handler.delete_order(req_data['order']['order_id'])

        resp = {"order": req_data['order']['order_id']}
        return make_response(resp, response['status'])
    
    except APIServerDefError as e:
        response = {"error": type(e).__name__, "message": str(e), "traceback" : traceback.format_exc()}
        app.logger.error(response)
        return jsonify(response), 400
    except OpStkAuthenticationError as e:
        response = {"error": type(e).__name__, "message": str(e), "traceback" : traceback.format_exc()}
        app.logger.error(response)
        return jsonify(response), 401
    except Exception as e:
        response = {"error": f"An unexpected error occurred: {e.__class__.__name__}", "message": str(e), "traceback" : traceback.format_exc()}
        stat_code = 500
        app.logger.error(response)
        if 'http_status' in dir(e):
            stat_code = e.http_status
        return jsonify(response), stat_code
    finally:
        app.logger.info(f"Finished - Deleting Order")
        app.logger.debug("Disconnecting Handler")
        try:
            billing_handler.disconnect()
            billing_handler = None
        except NameError:
            billing_handler = None


@app.route('/delete_user', methods=['DELETE'])
def delete_user():
    config = {'log_level': config_file['log_level'], 'openstack': {}}
    app.logger.info(f"Starting - Deleting User Objects")
    try:
        if not authenticate_headers(request.headers, app.logger):
            resp = {"message" : "Request not authenticated"}
            return make_response(resp, 401)
        
        req_data = request.get_json()
        app.logger.debug(req_data)
        if 'cloud_env' not in req_data:
            raise APIServerDefError("No Authentication data recieved.", 400)
        if 'user_info' not in req_data:
            raise APIServerDefError("No User data received.", 400)
        if 'project_id' not in req_data['user_info'] or 'cloud_user_id' not in req_data['user_info'] or 'billing_acct_id' not in req_data['user_info']:
            raise APIServerDefError("Invalid user data. 'project_id', 'cloud_user_id' and 'billing_acct_id' are required.", 400)

        # Setup Config
        config['openstack'] = req_data['cloud_env']
        config['billing_platform'] = config_file['billing_platform']
        config[config_file['billing_platform']] = config_file[config_file['billing_platform']]
        
        api_handler = APIHandler(config, log_file, billing_enabled=True)
        app.logger.debug(f"Successfully created APIHandler")

        attempt = api_handler.delete_user(req_data['user_info']['cloud_user_id'], req_data['user_info']['project_id'], req_data['user_info']['billing_acct_id'])
        app.logger.debug(f"Successfully deleted User Objects")

        resp = {"success": True}
        return make_response(resp,204)
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
        app.logger.info(f"Finished - Deleting User Objects")
        app.logger.debug("Disconnecting Handler")
        try:
            api_handler.disconnect()
            api_handler = None
        except NameError:
            api_handler = None

@app.route('/list_paginated_invoices', methods=['POST'])
def list_paginated_invoices():
    app.logger.info(f"Starting - List paginated invoices")
    try:
        if not authenticate_headers(request.headers, app.logger):
            resp = {"message" : "Request not authenticated"}
            return make_response(resp, 401)
        
        req_data = request.get_json()
        app.logger.debug(req_data)
        if 'invoices' not in req_data or 'billing_account_id' not in req_data['invoices']:
            raise APIServerDefError("No account id data recieved.", 400)
        
        api_handler = APIHandler(config_file, log_file, clients=None, billing_enabled=True)
        app.logger.debug(f"Successfully created APIHandler")

        offset = 0
        if 'offset' in req_data['invoices']:
            offset = req_data['invoices']['offset']

        limit = 100
        if 'limit' in req_data['invoices']:
            limit = req_data['invoices']['limit']
        

        response = api_handler.list_account_invoice_paginated(billing_account_id=req_data['invoices']['billing_account_id'], offset=offset, limit=limit)

        total_invoices = -1
        if 'X-Killbill-Pagination-MaxNbRecords' in response['headers']:
            total_invoices = response['headers']['X-Killbill-Pagination-MaxNbRecords']


        resp = {"total_invoices": total_invoices, "invoices": response['data']}
        return make_response(resp, response['status'])
    
    except APIServerDefError as e:
        response = {"error": type(e).__name__, "message": str(e), "traceback" : traceback.format_exc()}
        app.logger.error(response)
        return jsonify(response), 400
    except OpStkAuthenticationError as e:
        response = {"error": type(e).__name__, "message": str(e), "traceback" : traceback.format_exc()}
        app.logger.error(response)
        return jsonify(response), 401
    except Exception as e:
        response = {"error": f"An unexpected error occurred: {e.__class__.__name__}", "message": str(e), "traceback": traceback.format_exc()}
        stat_code = 500
        app.logger.error(response)
        if 'http_status' in dir(e):
            stat_code = e.http_status
        return jsonify(response), stat_code
    finally:
        app.logger.info(f"Finished - Listing paginated invoices")
        app.logger.debug("Disconnecting Handler")
        try:
            billing_handler.disconnect()
            billing_handler = None
        except NameError:
            billing_handler = None

@app.route('/get_account_invoice', methods=['POST'])
def get_account_invoice():
    app.logger.info(f"Starting - Getting account invoice")
    try:
        if not authenticate_headers(request.headers, app.logger):
            resp = {"message" : "Request not authenticated"}
            return make_response(resp, 401)
        
        req_data = request.get_json()
        app.logger.debug(req_data)
        if 'invoice' not in req_data or 'billing_account_id' not in req_data['invoice']:
            raise APIServerDefError("No Billling Account data recieved.", 400)
        if 'invoice' not in req_data or 'invoice_id' not in req_data['invoice']:
            raise APIServerDefError("No Invoice ID data recieved.", 400)

        api_handler = APIHandler(config_file, log_file, clients=None, billing_enabled=True)
        app.logger.debug(f"Successfully created APIHandler")

        response = api_handler.get_invoice_by_id(req_data['invoice']['invoice_id'])

        resp = {"account_invoice": response['data']}
        return make_response(resp, response['status'])
    
    except APIServerDefError as e:
        response = {"error": type(e).__name__, "message": str(e), "traceback" : traceback.format_exc()}
        app.logger.error(response)
        return jsonify(response), 400
    except OpStkAuthenticationError as e:
        response = {"error": type(e).__name__, "message": str(e), "traceback" : traceback.format_exc()}
        app.logger.error(response)
        return jsonify(response), 401
    except Exception as e:
        response = {"error": f"An unexpected error occurred: {e.__class__.__name__}", "message": str(e), "traceback" : traceback.format_exc()}
        stat_code = 500
        app.logger.error(response)
        if 'http_status' in dir(e):
            stat_code = e.http_status
        return jsonify(response), stat_code
    finally:
        app.logger.info(f"Finished - Getting account invoice by id")
        app.logger.debug("Disconnecting Handler")
        try:
            billing_handler.disconnect()
            billing_handler = None
        except NameError:
            billing_handler = None

@app.route('/change_user_details', methods=['POST'])
def change_user_details():
    config = {'log_level': config_file['log_level'], 'openstack': {}}
    app.logger.info(f"Starting - Updating User details")
    try:
        if not authenticate_headers(request.headers, app.logger):
            resp = {"message" : "Request not authenticated"}
            return make_response(resp, 401)
        
        req_data = request.get_json()
        app.logger.debug(req_data)
        if 'cloud_env' not in req_data:
            raise APIServerDefError("No Authentication data recieved.", 400)
        if 'user_info' not in req_data:
            raise APIServerDefError("No User data received.", 400)
        if 'cloud_user_id' not in req_data['user_info'] or 'billing_acct_id' not in req_data['user_info'] or 'new_data' not in req_data['user_info']:
            raise APIServerDefError("Invalid user data. 'cloud_user_id', 'billing_acct_id' and 'new_data' block are required.", 400)

        # Setup Config
        config['openstack'] = req_data['cloud_env']
        config['billing_platform'] = config_file['billing_platform']
        config[config_file['billing_platform']] = config_file[config_file['billing_platform']]
        
        api_handler = APIHandler(config, log_file, billing_enabled=True)
        app.logger.debug(f"Successfully created APIHandler")

        changed = api_handler.change_user_details(req_data['user_info']['cloud_user_id'], req_data['user_info']['billing_acct_id'], req_data['user_info']['new_data'])
        app.logger.debug(f"Successfully updated User's {changed}")

        resp = {"updated": changed}
        return make_response(resp,204)
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
        app.logger.info(f"Finished - Updating User details")
        app.logger.debug("Disconnecting Handler")
        try:
            api_handler.disconnect()
            api_handler = None
        except NameError:
            api_handler = None

@app.route('/add_order_tag', methods=['POST'])
def add_order_tag():
    app.logger.info(f"Starting - Adding tag to Order")
    try:
        if not authenticate_headers(request.headers, app.logger):
            resp = {"message" : "Request not authenticated"}
            return make_response(resp, 401)
        
        req_data = request.get_json()
        app.logger.debug(req_data)
        if 'tag' not in req_data or 'order_id' not in req_data['tag']:
            raise APIServerDefError("No Order ID data recieved.", 400)
        if 'tag' not in req_data or 'tag_name' not in req_data['tag'] or 'tag_value' not in req_data['tag']:
            raise APIServerDefError("No Tag data recieved.", 400)

        api_handler = APIHandler(config_file, log_file, billing_enabled=True)
        app.logger.debug(f"Successfully created APIHandler")

        response = api_handler.add_order_tag(req_data['tag']['order_id'], req_data['tag']['tag_name'], req_data['tag']['tag_value'])

        resp = {"tag": response['data']}
        return make_response(resp, response['status'])
    
    except APIServerDefError as e:
        response = {"error": type(e).__name__, "message": str(e), "traceback" : traceback.format_exc()}
        app.logger.error(response)
        return jsonify(response), 400
    except OpStkAuthenticationError as e:
        response = {"error": type(e).__name__, "message": str(e), "traceback" : traceback.format_exc()}
        app.logger.error(response)
        return jsonify(response), 401
    except Exception as e:
        response = {"error": f"An unexpected error occurred: {e.__class__.__name__}", "message": str(e), "traceback" : traceback.format_exc()}
        stat_code = 500
        app.logger.error(response)
        if 'http_status' in dir(e):
            stat_code = e.http_status
        return jsonify(response), stat_code
    finally:
        app.logger.info(f"Finished - Adding tag to order")
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
