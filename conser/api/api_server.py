# Local imports
import conser.app_definitions as app_paths
from conser.factory.factory import Factory
from conser.utils.service_logger import SensitiveFormatter
import conser.exceptions as EXCP
from conser.api.header_auth import authenticate_headers

# Py Packages
from flask import Flask, request, jsonify, make_response
from flask import Response
import logging
import importlib
import sys
import json
import traceback


# Flask app
app = Flask('Concertim Service API')
conf_dict = None
log_file = None

#### BASE
@app.route('/')
def running():
    app.logger.info("Running\n")
    return "Running\n"



"""
----------- FUNCTIONS -----------
"""

def create_user():
    app.logger.info("Starting - Creating new 'CM_' user in Cloud")
    handler = None
    try:
        # Authenticate with JWT
        authenticate(request.headers)

        # Validate Required Data
        request_data = request.get_json()
        app.logger.debug(request_data)
        verify_required_data(request_data, 
            'cloud_env', 
            'username', 
            'name', 
            'email', 
            'password')
        
        # Create API Handler
        handler = Factory.get_handler(
            "api", 
            conf_dict,
            log_file,
            cloud_auth_dict=request_data['cloud_env'],
            cloud_components_list=['keystone'],
            enable_concertim_client=False,
            enable_cloud_client=True,
            enable_billing_client=False
        )

        # Call Function in API Handler
        handler_return = handler.create_user(
            username=request_data['username'],
            password=request_data['password'],
            name=request_data['name'],
            email=request_data['email']
        )
        app.logger.debug(f"Handler Return Data - {handler_return}")

        # Return to Concertim
        resp = {
            'success': True,
            'username': request_data['username'],
            'user_cloud_id': handler_return['user']['id']
        }
        return make_response(resp, 201)
    except Exception as e:
        return handle_exception(e)
    finally:
        app.logger.info(f"Finished - Creating new 'CM_' user in Cloud")
        disconnect_handler(handler)


def delete_user():
    app.logger.info("Starting - Deleting user in Cloud")
    try:
        # Authenticate with JWT
        authenticate(request.headers)

        # Validate Required Data
        request_data = request.get_json()
        app.logger.debug(request_data)
        verify_required_data(request_data, 
            'cloud_env', 
            'user_info', 
            'cloud_user_id')
        
        # Create API Handler
        handler = Factory.get_handler(
            "api", 
            conf_dict,
            log_file,
            cloud_auth_dict=request_data['cloud_env'],
            cloud_components_list=['keystone'],
            enable_concertim_client=False,
            enable_cloud_client=True,
            enable_billing_client=False
        )

        # Call Function in API Handler
        handler_return = handler.delete_user(
            user_cloud_id=request_data['user_info']['cloud_user_id']
        )
        app.logger.debug(f"Handler Return Data - {handler_return}")

        # Return to Concertim
        resp = {
            'success': True
        }
        return make_response(resp, 201)
    except Exception as e:
        return handle_exception(e)
    finally:
        app.logger.info(f"Finished - Deleting user in Cloud")
        disconnect_handler(handler)

def change_user_details():
    app.logger.info("Starting - Updating User details")
    try:
        # Authenticate with JWT
        authenticate(request.headers)

        # Validate Required Data
        request_data = request.get_json()
        app.logger.debug(request_data)
        verify_required_data(request_data, 
            'cloud_env', 
            'user_info', 
            'cloud_user_id', 
            'cloud_default_project_id',
            'default_billing_acct_id',
            'new_data')
        
        # Create API Handler
        handler = Factory.get_handler(
            "api", 
            conf_dict,
            log_file,
            cloud_auth_dict=request_data['cloud_env'],
            cloud_components_list=['keystone'],
            enable_concertim_client=False,
            enable_cloud_client=True,
            enable_billing_client=True
        )

        # Call Function in API Handler
        primary_accts_list = None if 'primary_user_billing_accounts' not in request_data['user_info'] else request_data['user_info']['primary_user_billing_accounts']
        handler_return = handler.change_user_details(
            user_cloud_id=request_data['user_info']['cloud_user_id'],
            proejct_cloud_id=request_data['user_info']['cloud_default_project_id'],
            project_billing_id=request_data['user_info']['default_billing_acct_id'],
            new_data=request_data['new_data'],
            other_project_billing_ids=primary_accts_list
        )
        app.logger.debug(f"Handler Return Data - {handler_return}")

        # Return to Concertim
        resp = {
            'success': True,
            'updated': handler_return['updated_list']
        }
        return make_response(resp, 201)
    except Exception as e:
        return handle_exception(e)
    finally:
        app.logger.info(f"Finished - Updating User details")
        disconnect_handler(handler)

def create_team():
    app.logger.info("Starting - Creating new 'CM_' project in Cloud and corresponding billing account in Billing App")
    try:
        # Authenticate with JWT
        authenticate(request.headers)

        # Validate Required Data
        request_data = request.get_json()
        app.logger.debug(request_data)
        verify_required_data(request_data, 
            'cloud_env', 
            'name')
        
        # Create API Handler
        handler = Factory.get_handler(
            "api", 
            conf_dict,
            log_file,
            cloud_auth_dict=request_data['cloud_env'],
            cloud_components_list=['keystone'],
            enable_concertim_client=False,
            enable_cloud_client=True,
            enable_billing_client=True
        )

        # Call Function in API Handler
        handler_return = handler.create_team(
            name=request_data['name'],
            adjust_name=False
        )
        app.logger.debug(f"Handler Return Data - {handler_return}")

        # Return to Concertim
        resp = {
            'success': True,
            'project_id': handler_return['project']['id'],
            'billing_acct_id': handler_return['billing_acct']['id']
        }
        return make_response(resp, 201)
    except Exception as e:
        return handle_exception(e)
    finally:
        app.logger.info(f"Finished - Creating new team in Cloud and corresponding billing account in Billing App")
        disconnect_handler(handler)

def delete_team():
    app.logger.info("Starting - Deleting team in Cloud and closing billing account")
    try:
        # Authenticate with JWT
        authenticate(request.headers)

        # Validate Required Data
        request_data = request.get_json()
        app.logger.debug(request_data)
        verify_required_data(request_data, 
            'cloud_env', 
            'team_info',
        )
        
        # Create API Handler
        handler = Factory.get_handler(
            "api", 
            conf_dict,
            log_file,
            cloud_auth_dict=request_data['cloud_env'],
            cloud_components_list=['keystone'],
            enable_concertim_client=False,
            enable_cloud_client=True,
            enable_billing_client=True
        )

        # Call Function in API Handler
        handler_return = handler.delete_team(
            project_cloud_id=request_data['team_info']['project_id'],
            billing_id=request_data['team_info']['billing_acct_id']
        )
        app.logger.debug(f"Handler Return Data - {handler_return}")

        # Return to Concertim
        resp = {
            'success': True
        }
        return make_response(resp, 201)
    except Exception as e:
        return handle_exception(e)
    finally:
        app.logger.info(f"Finished - Deleting team in Cloud and closing billing account")
        disconnect_handler(handler)

def create_team_role():
    app.logger.info("Starting - Creating new team role")
    try:
        # Authenticate with JWT
        authenticate(request.headers)

        # Validate Required Data
        request_data = request.get_json()
        app.logger.debug(request_data)
        verify_required_data(request_data,
            'cloud_env',
            'team_role')

        # Create API Handler
        handler = Factory.get_handler(
            "api",
            conf_dict,
            log_file,
            cloud_auth_dict=request_data['cloud_env'],
            cloud_components_list=['keystone'],
            enable_concertim_client=False,
            enable_cloud_client=True,
            enable_billing_client=False
        )

        role_data = request_data['team_role']

        # Call Function in API Handler
        handler_return = handler.create_team_role(
            project_id=role_data['project_id'],
            user_id=role_data['user_id'],
            role=role_data['role']
        )
        app.logger.debug(f"Handler Return Data - {handler_return}")

        # Return to Concertim
        resp = { 'success': True }
        return make_response(resp, 201)
    except Exception as e:
        raise e
        # return handle_exception(e)
    finally:
        app.logger.info(f"Finished - Creating team role")
        disconnect_handler(handler)

def update_team_role():
    app.logger.info("Starting - Updating team role")
    try:
        # Authenticate with JWT
        authenticate(request.headers)

        # Validate Required Data
        request_data = request.get_json()
        app.logger.debug(request_data)
        verify_required_data(request_data,
            'cloud_env',
            'team_role')

        # Create API Handler
        handler = Factory.get_handler(
            "api",
            conf_dict,
            log_file,
            cloud_auth_dict=request_data['cloud_env'],
            cloud_components_list=['keystone'],
            enable_concertim_client=False,
            enable_cloud_client=True,
            enable_billing_client=False
        )

        role_data = request_data['team_role']

        # Call Function in API Handler
        handler_return = handler.update_team_role(
            project_id=role_data['project_id'],
            user_id=role_data['user_id'],
            current_role=role_data['current_role'],
            new_role=role_data['new_role']
        )
        app.logger.debug(f"Handler Return Data - {handler_return}")

        # Return to Concertim
        resp = { 'success': True }
        return make_response(resp, 201)
    except Exception as e:
        raise e
        # return handle_exception(e)
    finally:
        app.logger.info(f"Finished - Creating team role")
        disconnect_handler(handler)

def delete_team_role():
    app.logger.info("Starting - Removing team role")
    try:
        # Authenticate with JWT
        authenticate(request.headers)

        # Validate Required Data
        request_data = request.get_json()
        app.logger.debug(request_data)
        verify_required_data(request_data,
            'cloud_env',
            'team_role')

        # Create API Handler
        handler = Factory.get_handler(
            "api",
            conf_dict,
            log_file,
            cloud_auth_dict=request_data['cloud_env'],
            cloud_components_list=['keystone'],
            enable_concertim_client=False,
            enable_cloud_client=True,
            enable_billing_client=False
        )

        role_data = request_data['team_role']

        # Call Function in API Handler
        handler_return = handler.delete_team_role(
            project_id=role_data['project_id'],
            user_id=role_data['user_id'],
            role=role_data['role']
        )
        app.logger.debug(f"Handler Return Data - {handler_return}")

        # Return to Concertim
        resp = { 'success': True }
        return make_response(resp, 201)
    except Exception as e:
        raise e
        # return handle_exception(e)
    finally:
        app.logger.info(f"Finished - Removing team role")
        disconnect_handler(handler)

def update_status(obj_type, obj_id):
    app.logger.info(f"Starting - Updating status for {obj_type}:{obj_id}")
    try:
        # Authenticate with JWT
        authenticate(request.headers)

        # Validate Required Data
        request_data = request.get_json()
        app.logger.debug(request_data)
        verify_required_data(request_data, 
            'cloud_env', 
            'action')
        
        # Create API Handler
        handler = Factory.get_handler(
            "api", 
            conf_dict,
            log_file,
            cloud_auth_dict=request_data['cloud_env'],
            cloud_components_list=['nova', 'heat'],
            enable_concertim_client=False,
            enable_cloud_client=True,
            enable_billing_client=True
        )

        # Call Function in API Handler
        handler_return = handler.update_status(
            concertim_obj_type=obj_type,
            cloud_obj_id=obj_id,
            action=action
        )
        app.logger.debug(f"Handler Return Data - {handler_return}")

        # Return to Concertim
        resp = {
            'cloud_response': handler_return['message']
        }
        return make_response(resp, handler_return['status_code'])
    except Exception as e:
        return handle_exception(e)
    finally:
        app.logger.info(f"Finished - Updating status for {obj_type}:{obj_id}")
        disconnect_handler(handler)

def key_pair_create():
    app.logger.info("Starting - Creating keypair in Cloud")
    try:
        # Authenticate with JWT
        authenticate(request.headers)

        # Validate Required Data
        request_data = request.get_json()
        app.logger.debug(request_data)
        verify_required_data(request_data, 
            'cloud_env', 
            'key_pair')
        
        # Create API Handler
        handler = Factory.get_handler(
            "api", 
            conf_dict,
            log_file,
            cloud_auth_dict=request_data['cloud_env'],
            cloud_components_list=['nova'],
            enable_concertim_client=False,
            enable_cloud_client=True,
            enable_billing_client=False
        )

        # Call Function in API Handler
        pub_key = None if 'public_key' not in request_data['keypair'] else request_data['keypair']['public_key']
        key_type = 'ssh' if 'key_type' not in request_data['keypair'] else request_data['keypair']['key_type']

        handler_return = handler.create_keypair(
            key_name=request_data['keypair']['name'],
            key_type=key_type,
            imported_public_key=pub_key
        )
        app.logger.debug(f"Handler Return Data - {handler_return}")

        # Return to Concertim
        resp = {
            'success': True,
            'key_pair': handler_return['key_pair']
        }
        return make_response(resp, 201)
    except Exception as e:
        return handle_exception(e)
    finally:
        app.logger.info(f"Finished - Creating keypair in Cloud")
        disconnect_handler(handler)

def key_pair_list():
    app.logger.info("Starting - Listing keypairs")
    try:
        # Authenticate with JWT
        authenticate(request.headers)

        # Validate Required Data
        request_data = request.get_json()
        app.logger.debug(request_data)
        verify_required_data(request_data, 
            'cloud_env')
        
        # Create API Handler
        handler = Factory.get_handler(
            "api", 
            conf_dict,
            log_file,
            cloud_auth_dict=request_data['cloud_env'],
            cloud_components_list=['nova'],
            enable_concertim_client=False,
            enable_cloud_client=True,
            enable_billing_client=False
        )

        # Call Function in API Handler
        handler_return = handler.list_keypairs()
        app.logger.debug(f"Handler Return Data - {handler_return}")

        # Return to Concertim
        resp = {
            'success': True,
            'key_pairs': handler_return['key_pairs']
        }
        return make_response(resp, 201)
    except Exception as e:
        return handle_exception(e)
    finally:
        app.logger.info(f"Finished - Listing keypairs")
        disconnect_handler(handler)

def key_pair_delete():
    app.logger.info("Starting - Deleting keypair")
    try:
        # Authenticate with JWT
        authenticate(request.headers)

        # Validate Required Data
        request_data = request.get_json()
        app.logger.debug(request_data)
        verify_required_data(request_data, 
            'cloud_env', 
            'keypair_id')
        
        # Create API Handler
        handler = Factory.get_handler(
            "api", 
            conf_dict,
            log_file,
            cloud_auth_dict=request_data['cloud_env'],
            cloud_components_list=['nova'],
            enable_concertim_client=False,
            enable_cloud_client=True,
            enable_billing_client=False
        )

        # Call Function in API Handler
        handler_return = handler.delete_keypair(
            key_id=request_data['keypair_name']
        )
        app.logger.debug(f"Handler Return Data - {handler_return}")

        # Return to Concertim
        resp = {
            'success': True,
            'key_pair_name': request_data['keypair_name']
        }
        return make_response(resp, 201)
    except Exception as e:
        return handle_exception(e)
    finally:
        app.logger.info(f"Finished - Deleting keypair")
        disconnect_handler(handler)

def get_draft_invoice():
    app.logger.info("Starting - Getting User's draft invoice")
    try:
        # Authenticate with JWT
        authenticate(request.headers)

        # Validate Required Data
        request_data = request.get_json()
        app.logger.debug(request_data)
        verify_required_data(request_data,
            'billing_acct_id')
        
        # Create API Handler
        handler = Factory.get_handler(
            "api", 
            conf_dict,
            log_file,
            enable_concertim_client=False,
            enable_cloud_client=False,
            enable_billing_client=True
        )

        # Call Function in API Handler
        handler_return = handler.get_draft_invoice(
            project_billing_id=request_data['billing_acct_id']
        )
        app.logger.debug(f"Handler Return Data - {handler_return}")

        # Return to Concertim
        resp = {
            'success': True,
            'draft_invoice': handler_return['invoice']
        }
        return make_response(resp, 201)
    except Exception as e:
        return handle_exception(e)
    finally:
        app.logger.info(f"Finished - Getting User's draft invoice")
        disconnect_handler(handler)

def list_paginated_invoices():
    app.logger.info("Starting - Listing paginated invoices")
    try:
        # Authenticate with JWT
        authenticate(request.headers)

        # Validate Required Data
        request_data = request.get_json()
        app.logger.debug(request_data)
        verify_required_data(request_data,
            'billing_acct_id')
        
        # Create API Handler
        handler = Factory.get_handler(
            "api", 
            conf_dict,
            log_file,
            enable_concertim_client=False,
            enable_cloud_client=False,
            enable_billing_client=True
        )

        # Check for limit and offset - set to default otherwise
        offset = 0 if 'offset' not in request_data else int(request_data['offset'])
        limit = 100 if 'limit' not in request_data else int(request_data['limit'])

        # Call Function in API Handler
        handler_return = handler.list_account_invoice_paginated(
            project_billing_id=request_data['billing_acct_id'],
            offset=offset,
            limit=limit
        )
        app.logger.debug(f"Handler Return Data - {handler_return}")

        # Return to Concertim
        resp = {
            'success': True,
            'total_invoices': handler_return['total_invoices'],
            'invoices': handler_return['invoices']
        }
        return make_response(resp, 201)
    except Exception as e:
        return handle_exception(e)
    finally:
        app.logger.info(f"Finished - Listing paginated invoices")
        disconnect_handler(handler)

def get_account_invoice():
    app.logger.info("Starting - Getting User's invoice by ID")
    try:
        # Authenticate with JWT
        authenticate(request.headers)

        # Validate Required Data
        request_data = request.get_json()
        app.logger.debug(request_data)
        verify_required_data(request_data,
            'billing_acct_id',
            'invoice_id')
        
        # Create API Handler
        handler = Factory.get_handler(
            "api", 
            conf_dict,
            log_file,
            enable_concertim_client=False,
            enable_cloud_client=False,
            enable_billing_client=True
        )

        # Call Function in API Handler
        handler_return = handler.get_invoice_by_id(
            project_billing_id=request_data['billing_acct_id'],
            invoice_id=request_data['invoice_id']
        )
        app.logger.debug(f"Handler Return Data - {handler_return}")

        # Return to Concertim
        resp = {
            'success': True,
            'invoice': handler_return['invoice']
        }
        return make_response(resp, 201)
    except Exception as e:
        return handle_exception(e)
    finally:
        app.logger.info(f"Finished - Getting User's invoice by ID")
        disconnect_handler(handler)

def add_credits():
    app.logger.info("Starting - Adding credits to billing platform for User's Account")
    try:
        # Authenticate with JWT
        authenticate(request.headers)

        # Validate Required Data
        request_data = request.get_json()
        app.logger.debug(request_data)
        verify_required_data(request_data, 'credits')
        
        # Create API Handler
        handler = Factory.get_handler(
            "api", 
            conf_dict,
            log_file,
            enable_concertim_client=False,
            enable_cloud_client=False,
            enable_billing_client=True
        )

        credits_data = request_data['credits']
        # Call Function in API Handler
        handler_return = handler.add_credits(
            project_billing_id=credits_data['billing_acct_id'],
            amount=float(credits_data['amount'])
        )
        app.logger.debug(f"Handler Return Data - {handler_return}")

        # Return to Concertim
        resp = {
            'success': True,
            'credits': handler_return['credits']
        }
        return make_response(resp, 201)
    except Exception as e:
        raise e
        #return handle_exception(e)
    finally:
        app.logger.info(f"Finished - Adding credits to billing platform for User's Account")
        disconnect_handler(handler)

def get_credits():
    app.logger.info("Starting - Getting Credits for Account")
    try:
        # Authenticate with JWT
        authenticate(request.headers)

        # Validate Required Data
        request_data = request.get_json()
        app.logger.debug(request_data)
        verify_required_data(request_data, 
            'billing_acct_id')
        
        # Create API Handler
        handler = Factory.get_handler(
            "api", 
            conf_dict,
            log_file,
            enable_concertim_client=False,
            enable_cloud_client=False,
            enable_billing_client=True
        )

        # Call Function in API Handler
        handler_return = handler.get_credits(
            billing_acct_id=request_data['billing_acct_id']
        )
        app.logger.debug(f"Handler Return Data - {handler_return}")

        # Return to Concertim
        resp = {
            'success': True,
            'credits': handler_return['credits']
        }
        return make_response(resp, 201)
    except Exception as e:
        return handle_exception(e)
    finally:
        app.logger.info(f"Finished - Getting Credits for Account")
        disconnect_handler(handler)

def create_order():
    app.logger.info("Starting - Creating Order")
    try:
        # Authenticate with JWT
        authenticate(request.headers)

        # Validate Required Data
        request_data = request.get_json()
        app.logger.debug(request_data)
        verify_required_data(request_data, 
            'billing_acct_id')
        
        # Create API Handler
        handler = Factory.get_handler(
            "api", 
            conf_dict,
            log_file,
            enable_concertim_client=False,
            enable_cloud_client=False,
            enable_billing_client=True
        )

        # Call Function in API Handler
        handler_return = handler.create_order(
            project_billing_id=request_data['billing_acct_id']
        )
        app.logger.debug(f"Handler Return Data - {handler_return}")

        # Return to Concertim
        resp = {
            'success': True,
            'order_id': handler_return['order_id'],
            'order': handler_return['order']
        }
        return make_response(resp, 201)
    except Exception as e:
        return handle_exception(e)
    finally:
        app.logger.info(f"Finished - Creating Order")
        disconnect_handler(handler)

def add_order_tag():
    app.logger.info("Starting - Adding tag to Order")
    try:
        # Authenticate with JWT
        authenticate(request.headers)

        # Validate Required Data
        request_data = request.get_json()
        app.logger.debug(request_data)
        verify_required_data(request_data, 
            'order_id',
            'tag_name',
            'tag_value')
        
        # Create API Handler
        handler = Factory.get_handler(
            "api", 
            conf_dict,
            log_file,
            enable_concertim_client=False,
            enable_cloud_client=False,
            enable_billing_client=True
        )

        # Call Function in API Handler
        handler_return = handler.add_order_tag(
            cluster_billing_id=request_data['order_id'],
            tag_name=request_data['tag_name'],
            tag_value=request_data['tag_value']
        )
        app.logger.debug(f"Handler Return Data - {handler_return}")

        # Return to Concertim
        resp = {
            'success': True,
            'tag': handler_return['tag']
        }
        return make_response(resp, 201)
    except Exception as e:
        return handle_exception(e)
    finally:
        app.logger.info(f"Finished - Adding tag to Order")
        disconnect_handler(handler)
    

### HELPERS
def handle_exception(e):
    app.logger.debug(f"Handling Exception: {e}")
    type_name = type(e).__name__
    response = {"success": False, "error": type_name, "message": str(e), "traceback" : traceback.format_exc()}

    if 'http_status' in dir(e) and e.http_status:
        code = e.http_status
    elif type_name == "APIServerDefError":
        code = 400
    else:
        code = 500
    
    return jsonify(response), code

def authenticate(headers):
    if not authenticate_headers(headers, app.logger):
        raise APIAuthenticationError(headers)
    else:
        app.logger.debug("Request Authenticated")
        return True

def verify_required_data(req_json, *args):
    def find_key(d, key):
        # Check if key is in the current dictionary
        if key in d:
            return True
        # If not, iterate through the dictionary to find nested dictionaries and search within them
        for k, v in d.items():
            if isinstance(v, dict) and find_key(v, key):
                return True
        return False
    # Get list of missing keys
    missing_keys = [key for key in args if not find_key(req_json, key)]
    # Raise exception if there are missing keys
    if missing_keys:
        raise EXCP.MissingRequiredArgument(missing_keys)
    else:
        app.logger.debug("All required fields present")
        return True

def disconnect_handler(handler):
    app.logger.debug("Disconnecting Handler")
    try:
        handler.disconnect()
        handler = None
    except (NameError, AttributeError):
        handler = None
    return

"""
----------- ROUTES -----------

Functions are below the Routes section

"""
#### USERS
app.add_url_rule('/user', endpoint='create_user',
                                view_func=create_user,
                                methods=['POST'])

app.add_url_rule('/user', endpoint='delete_user',
                                view_func=delete_user,
                                methods=['DELETE'])

app.add_url_rule('/user', endpoint='change_user_details',
                                view_func=change_user_details,
                                methods=['PATCH'])

#### TEAMS
app.add_url_rule('/team', endpoint='create_team',
                                view_func=create_team,
                                methods=['POST'])

app.add_url_rule('/team', endpoint='delete_team',
                                view_func=delete_team,
                                methods=['DELETE'])

#### TEAM ROLES
app.add_url_rule('/team_role', endpoint='create_team_role',
                                view_func=create_team_role,
                                methods=['POST'])

app.add_url_rule('/team_role', endpoint='update_team_role',
                                view_func=update_team_role,
                                methods=['PATCH'])

app.add_url_rule('/team_role', endpoint='delete_team_role',
                                view_func=delete_team_role,
                                methods=['DELETE'])

#### DEVICES/RACKS
app.add_url_rule('/update_status/<obj_type>/<obj_id>', endpoint='update_status',
                                view_func=update_status,
                                methods=['POST'])

#### KEY PAIRS
app.add_url_rule('/key_pairs', endpoint='key_pair_create',
                                view_func=key_pair_create,
                                methods=['POST'])

app.add_url_rule('/key_pairs', endpoint='key_pair_list',
                                view_func=key_pair_list,
                                methods=['GET'])

app.add_url_rule('/key_pairs', endpoint='key_pair_delete',
                                view_func=key_pair_delete,
                                methods=['DELETE'])

#### INVOICES
app.add_url_rule('/get_draft_invoice', endpoint='get_draft_invoice',
                                view_func=get_draft_invoice,
                                methods=['POST'])

app.add_url_rule('/list_paginated_invoices', endpoint='list_paginated_invoices',
                                view_func=list_paginated_invoices,
                                methods=['POST'])

app.add_url_rule('/get_account_invoice', endpoint='get_account_invoice',
                                view_func=get_account_invoice,
                                methods=['POST'])

#### CREDITS
app.add_url_rule('/credits', endpoint='add_credits',
                                view_func=add_credits,
                                methods=['POST'])

app.add_url_rule('/credits', endpoint='get_credits',
                                view_func=get_credits,
                                methods=['GET'])

#### BILLING ORDERS
app.add_url_rule('/create_order', endpoint='create_order',
                                view_func=create_order,
                                methods=['POST'])

app.add_url_rule('/add_order_tag', endpoint='add_order_tag',
                                view_func=add_order_tag,
                                methods=['POST'])
                
### RUNNER
def run_api(config_obj, log_f):
    global conf_dict
    conf_dict = config_obj
    global log_file
    log_file = log_f

    # Logging setup
    formatter = SensitiveFormatter('[%(asctime)s] - %(levelname)-8s: %(module)-12s: %(funcName)-26s===>  %(message)s')
    fh = logging.FileHandler(log_file)
    fh.setFormatter(formatter)
    app.logger.addHandler(fh)
    app.logger.setLevel(conf_dict['log_level'])

    app.logger.info("========== STARTING API SERVER ==========")
    app.run(host='0.0.0.0', port=42356)


