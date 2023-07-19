# Local Imports
from utils.service_logger import create_logger
# endpoints file containing info on all concertim endpoints
from concertim.components.endpoints import ENDPOINTS

# Py Packages
import json
# Disable insecure warnings  
import requests
requests.packages.urllib3.disable_warnings() 

class ConcertimService(object):
    def __init__(self, config_obj, log_file):
        self.__CONFIG = config_obj
        self.__LOGGER = create_logger(__name__, log_file, self.__CONFIG['log_level'])
        self.__URL = self.__CONFIG['concertim']['concertim_url']
        self.__AUTH_TOKEN = self.__get_auth_token()
    
    def __get_auth_token(self):
        login = self.__CONFIG['concertim']['concertim_username']
        password = self.__CONFIG['concertim']['concertim_password']
        variables_dict = {'login': login, 'password': password}
        token = self.__api_call('post', 'LOGIN_AUTH', variables_dict)
        return token
    
    # Return a dict of available endpoints and the call/data needed
    def list_available_endpoints(self):
        return ENDPOINTS

    def create_device(self, variables_dict):
        response = self.__api_call('post', 'CREATE_DEVICE', variables_dict=variables_dict)
        return response
    
    def create_rack(self, variables_dict):
        self.__LOGGER.debug(f"{variables_dict}")
        response = self.__api_call('post', 'CREATE_RACK', variables_dict=variables_dict)
        return response
    
    def create_template(self, variables_dict):
        response = self.__api_call('post', 'CREATE_TEMPLATE', variables_dict=variables_dict)
        return response

    def delete_device(self, ID):
        response = self.__api_call('delete', 'DELETE_DEVICE', endpoint_var=str(ID))
        return True
    
    def delete_rack(self, ID, recurse=False):
        opts = str(ID)
        if recurse:
            opts += ENDPOINTS['DELETE']['recurse']
        response = self.__api_call('delete', 'DELETE_RACK', endpoint_var=opts)
        return True

    def delete_template(self, ID, recurse=False):
        opts = str(ID)
        if recurse:
            opts += ENDPOINTS['DELETE']['recurse']
        response = self.__api_call('delete', 'DELETE_TEMPLATE', endpoint_var=opts)
        return True

    def list_devices(self):
        response = self.__api_call('get', 'LIST_DEVICES')
        return response

    def list_racks(self):
        response = self.__api_call('get', 'LIST_RACKS')
        return response

    def list_templates(self):
        response = self.__api_call('get', 'LIST_TEMPLATES')
        return response

    def list_users(self):
        response = self.__api_call('get', 'LIST_USERS')
        return response
    
    def show_device(self, ID):
        response = self.__api_call('get', 'SHOW_DEVICE', endpoint_var=str(ID))
        return response

    def show_rack(self, ID):
        response = self.__api_call('get', 'SHOW_RACK', endpoint_var=str(ID))
        return response

    def move_device(self, ID, variables_dict):
        response = self.__api_call('patch', 'MOVE_DEVICE', variables_dict=variables_dict, endpoint_var=str(ID))
        return response

    def update_device(self, ID, variables_dict):
        response = self.__api_call('patch', 'UPDATE_DEVICE', variables_dict=variables_dict, endpoint_var=str(ID))
        return response

    def update_rack(self, ID, variables_dict):
        response = self.__api_call('patch', 'UPDATE_RACK', variables_dict=variables_dict, endpoint_var=str(ID))
        return response

    def update_template(self, ID, variables_dict):
        response = self.__api_call('patch', 'UPDATE_TEMPLATE', variables_dict=variables_dict, endpoint_var=str(ID))
        return response

    def send_metric(self, ID, variables_dict):
        try:
            response = self.__api_call('put', 'METRIC', variables_dict=variables_dict, endpoint_var=str(ID))
            return response
        except ValueError as e:
            self.__LOGGER.error(f"{e}")
            self.__LOGGER.warning(f"FAILED - Could not send metric for {variables_dict['name']}")
            raise e

    # Generic method for handling Concertim API calls.
    def __api_call(self, method, endpoint_name, variables_dict={}, endpoint_var=''):
        """
        Generic method for handling Concertim API calls.
        ACCEPTS:
            method - the REST call to make (get,post,patch,etc)
            endpoint_name - the endpoint name correspoinding to the ENDPOINTS dictionary
                            (CREATE_DEVICE, DELETE_DEVICE, UPDATE_DEVICE, etc)
            *variables_dict - the dictionary containing all needed variables to make the API call
            *endpoint_var - this is the ID or NAME of a device/template/rack that needs to be filled in the URL string
        
        Will return the JSON response, or raise an exception based on the status code
        NOTE: if sending LOGIN_AUTH for the endpoint, it will not add the Authorization to the header
              and will return the auth token instead of the response.json()
        """
        endpoint = ENDPOINTS[method.upper()]['endpoints'][endpoint_name]
        headers = ENDPOINTS[method.upper()]['headers']
        # Handle endpoint formatting
        if endpoint_var:
            url = self.__URL + endpoint['endpoint'].format(endpoint_var)
        else:
            url = self.__URL + endpoint['endpoint']

        # Handle if it is LOGIN_AUTH
        if endpoint_name != 'LOGIN_AUTH' and self.__AUTH_TOKEN is not None:
            headers["Authorization"] = self.__AUTH_TOKEN
        elif endpoint_name == 'LOGIN_AUTH':
            self.__LOGGER.debug("Getting Concertim Auth Token")
        elif self.__AUTH_TOKEN is None:
            e = Exception("No Authentication Token provided")
            self.__LOGGER.exception(str(e))
            raise e

        # Handle if there is a 'data' dump needed
        if variables_dict:
            self.__check_required_vars(variables_dict, endpoint)
            data_dict = self.__get_data(variables_dict, endpoint['data'])
            data = json.dumps(data_dict)

            # Don't log user/pass in plain text
            if endpoint_name == 'LOGIN_AUTH':
                self.__LOGGER.debug(f"API CALL ({method}) - {url}")
            else:
                self.__LOGGER.debug(f"API CALL ({method}) - {url} : data [{data}]")

            response = getattr(requests, method.lower())(url, headers=headers, data=data, verify=False)
        else:
            self.__LOGGER.debug(f"API CALL ({method}) - {url}")
            response = getattr(requests, method.lower())(url, headers=headers, verify=False)

        # Handle response status codes
        if response.status_code in [200, 201]:
            # Send the token if it is the login endpoint, else return the response.json
            if endpoint_name == 'LOGIN_AUTH':
                return response.headers.get("Authorization")
            return response.json()
        elif response.status_code == 400:
            e = ValueError(f"Bad request, please check your data: {response.json()}")
            self.__LOGGER.exception(str(e))
            raise e
        elif response.status_code == 401:
            e = ValueError(f"Unauthorized, please check your credentials: {response.json()}")
            self.__LOGGER.exception(str(e))
            raise e
        elif response.status_code == 404:
            e = ValueError(f"No path found, please check your endpoint: {response.json()}")
            self.__LOGGER.exception(str(e))
            raise e
        elif response.status_code == 500:
            e = ValueError(f"Server error, please check the Concertim host server or try again later: {response.json()}")
            self.__LOGGER.exception(str(e))
            raise e
        elif response.status_code == 422:
            e = FileExistsError(f"Cannot process: {response.json()}")
            self.__LOGGER.warning("The item you are trying to add already exists")
            raise e
        else:
            self.__LOGGER.exception('Unhandled REST request error.')
            response.raise_for_status()

    # Return the given data template from ENDPOINTS with all var filled in from variables_dict
    # Uses recursion to traverse through the dict
    def __get_data(self, variables_dict, template):
        data_dict = {}
        casting = {'value': float, 'ttl': int}
        for key, value in template.items():
            if isinstance(value, dict):
                data_dict[key] = self.__get_data(variables_dict, value)
            else:
                if key in casting:
                    data_dict[key] = casting[key](value.format(**variables_dict))
                else:
                    data_dict[key] = value.format(**variables_dict)
        return data_dict

    # Return Ture if all necessary vars are present, otherwise raise an err
    def __check_required_vars(self, variables_dict, endpoint):
        missing_vars = [var for var in endpoint['required_vars'] if var not in variables_dict]
        if missing_vars:
            e = ValueError(f'Missing required variables: {", ".join(missing_vars)}')
            self.__LOGGER.error(str(e))
            raise e
        return True

    def disconnect(self):
        self.__LOGGER.info("Disconnecting Concertim Services")
        return


class ConcertimData:
    def __init__(self):
        self.racks = {}
        self.devices = {}
        self.users = {}
        self.templates = {}

    def __repr__(self):
        return f"{self.racks.__repr__()} \n \
            {self.devices.__repr__()} \n \
            {self.users.__repr__()} \n  \
            {self.templates.__repr__()} \n"

class OpenstackConcertimMap:
    def __init__(self):
        self.stack_to_rack = {}
        self.instance_to_device = {}
        self.flavor_to_template = {}
        self.os_user_to_concertim_user = {}
        self.os_project_to_concertim_user = {}