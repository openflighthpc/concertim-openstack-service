# Local Imports
from con_opstk.utils.service_logger import create_logger
from con_opstk.data_handler.base import BaseHandler
from con_opstk.openstack.exceptions import APIServerDefError
# Py Packages
import sys
from novaclient.exceptions import ClientException as nova_ex
from heatclient.exc import BaseException as heat_ex


class APIHandler(BaseHandler):
    DEFAULT_CLIENTS = ['keystone']
    def __init__(self, config_obj, log_file, enable_concertim=False, clients=None, billing_enabled=False):
        self.clients = clients if clients else APIHandler.DEFAULT_CLIENTS
        self.billing_enabled = billing_enabled
        super().__init__(config_obj, log_file, self.clients, enable_concertim=enable_concertim, billing_enabled=billing_enabled)
        self.__LOGGER = create_logger(__name__, self._LOG_FILE, self._CONFIG['log_level'])

    def create_user(self, username, password, email):
        children = []
        opsk_username = f"CM_{username}"
        try:
            # Create new user
            self.__LOGGER.info(f"Creating User for {username}")
            if 'user_domain_name' in self._CONFIG['openstack']:
                new_user = self.openstack_service.create_new_cm_user(opsk_username, password, email, domain=self._CONFIG['openstack']['user_domain_name'])
            else:
                new_user = self.openstack_service.create_new_cm_user(opsk_username, password, email)
            children.append(new_user)
            return new_user
        except Exception as e:
            self.__LOGGER.error(f"Encountered ERROR - Aborting")
            super().__scrub(*children) # what's this for/ doing?
            self.__LOGGER.error(f"Encountered error when creating new Concertim Managed User {type(e).__name__} - {e} - {sys.exc_info()[2].tb_frame.f_code.co_filename} - {sys.exc_info()[2].tb_lineno}")
            raise e


    def create_team_project(self, name):
        children = []
        formatted_name = name.replace(' ', '_')
        opsk_project_name = f"CM_{formatted_name}_proj"
        try:
            self.__LOGGER.info(f"Creating Project for team {name}")
            # Create new project
            if 'project_domain_name' in self._CONFIG['openstack']:
                new_project = self.openstack_service.create_new_cm_project(opsk_project_name,domain=self._CONFIG['openstack']['project_domain_name'])
            else:
                new_project = self.openstack_service.create_new_cm_project(opsk_project_name)
            children.append(new_project)
            # Create billing account
            self.__LOGGER.info(f"Creating Billling Account for team {name}")
            response = self.billing_service.create_new_account(name=formatted_name, openstack_project_id=new_project.id)
            location_header = response['headers']['Location']
            new_billing_acct_id = location_header.split('/')[-1]

            return new_project, new_billing_acct_id
        except Exception as e:
            self.__LOGGER.error(f"Encountered ERROR - Aborting")
            super().__scrub(*children)
            self.__LOGGER.error(f"Encountered error when creating new Concertim Project/Billing {type(e).__name__} - {e} - {sys.exc_info()[2].tb_frame.f_code.co_filename} - {sys.exc_info()[2].tb_lineno}")
            raise e

    def delete_team(self, openstack_project_id, billing_acct_id):
        self.__LOGGER.info(f"Starting delete of Concertim Team objects")
        try:
            self.openstack_service.delete_project(openstack_project_id)
            self.billing_service.close_account(billing_acct_id)
            return True
        except Exception as e:
            self.__LOGGER.error(f"Encountered error when completing Team objects deletion : {e.__class__.__name__} - {e} - {sys.exc_info()[2].tb_frame.f_code.co_filename} - {sys.exc_info()[2].tb_lineno}")
            raise e


    def create_team_role(self, user_id, project_id, role):
        self.__LOGGER.info(f"Creating role #{role} for user #{user_id} in project #{project_id}")
        try:
            self.openstack_service.add_user_to_project(user_id, project_id, role)
        except Exception as e:
            self.__LOGGER.error(f"Encountered error when adding user {user_id} to project {project_id} : {e.__class__.__name__} - {e} - {sys.exc_info()[2].tb_frame.f_code.co_filename} - {sys.exc_info()[2].tb_lineno}")
            raise e

    def update_status(self, type, id, action):
        self.__LOGGER.info(f"Starting action {action} for {type} {id}")
        try:
            result = None
            if type == "devices":
                result = self.openstack_service.update_instance_status(id, action)
            elif type == "racks":
                result = self.openstack_service.update_stack_status(id, action)
            
            # Check if update function returned a client exception (will only happen if forbidden/unauth)
            if isinstance(result, nova_ex) or isinstance(result, heat_ex):
                return (403, "Could not complete action due to credentials provided")
            return result
        except Exception as e:
            self.__LOGGER.error(f"Encountered error when completing action [action:{action},type:{type},id:{id}] : {e.__class__.__name__} - {e} - {sys.exc_info()[2].tb_frame.f_code.co_filename} - {sys.exc_info()[2].tb_lineno}")
            raise e

    def get_latest_invoice(self, billing_account_id):
        self.__LOGGER.info(f"Getting latest invoice for {billing_account_id}")
        result = self.billing_service.get_latest_invoice(billing_account_id)
        return result
       
    def get_draft_invoice(self, billing_account_id):
        self.__LOGGER.info(f"Getting draft invoice for {billing_account_id}")
        result = self.billing_service.get_draft_invoice(billing_account_id)
        return result
    
    def add_credits(self, billing_account_id, credits_to_add):
        self.__LOGGER.info(f"Adding credits to {billing_account_id}")
        result = self.billing_service.add_credits(billing_account_id, credits_to_add)
        return result
    
    def get_credits(self, billing_account_id):
        self.__LOGGER.info(f"Getting credits for {billing_account_id}")
        result = self.billing_service.get_credits(billing_account_id)
        return result
    
    def create_order(self, billing_account_id):
        self.__LOGGER.info(f"Creating Order for {billing_account_id}")
        result = self.billing_service.create_order(billing_account_id)
        return result
    
    def list_account_invoice_paginated(self, billing_account_id, offset, limit):
        self.__LOGGER.info(f"Listing paginated invoices for {billing_account_id}")
        result = self.billing_service.list_account_invoice_paginated(account_id=billing_account_id, offset=offset, limit=limit)
        return result
    
    def get_invoice_by_id(self, invoice_id):
        self.__LOGGER.info(f"Getting invoice for id {invoice_id}")
        result = self.billing_service.get_invoice_by_id(invoice_id)

        self.read_view()

        for subscription_id in result['data']['items']:

            for tup in self.view.racks:
                rack = self.view.racks[tup]
                self.__LOGGER.info(f"{rack}")

                # Checking for matching of Openstack stack id
                if rack.id[1] != result['data']['items'][subscription_id]['openstack_stack_id']:
                    continue

                result['data']['items'][subscription_id]['openstack_stack_name'] = rack.openstack_name

        return result

    def add_order_tag(self, order_id, tag_name, tag_value):
        self.__LOGGER.info(f"Creating tag for order_id {order_id} - {tag_name} : {tag_value}")
        result = self.billing_service.add_order_tag(order_id, tag_name, tag_value)
        return result
    

    def create_keypair(self, name, key_type='ssh', imported_pub_key=None):
        self.__LOGGER.info(f"Starting creation of {key_type} key pair {name}")
        try:
            result = self.openstack_service.create_keypair(name, imported_pub_key=imported_pub_key, key_type=key_type)
            # Return the keypair information as a dict, not the <KeyPair> object
            return result._info
        except Exception as e:
            self.__LOGGER.error(f"Encountered error when completing key pair creation : {e.__class__.__name__} - {e} - {sys.exc_info()[2].tb_frame.f_code.co_filename} - {sys.exc_info()[2].tb_lineno}")
            raise e

    def list_keypairs(self):
        self.__LOGGER.info(f"Starting listing of keypairs")
        try:
            result = self.openstack_service.list_keypairs()
            # Return the keypair information as a dict, not the <KeyPair> object
            return [kp._info for kp in result if hasattr(kp,'_info')]
        except Exception as e:
            self.__LOGGER.error(f"Encountered error when trying to list key pairs : {e.__class__.__name__} - {e} - {sys.exc_info()[2].tb_frame.f_code.co_filename} - {sys.exc_info()[2].tb_lineno}")
            raise e

    def delete_keypair(self, name):
        self.__LOGGER.info(f"Starting deletion of key pair {name}")
        try:
            result = self.openstack_service.delete_keypair(name)
            return result
        except Exception as e:
            self.__LOGGER.error(f"Encountered error when completing key pair deletion : {e.__class__.__name__} - {e} - {sys.exc_info()[2].tb_frame.f_code.co_filename} - {sys.exc_info()[2].tb_lineno}")
            raise e

    def change_user_details(self, openstack_user_id, billing_acct_id, new_data):
        self.__LOGGER.info(f"Updating details for User '{openstack_user_id}'")
        changed = []
        try:
            for field in new_data.keys():
                if field == 'password':
                    self.openstack_service.change_user_details(openstack_user_id, new_password=new_data['password'])
                    changed.append("password")
                if field == 'email':
                    self.openstack_service.change_user_details(openstack_user_id, new_email=new_data['email'])
                    self.billing_service.change_account_email(billing_acct_id, new_data['email'])
                    changed.append("email")
            return changed
        except Exception as e:
            self.__LOGGER.error(f"Encountered error when updating User info : {e.__class__.__name__} - {e} - {sys.exc_info()[2].tb_frame.f_code.co_filename} - {sys.exc_info()[2].tb_lineno}")
            raise e

    def delete_user(self, openstack_user_id, openstack_project_id, billing_acct_id):
        self.__LOGGER.info(f"Starting delete of Concertim User objects")
        try:
            self.openstack_service.delete_cm_pair(openstack_user_id, openstack_project_id)
            self.billing_service.close_account(billing_acct_id)
            return True
        except Exception as e:
            self.__LOGGER.error(f"Encountered error when completing User objects deletion : {e.__class__.__name__} - {e} - {sys.exc_info()[2].tb_frame.f_code.co_filename} - {sys.exc_info()[2].tb_lineno}")
            raise e


    
