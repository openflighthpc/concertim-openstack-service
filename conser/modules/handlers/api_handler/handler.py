# Local Imports
from conser.utils.service_logger import create_logger
from conser.factory.abs_classes.handlers import Handler
import conser.exceptions as EXCP

class APIHandler(Handler):
    ############
    # DEFAULTS #
    ############
    ACTIONS_MAP = {
        'devices': {
            'function': 'update_server_status',
            'actions': ['on', 'off', 'suspend', 'resume', 'destroy']
        },
        'racks': {
            'function': 'update_cluster_status',
            'actions': ['suspend', 'resume', 'destroy']
        }
    }

    ########
    # INIT #
    ########
    def __init__(self, clients_dict, log_file, log_level):
        self._LOG_LEVEL = log_level
        self._LOG_FILE = log_file
        self.__LOGGER = create_logger(__name__, self._LOG_FILE, self._LOG_LEVEL)
        self.clients = clients_dict

    #########################
    # API HANDLER FUNCTIONS #
    #########################
    def create_user(self, username, password, name, email):
        # EXIT CASES
        if 'cloud' not in self.clients or not self.clients['cloud']:
            raise EXCP.MissingRequiredClient('cloud')
        if 'billing' not in self.clients or not self.clients['billing']:
            raise EXCP.MissingRequiredClient('billing')

        # OBJECT LOGIC
        children = []
        try:
            #-- Create cloud user
            self.__LOGGER.debug(f"Creating new Concertim Managed User in Cloud")
            new_user = self.clients['cloud'].create_cm_user(
                username='CM_' + username,
                password=password,
                email=email
            )
            children.append(('cloud', 'user', new_user['id']))
            #-- Create cloud project
            self.__LOGGER.debug(f"Creating new default project for User -> {new_user['id']}")
            new_project = self.clients['cloud'].create_cm_project(
                name='CM_' + username,
                primary_user_cloud_id=new_user['id']
            )
            children.append(('cloud', 'project', new_project['id']))
            #-- Create billing account for default project
            self.__LOGGER.debug(f"Creating new billing account for User's default project -> {new_project['id']}")
            new_billing_acct = self.clients['billing'].create_account(
                project_cloud_name='CM_' + username,
                project_cloud_id=new_project['id'],
                primary_user_email=email
            )
            children.append(('billing', 'account', new_billing_acct['id']))
        except Exception as e:
            self.__LOGGER.error("Create FAILED - scrubbing orphaned objects")
            self._scrub_orphans(children)
            raise e

        # BUILD RETURN DICT
        self.__LOGGER.debug(f"Building Return dictionary")
        return_dict = {
            'user':{
                'id': new_user['id']
            },
            'project': {
                'id': new_project['id']
            }
            'billing_acct':{
                'id': new_billing_acct['id']
            }
        }
        # RETURN
        return return_dict

    def delete_user(self, user_cloud_id, project_cloud_id, project_billing_id):
        self.__LOGGER.debug(f"Deleting User, their default project, and their default project's billing account")
        # EXIT CASES
        if 'cloud' not in self.clients or not self.clients['cloud']:
            raise EXCP.MissingRequiredClient('cloud')
        if 'billing' not in self.clients or not self.clients['billing']:
            raise EXCP.MissingRequiredClient('billing')
        
        # OBJECT LOGIC
        failed = []
        #-- Delete billing acct
        try:
            self.clients['billing'].delete_account(project_billing_id)
        except Exception as e:
            failed.append(('billing_acct', e))
        #-- Delete Cloud project
        try:
            self.clients['cloud'].delete_project(project_cloud_id)
        except Exception as e:
            failed.append(('project', e))
        #-- Delete Cloud user
        try:
            self.clients['cloud'].delete_user(user_cloud_id)
        except Exception as e:
            failed.append(('user', e))

        #-- Handle failures
        if failed:
            raise Exception(f"Failed to delete some objects -> {failed}")

        # BUILD RETURN DICT
        self.__LOGGER.debug(f"Building Return dictionary")
        return_dict = {
            'success': True
        }
        # RETURN
        return return_dict

    def change_user_details(self, user_cloud_id, project_cloud_id, project_billing_id, new_data, other_project_billing_ids=None):
        self.__LOGGER.debug(f"Changing info for User -> {user_cloud_id}")
        # EXIT CASES
        if 'cloud' not in self.clients or not self.clients['cloud']:
            raise EXCP.MissingRequiredClient('cloud')
        if 'billing' not in self.clients or not self.clients['billing']:
            raise EXCP.MissingRequiredClient('billing')

        # OBJECT LOGIC
        new_email = None if 'email' not in new_data else new_data['email']
        new_pw = None if 'password' not in new_data else new_data['password']
        updated = []
        #-- Change user details in cloud
        user_update = self.clients['cloud'].update_user_info(
            user_cloud_id=user_cloud_id, 
            new_email=new_email,
            new_password=new_pw
        )
        for field in user_update['changed']:
            updated.append(('cloud_user', user_cloud_id, field))

        #-- Change details in billing app
        if new_email:
            self.clients['billing'].update_account_billing_info(
                project_billing_id=project_billing_id,
                new_email=new_email
            )
            updated.append(('billing_acct', project_billing_id , 'email'))
            for proj_bill_id in other_project_billing_ids:
                self.clients['billing'].update_account_billing_info(
                    project_billing_id=proj_bill_id,
                    new_email=new_email
                )
                updated.append(('billing_acct', proj_bill_id , 'email'))

        # BUILD RETURN DICT
        self.__LOGGER.debug(f"Building Return dictionary")
        return_dict = {
            'updated_list': updated
        }
        # RETURN
        return return_dict

    def create_project(self, name, primary_user_cloud_id, primary_user_email):
        self.__LOGGER.debug(f"")
        # EXIT CASES
        if 'cloud' not in self.clients or not self.clients['cloud']:
            raise EXCP.MissingRequiredClient('cloud')
        if 'billing' not in self.clients or not self.clients['billing']:
            raise EXCP.MissingRequiredClient('billing')

        # OBJECT LOGIC
        try:
            #-- Create cloud project
            self.__LOGGER.debug(f"Creating new project -> {name}")
            new_project = self.clients['cloud'].create_cm_project(
                name='CM_' + name,
                primary_user_cloud_id=primary_user_cloud_id
            )
            children.append(('cloud', 'project', new_project['id']))
            #-- Create billing account for default project
            self.__LOGGER.debug(f"Creating new billing account for project -> {name}")
            new_billing_acct = self.clients['billing'].create_account(
                project_cloud_name='CM_' + name,
                project_cloud_id=new_project['id'],
                primary_user_email=primary_user_email
            )
            children.append(('billing', 'account', new_billing_acct['id']))
        except Exception as e:
            self.__LOGGER.error("Create FAILED - scrubbing orphaned objects")
            self._scrub_orphans(children)
            raise e

        # BUILD RETURN DICT
        self.__LOGGER.debug(f"Building Return dictionary")
        return_dict = {
            'project': {
                'id': new_project['id']
            },
            'billing_acct':{
                'id': new_billing_acct['id']
            }
        }
        # RETURN
        return return_dict

    def delete_project(self, project_cloud_id, project_billing_id):
        self.__LOGGER.debug(f"Deleting project and project's billing account")
        # EXIT CASES
        if 'cloud' not in self.clients or not self.clients['cloud']:
            raise EXCP.MissingRequiredClient('cloud')
        if 'billing' not in self.clients or not self.clients['billing']:
            raise EXCP.MissingRequiredClient('billing')
        
        # OBJECT LOGIC
        failed = []
        #-- Delete billing acct
        try:
            self.clients['billing'].delete_account(project_billing_id)
        except Exception as e:
            failed.append(('billing_acct', e))
        #-- Delete Cloud project
        try:
            self.clients['cloud'].delete_project(project_cloud_id)
        except Exception as e:
            failed.append(('project', e))

        #-- Handle failures
        if failed:
            raise Exception(f"Failed to delete some objects -> {failed}")

        # BUILD RETURN DICT
        self.__LOGGER.debug(f"Building Return dictionary")
        return_dict = {
            'success': True
        }
        # RETURN
        return return_dict

    def update_status(self, concertim_obj_type, cloud_obj_id, action):
        self.__LOGGER.debug(f"Updating status for {concertim_obj_type}.{cloud_obj_id} to {action}")
        # EXIT CASES
        if 'cloud' not in self.clients or not self.clients['cloud']:
            raise EXCP.MissingRequiredClient('cloud')
        if 'billing' not in self.clients or not self.clients['billing']:
            raise EXCP.MissingRequiredClient('billing')
        if concertim_obj_type not in APIHandler.ACTIONS_MAP:
            raise InvalidAPICall(concertim_obj_type)
        if action not in APIHandler.ACTIONS_MAP[concertim_obj_type]['actions']:
            raise InvalidAPICall(f"{concertim_obj_type}.{action}")
        
        # OBJECT LOGIC
        #-- Update status
        attempt = getattr(self.clients['cloud'], APIHandler.ACTIONS_MAP[concertim_obj_type]['function'])(
            cloud_obj_id,
            action
        )
        #-- Update billing if needed
        if concertim_obj_type == 'racks' and action == 'destroy':
            cluster_delete = self.clients['billing'].delete_cluster_order(
                cluster_billing_id=cloud_obj_id
            )
        
        # BUILD RETURN DICT
        self.__LOGGER.debug(f"Building Return dictionary")
        return_dict = {
            'message': attempt
        }
        # RETURN
        return return_dict

    def create_keypair(self, key_name, key_type='ssh', imported_public_key=None):
        self.__LOGGER.debug(f"Creating keypair {key_name}")
        # EXIT CASES
        if 'cloud' not in self.clients or not self.clients['cloud']:
            raise EXCP.MissingRequiredClient('cloud')

        # OBJECT LOGIC
        keypair = self.clients['cloud'].create_keypair(
            name=key_name, 
            imported_pub_key=imported_public_key, 
            key_type=key_type
        )
        # BUILD RETURN DICT
        self.__LOGGER.debug(f"Building Return dictionary")
        return_dict = {
            'key_pair': {
                'id': keypair['id']
                'name': keypair['name'],
                'private_key': keypair['private_key'],
                'public_key': keypair['public_key']
            }
        }
        # RETURN
        return return_dict

    def list_keypairs(self):
        self.__LOGGER.debug(f"Listing all keypairs for current user")
        # EXIT CASES
        if 'cloud' not in self.clients or not self.clients['cloud']:
            raise EXCP.MissingRequiredClient('cloud')

        # OBJECT LOGIC
        keypairs = self.clients['cloud'].get_all_keypairs()
        keypair_list = [kp_info for kp_id, kp_info in keypairs['key_pairs'].items()]

        # BUILD RETURN DICT
        self.__LOGGER.debug(f"Building Return dictionary")
        return_dict = {
            'key_pairs': keypair_list
        }
        # RETURN
        return return_dict

    def delete_keypair(self, key_id):
        self.__LOGGER.debug(f"Deleting keypair {key_id}")
        # EXIT CASES
        if 'cloud' not in self.clients or not self.clients['cloud']:
            raise EXCP.MissingRequiredClient('cloud')

        # OBJECT LOGIC
        attempt = self.clients['cloud'].delete_keypair(
            key_cloud_id=key_id
        )

        # BUILD RETURN DICT
        self.__LOGGER.debug(f"Building Return dictionary")
        return_dict = {
            'success': True
        }
        # RETURN
        return return_dict

    def get_draft_invoice(self, project_billing_id):
        self.__LOGGER.debug(f"Retieving preview of upcoming invoice for {project_billing_id}")
        # EXIT CASES
        if 'billing' not in self.clients or not self.clients['billing']:
            raise EXCP.MissingRequiredClient('billing')

        # OBJECT LOGIC
        draft = self.clients['billing'].get_invoice_preview(
            project_billing_id=project_billing_id
        )

        # BUILD RETURN DICT
        self.__LOGGER.debug(f"Building Return dictionary")
        return_dict = {
            'invoice': draft['invoice']
        }
        # RETURN
        return return_dict

    def list_account_invoice_paginated(self, project_billing_id, offset, limit):
        self.__LOGGER.debug(f"Listing invoices for {project_billing_id}")
        # EXIT CASES
        if 'billing' not in self.clients or not self.clients['billing']:
            raise EXCP.MissingRequiredClient('billing')

        # OBJECT LOGIC
        invoices = self.clients['billing'].get_all_invoices(
            project_billing_id=project_billing_id,
            offset=offset,
            limit=limit
        )

        # BUILD RETURN DICT
        self.__LOGGER.debug(f"Building Return dictionary")
        return_dict = {
            'total_invoices': len(invoices['invoices'])
            'invoices': invoices['invoices']
        }
        # RETURN
        return return_dict

    def get_invoice_by_id(self, project_billing_id, invoice_id):
        self.__LOGGER.debug(f"Retrieving invoice {invoice_id} for {project_billing_id}")
        # EXIT CASES
        if 'billing' not in self.clients or not self.clients['billing']:
            raise EXCP.MissingRequiredClient('billing')

        # OBJECT LOGIC
        invoice = self.clients['billing'].get_invoice(
            project_billing_id=project_billing_id,
            invoice_id=invoice_id
        )

        # BUILD RETURN DICT
        self.__LOGGER.debug(f"Building Return dictionary")
        return_dict = {
            'invoice': invoice['invoice']
        }
        # RETURN
        return return_dict

    def add_credits(self, project_billing_id, amount):
        self.__LOGGER.debug(f"")
        # EXIT CASES
        if 'billing' not in self.clients or not self.clients['billing']:
            raise EXCP.MissingRequiredClient('billing')

        # OBJECT LOGIC
        creds = self.clients['billing'].add_credits(
            project_billing_id=project_billing_id,
            amount=amount
        )

        # BUILD RETURN DICT
        self.__LOGGER.debug(f"Building Return dictionary")
        return_dict = {
            'credits': creds['amount']
        }
        # RETURN
        return return_dict

    def get_credits(self, project_billing_id):
        self.__LOGGER.debug(f"Fetching current credit amount after usage applied")
        # EXIT CASES
        if 'billing' not in self.clients or not self.clients['billing']:
            raise EXCP.MissingRequiredClient('billing')

        # OBJECT LOGIC
        remaining_credits = self.client['billing'].get_credits(
            project_billing_id=project_billing_id
        )

        # BUILD RETURN DICT
        self.__LOGGER.debug(f"Building Return dictionary")
        return_dict = {
            'credits': remaining_credits['amount']
        }
        # RETURN
        return return_dict

    def create_order(self, project_billing_id):
        self.__LOGGER.debug(f"Creating new order for account {project_billing_id}")
        # EXIT CASES
        if 'billing' not in self.clients or not self.clients['billing']:
            raise EXCP.MissingRequiredClient('billing')

        # OBJECT LOGIC
        order = self.clients['billing'].create_cluster_order(
            project_billing_id=project_billing_id
        )

        # BUILD RETURN DICT
        self.__LOGGER.debug(f"Building Return dictionary")
        return_dict = {
            'order_id': order['id']
            'order': order['order']
        }
        # RETURN
        return return_dict

    def add_order_tag(self, cluster_billing_id, tag_name, tag_value):
        self.__LOGGER.debug(f"Tagging order with {tag_name}:{tag_value}")
        # EXIT CASES
        if 'billing' not in self.clients or not self.clients['billing']:
            raise EXCP.MissingRequiredClient('billing')

        # OBJECT LOGIC
        tag = self.clients['billing'].add_order_tag(
            cluster_billing_id=cluster_billing_id, 
            tag_name=tag_name, 
            tag_value=tag_value
        )
        # BUILD RETURN DICT
        self.__LOGGER.debug(f"Building Return dictionary")
        return_dict = {
            'tag': tag['tag']
        }
        # RETURN
        return return_dict

    ##############################
    # HANDLER REQUIRED FUNCTIONS #
    ##############################
    def run_process(self):
        """
        The main running loop of the Handler.

        THIS IS EMPTY FOR API HANDLER ONLY
        API HANDLER RUNS VIA SPECIFIC FUNCTION CALLS
        """
        pass

    def disconnect(self):
        """
        Function for disconnecting all clients before garbage collection.
        """
        self.__LOGGER.info("Disconnecting API Clients and Components")
        for name, client in self.clients.items():
            client.disconnect()
        self.clients = None

    #######################
    # API HANDLER HELPERS #
    #######################

    def _scrub_orphans(self, orphans):
        '''
        Helper for deleting orphaned objects in complex create functions
        Orphans should be: <Tuple (client_type, object_type, id)>
            client_type: The name of the client in the clients map (cloud, billing)
            object_type: The ending of the function call for the delete of that object
                         (if func is 'delete_user' then object_type='user')
            id: The ID of the object to be deleted
        '''
        for orph_tup in orphans:
            getattr(self.clients[orph_tup[0]], 'delete_' + orph_tup[1])(orph_tup[2])