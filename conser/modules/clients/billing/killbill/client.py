# Local Imports
from conser.utils.service_logger import create_logger
from conser.factory.factory import Factory
from conser.factory.abs_classes.clients import AbsBillingClient
import conser.exceptions as EXCP

# Billing app imports
import killbill
from dateutil.parser import parse as dt_parse

# Py Packages
import sys
import json
from datetime import datetime, timedelta
# Disable insecure warnings  
import requests
requests.packages.urllib3.disable_warnings() 

class KillbillClient(AbsBillingClient):
    ############
    # DEFAULTS #
    ############
    BILLING_CREDIT_THRESHOLD=25
    BILLING_CYCLE_DAYS=31
    BILLING_CURRENCY='USD'
    CLUSTER_BILLING_ID_FIELD = 'openstack_stack_id'
    PROJECT_BILLING_ID_FIELD = 'project_cloud_id'
    CUSTOM_FIELD_FUNCTIONS = {
        'add': {
            'account': 'create_account_custom_fields_with_http_info',
            'subscription': 'create_subscription_custom_fields_with_http_info'
        },
        'get': {
            'account': 'get_account_custom_fields_with_http_info',
            'subscription': 'get_subscription_custom_fields_with_http_info'
        },
        'delete': {
            'account': 'delete_account_custom_fields',
            'subscription': 'delete_subscription_custom_fields'
        }
    }

    ########
    # INIT #
    ########
    def __init__(self, killbill_config, log_file, log_level):
        self._LOG_LEVEL = log_level
        self._LOG_FILE = log_file
        self._CONFIG = killbill_config
        self.__LOGGER = create_logger(__name__, self._LOG_FILE, self._LOG_LEVEL)
        self.__LOGGER.info("CREATING KILLBILL CLIENT")
        self.subscription_plan = self._CONFIG['plan_name']
        self.apis = self.get_connection_obj()
        if 'credit_threshold' in self._CONFIG and self._CONFIG['credit_threshold']:
            self._credit_threshold = float(self._CONFIG['credit_threshold'])
        else:
            self._credit_threshold = float(KillbillClient.BILLING_CREDIT_THRESHOLD)

    ############################################
    # BILLING CLIENT OBJECT REQUIRED FUNCTIONS #
    ############################################

    def create_account(self, project_cloud_name, project_cloud_id, primary_user_email, primary_user_cloud_id):
        """
        Function for creating object(s) to represent the Concertim Team for billing.
        """
        self.__LOGGER.debug(f"Creating new billing account for {project_cloud_name}")
        # EXIT CASES
        if not self.apis['account']:
            raise EXCP.NoComponentFound('AccountAPI')
        if not project_cloud_name:
            raise EXCP.MissingRequiredArgs('project_cloud_name')
        if not project_cloud_id:
            raise EXCP.MissingRequiredArgs('project_cloud_id')
        if not primary_user_email:
            raise EXCP.MissingRequiredArgs('primary_user_email')
        if not primary_user_cloud_id:
            raise EXCP.MissingRequiredArgs('primary_user_cloud_id')

        # BILLING OBJECT LOGIC
        #-- Create new account object
        acct_body = killbill.Account(
            name=project_cloud_name,
            email=primary_user_email,
            bill_cycle_day_local=KillbillClient.BILLING_CYCLE_DAYS,
            currency=KillbillClient.BILLING_CURRENCY
        )
        resp = self.apis['account'].create_account_with_http_info(
            acct_body,
            created_by='KillbillClient'
        )
        #-- Get response as dict and check for failures
        resp_dict = self._get_dict_from_resp(resp)
        resp_dict['data'] = resp_dict['data'].to_dict()
        #-- Get account ID located at end of header
        acct_id = resp_dict['headers']['Location'].split('/')[-1]
        #-- Add cloud ID to account as custom field
        field_id = self._add_custom_field(
            obj_type='account', 
            obj_id=acct_id, 
            field_name=KillbillClient.PROJECT_BILLING_ID_FIELD, 
            field_value=project_cloud_id
        )
        field_id = self._add_custom_field(
            obj_type='account', 
            obj_id=acct_id, 
            field_name='primary_user_cloud_id', 
            field_value=primary_user_cloud_id
        )

        # BUILD RETURN DICT
        self.__LOGGER.debug(f"Building Return dictionary")
        return_dict = {
            'id': acct_id,
            'name': resp_dict['data']['name'],
            'email': resp_dict['data']['email'],
        }

        # RETURN
        return return_dict

    def create_cluster_order(self, project_billing_id):
        """
        Function to create the equivalent of an order for a new cluster.
        """
        self.__LOGGER.debug(f"Creating new order for account {project_billing_id}")
        # EXIT CASES
        if not self.apis['subscription']:
            raise EXCP.NoComponentFound('SubscriptionAPI')
        if not project_billing_id:
            raise EXCP.MissingRequiredArgs('project_billing_id')
        #-- Verify account has enough credits
        remaining_credits = self._get_remaining_credits(project_billing_id)
        if remaining_credits <= self._credit_threshold:
            return {
                'data' : "Not enough credits to create a new order for account " + project_billing_id,
                'status' : 500,
                'headers' : None
            }
        
        # BILLING OBJECT LOGIC
        order_body = killbill.Subscription(
            account_id=project_billing_id,
            plan_name=self.subscription_plan
        )
        resp = self.apis['subscription'].create_subscription(
            order_body,
            created_by="KillbillClient"
        )
        resp_dict = self._get_dict_from_resp(resp)
        resp_dict['data'] = resp_dict['data'].to_dict()
        #-- Get subscription ID
        sub_id = resp_dict['headers']['Location'].split('/')[-1]

        # BUILD RETURN DICT
        self.__LOGGER.debug(f"Building Return dictionary")
        return_dict = {
            'id': sub_id,
            'start_date': resp_dict['data']['start_date'],
            'product_name': resp_dict['data']['product_name'],
            'billing_period': resp_dict['data']['billing_period'],
            'account_id': resp_dict['data']['account_id']
        }
        # RETURN
        return return_dict
    
    def update_usage(self, usage_metric_type, usage_metric_value, cluster_billing_id):
        """
        Function to update usage data for a User's cluster item in the billing app.
        """
        self.__LOGGER.debug(f"Updating usage for {cluster_billing_id} : {usage_metric_type} -> {usage_metric_value}")
        # EXIT CASES
        if not self.apis['usage']:
            raise EXCP.NoComponentFound('UsageAPI')
        if not cluster_billing_id:
            raise EXCP.MissingRequiredArgs('cluster_billing_id')
        if not usage_metric_type:
            raise EXCP.MissingRequiredArgs('usage_metric_type')

        # BILLING OBJECT LOGIC
        start_date = datetime.today().date().replace(day=1)
        end_date = (begin_date + timedelta(days=32)).replace(day=1)
        METRIC_PREFIX = 'cloud_'
        # Get current usage and subtract because killbill's record usage is accumlative
        curr_usage_resp = self.apis['usage'].get_usage_with_http_info(
            subscription_id=cluster_billing_id,
            unit_type=METRIC_PREFIX + usage_metric_type,
            start_date=start_date,
            end_date=end_date
        )
        curr_usage_dict = self._get_dict_from_resp(curr_usage_resp)
        if len(curr_usage_dict['data'].rolled_up_units) > 0:
            amount_to_post = usage_metric_value - curr_usage_dict['data'].rolled_up_units[0].amount
        else:
            amount_to_post = usage_metric_value

        usage_body = {
            "subscriptionId": cluster_billing_id,
            "unitUsageRecords": [
                {
                    "unitType": METRIC_PREFIX + usage_metric_type,
                    "usageRecords": [
                        {
                            "recordDate": datetime.date.today().strftime("%Y-%m-%d"),
                            "amount": amount_to_post,
                        }
                    ],
                }
            ],
            "trackingId": datetime.datetime.now().isoformat(),
        }
        resp = self.apis['usage'].record_usage_with_http_info(
            body=usage_body,
            created_by='KillbillClient'
        )
        resp_dict = self._get_dict_from_resp(resp)

        # BUILD RETURN DICT
        self.__LOGGER.debug(f"Building Return dictionary")
        return_dict = {
            'submitted': True,
            'usage': resp_dict['data'].to_dict()
        }
        # RETURN
        return return_dict

    def add_credits(self, project_billing_id, amount):
        """
        Function to add a currency/token/credit amount to aan Account.
        """
        self.__LOGGER.debug(f"Adding {amount} credit to {project_billing_id}")
        # EXIT CASES
        if not self.apis['credit']:
            raise EXCP.NoComponentFound('CreditAPI')
        if not project_billing_id:
            raise EXCP.MissingRequiredArgs('project_billing_id')
        if not amount:
            raise EXCP.MissingRequiredArgs('amount')
        if amount <= 0:
            raise ValueError("Must add more than 0 credits")

        # BILLING OBJECT LOGIC
        #-- Credits bodies are sent as a list
        credit_body = [
            killbill.InvoiceItem(
                account_id=project_billing_id,
                amount=amount,
                currency=KillbillClient.BILLING_CURRENCY,
                description='Adding Credits via KillbillClient'
            )
        ]
        resp = self.apis['credit'].create_credits_with_http_info(
            credit_body,
            auto_commit=True,
            created_by='KillbillClient',
            reason='Credits added in Concertim',
            comment=''
        )
        resp_dict = self._get_dict_from_resp(resp)
        credit_list = []
        amounts = 0.0
        for cred in resp_dict['data']:
            credit_list.append(cred.to_dict())
            amounts += cred.credit_amount

        # BUILD RETURN DICT
        self.__LOGGER.debug(f"Building Return dictionary")
        return_dict = {
            'submitted': True,
            'amount': amounts,
            'credits': credit_list
        }
        # RETURN
        return return_dict

    def delete_account(self, project_billing_id):
        """
        Function for deleting object(s) representing the Concertim Team.
        """
        self.__LOGGER.debug(f"Closing account: {project_billing_id}")
        # EXIT CASES
        if not self.apis['account']:
            raise EXCP.NoComponentFound('AccountAPI')
        if not project_billing_id:
            raise EXCP.MissingRequiredArgs('project_billing_id')
        
        # BILLING OBJECT LOGIC
        resp = self.apis['account'].close_account_with_http_info(
            account_id=project_billing_id,
            creted_by='KillbillClient',
            reason='Deleted', 
            comment='Deleted Via Concertim'
        )
        resp_dict = self._get_dict_from_resp(resp)

        # BUILD RETURN DICT
        self.__LOGGER.debug(f"Building Return dictionary")
        return_dict = {
            'submitted': True,
            'status': resp_dict['status']
        }
        # RETURN
        return return_dict

    def delete_cluster_order(self, cluster_billing_id):
        """
        Function to delete/cancel the equivalent of an order for a new cluster.
        """
        self.__LOGGER.debug(f"Cancelling order: {cluster_billing_id}")
        # EXIT CASES
        if not self.apis['subscription']:
            raise EXCP.NoComponentFound('SubscriptionAPI')
        if not cluster_billing_id:
            raise EXCP.MissingRequiredArgs('cluster_billing_id')

        # BILLING OBJECT LOGIC
        resp = self.apis['subscription'].cancel_subscription_plan_with_http_info(
            subscription_id=cluster_billing_id,
            created_by='KillbillClient'
        )
        resp_dict = self._get_dict_from_resp(resp)

        # BUILD RETURN DICT
        self.__LOGGER.debug(f"Building Return dictionary")
        return_dict = {
            'submitted': True,
            'status': resp_dict['status']
        }
        # RETURN
        return return_dict
    
    def get_account_billing_info(self, project_billing_id):
        """
        Function to retrieve an Account's billing information from the billing app.
        """
        self.__LOGGER.debug(f"Fetching info for account {project_billing_id}")
        # EXIT CASES
        if not self.apis['account']:
            raise EXCP.NoComponentFound('AccountAPI')
        if not project_billing_id:
            raise EXCP.MissingRequiredArgs('project_billing_id')
        
        # BILLING OBJECT LOGIC
        resp = self.apis['account'].get_account_with_http_info(
            project_billing_id,
            account_with_balance_and_cba=True
        )
        cfs = self._get_custom_fields(
            obj_type='account',
            obj_id=project_billing_id
        )
        puc_id = None
        pcb_id = None
        for cf in cfs['data']:
            if cf['name'] == 'primary_user_cloud_id':
                puc_id = cf['value']
            elif cf['name'] == KillbillClient.PROJECT_BILLING_ID_FIELD:
                pcb_id = cf['value']
        resp_dict = self._get_dict_from_resp(resp)
        resp_dict['data'] = resp_dict['data'].to_dict()

        # BUILD RETURN DICT
        self.__LOGGER.debug(f"Building Return dictionary")
        return_dict = {
            'id': project_billing_id,
            'name': resp_dict['data']['name'],
            'primary_user_cloud_id': puc_id,
            KillbillClient.PROJECT_BILLING_ID_FIELD: pcb_id,
            'credit_balance': resp['data']['account_cba']
        }
        # RETURN
        return return_dict

    def get_cluster_billing_info(self, cluster_billing_id):
        """
        Function to get a cluster's billing info from the billing app.
        """
        self.__LOGGER.debug(f"Fetching info for Order {cluster_billing_id}")
        # EXIT CASES
        if not self.apis['subscription']:
            raise EXCP.NoComponentFound('SubscriptionAPI')
        if not cluster_billing_id:
            raise EXCP.MissingRequiredArgs('cluster_billing_id')

        # BILLING OBJECT LOGIC
        resp = self.apis['subscription'].get_subscription_with_http_info(
            subscription_id=cluster_billing_id
        )
        resp_dict = self._get_dict_from_resp(resp)
        resp_dict['data'] = resp_dict['data'].to_dict()

        # BUILD RETURN DICT
        self.__LOGGER.debug(f"Building Return dictionary")
        return_dict = {
            'id': cluster_billing_id,
            'order': resp_dict['data']
        }
        # RETURN
        return return_dict

    def lookup_cluster_billing_info(self, cluster_cloud_id):
        """
        Function for killbill to find the subscrition info given the cluster's cloud_id
        """
        self.__LOGGER.debug(f"Looking for subscription for Cluster {cluster_cloud_id}")
        # EXIT CASES
        if not self.apis['custom_field']:
            raise EXCP.NoComponentFound('CustomFieldAPI')
        if not cluster_cloud_id:
            raise EXCP.MissingRequiredArgs('cluster_cloud_id')

        # BILLING OBJECT LOGIC
        resp = self.apis['custom_field'].search_custom_fields_with_http_info(
            search_key=cluster_cloud_id
        )
        resp_dict = self._get_dict_from_resp(resp)
        matches = {
            'count': 0,
            'subscriptions': {}
        }
        for cf in resp_dict['data']:
            if cf.object_type != "SUBSCRIPTION" or cf.name != KillbillClient.CLUSTER_BILLING_ID_FIELD:
                continue
            sub = self.get_cluster_billing_info(
                cluster_billing_id=cf.object_id
            )
            if sub.state != "ACTIVE":
                continue
            matches['subscriptions'][cf.object_id] = sub
            matches['count'] += 1
        if matches['count'] > 0:
            return matches
        return None

    def lookup_project_billing_info(self, project_cloud_id):
        """
        Function for killbill to find the account info given the projects's cloud_id
        """
        self.__LOGGER.debug(f"Looking for account for Project {project_cloud_id}")
        # EXIT CASES
        if not self.apis['custom_field']:
            raise EXCP.NoComponentFound('CustomFieldAPI')
        if not project_cloud_id:
            raise EXCP.MissingRequiredArgs('project_cloud_id')

        # BILLING OBJECT LOGIC
        resp = self.apis['custom_field'].search_custom_fields_with_http_info(
            search_key=project_cloud_id
        )
        resp_dict = self._get_dict_from_resp(resp)
        matches = {
            'count': 0,
            'accounts': {}
        }
        for cf in resp_dict['data']:
            if cf.object_type != "ACCOUNT" or cf.name != KillbillClient.PROJECT_BILLING_ID_FIELD:
                continue
            acct = self.get_account_billing_info(
                project_billing_id=cf.object_id
            )
            if acct.state != "ACTIVE":
                continue
            matches['accounts'][cf.object_id] = acct
            matches['count'] += 1
        if matches['count'] > 0:
            return matches
        return None
    
    def get_all_billing_accounts(self):
        """
        Function to get all User/Account info from the billing app.
        """
        self.__LOGGER.debug(f"Fetching info for all billing accounts")
        # EXIT CASES
        if not self.apis['account']:
            raise EXCP.NoComponentFound('AccountAPI')
        
        # BILLING OBJECT LOGIC
        resp = self.apis['account'].get_accounts_with_http_info(
            account_with_balance_and_cba=True
        )
        resp_dict = self._get_dict_from_resp(resp)
        #-- Convert everything to a dict
        acct_list = []
        acct_ids = []
        for acct in resp_dict['data']:
            acct_list.append(acct.to_dict())
            acct_ids.append(acct.account_id)

        # BUILD RETURN DICT
        self.__LOGGER.debug(f"Building Return dictionary")
        return_dict = {
            'ids': acct_ids,
            'accounts': acct_list
        }
        # RETURN
        return return_dict

    def get_all_billing_clusters(self, project_billing_id):
        """
        Function to get all Cluster/Order info from the billing app for an Account.
        """
        self.__LOGGER.debug(f"Fetching all orders for account {project_billing_id}")
        # EXIT CASES
        if not self.apis['account']:
            raise EXCP.NoComponentFound('AccountAPI')
        if not project_billing_id:
            raise EXCP.MissingRequiredArgs('project_billing_id')

        # BILLING OBJECT LOGIC
        resp = self.apis['account'].get_account_bundles_with_http_info(
            account_id=project_billing_id
        )
        resp_dict = self._get_dict_from_resp(resp)
        subs_list = []
        subs_ids = []
        for bundle in resp_dict['data']:
            for sub in bundle.subscriptions:
                subs_list.append(sub.to_dict())
                subs_ids.append(sub.subscription_id)

        # BUILD RETURN DICT
        self.__LOGGER.debug(f"Building Return dictionary")
        return_dict = {
            'ids': subs_ids,
            'orders': subs_list
        }
        # RETURN
        return return_dict

    def update_account_billing_info(self, project_billing_id, new_email=None):
        """
        Function to update an Account's info in the billing app. Email, password, etc.
        """
        self.__LOGGER.debug(f"Updating account {project_billing_id}")
        # EXIT CASES
        if not self.apis['account']:
            raise EXCP.NoComponentFound('AccountAPI')
        if not project_billing_id:
            raise EXCP.MissingRequiredArgs('project_billing_id')
        
        # BILLING OBJECT LOGIC
        update_body = killbill.Account()
        if new_email:
            update_body.email = new_email
        resp = self.apis['account'].update_account_with_http_info(
            account_id=project_billing_id,
            body=update_body,
            created_by='KillbillClient',
            reason='Updated', 
            comment='Updated Via Concertim'
        )
        resp_dict = self._get_dict_from_resp(resp)

        # BUILD RETURN DICT
        self.__LOGGER.debug(f"Building Return dictionary")
        return_dict = {
            'submitted': True,
            'status': resp_dict['status']
        }
        # RETURN
        return return_dict

    def get_invoice_preview(self, project_billing_id):
        """
        Get the json data of a preview of the current invoice amounts for an Account.
        """
        # EXIT CASES
        if not self.apis['invoice']:
            raise EXCP.NoComponentFound('InvoiceAPI')
        if not project_billing_id:
            raise EXCP.MissingRequiredArgs('project_billing_id')

        # BILLING OBJECT LOGIC
        dryrun_body = killbill.InvoiceDryRun(dry_run_type='UPCOMING_INVOICE')
        resp = self.apis['invoice'].generate_dry_run_invoice_with_http_info(
            dryrun_body,
            project_billing_id,
            created_by='KillbillClient'
        )
        resp_dict = self._get_dict_from_resp(resp)
        #-- Convert everything to dict
        if resp_dict['data'].items is not None:
            for item in resp_dict['data'].items:            
                if item.item_details is not None:
                    item.item_details = json.loads(item.item_details)
        resp_dict['data'] = resp_dict['data'].to_dict()
        invoice_dict = self._build_invoice_dict(resp_dict['data'])

        # BUILD RETURN DICT
        self.__LOGGER.debug(f"Building Return dictionary")
        return_dict = {
            'account_id': project_billing_id,
            'invoice': invoice_dict
        }
        # RETURN
        return return_dict
    
    def get_all_invoices(self, project_billing_id, offset=0, limit=100):
        """
        Get the paginated invoice history for an Account.
        """
        # EXIT CASES
        if not self.apis['account']:
            raise EXCP.NoComponentFound('AccountAPI')
        if not project_billing_id:
            raise EXCP.MissingRequiredArgs('project_billing_id')

        # BILLING OBJECT LOGIC
        resp = self.apis['account'].get_invoices_for_account_paginated_with_http_info(
            account_id=project_billing_id,
            offset=offset,
            limit=limit
        )
        resp_dict = self._get_dict_from_resp(resp)
        inv_list = []
        for inv in resp_dict['data']:
            inv_list.append(inv.to_dict())

        # BUILD RETURN DICT
        self.__LOGGER.debug(f"Building Return dictionary")
        return_dict = {
            'id': project_billing_id,
            'invoices': inv_list
        }
        # RETURN
        return return_dict

    def get_invoice(self, project_billing_id, invoice_id):
        """
        Get a specific invoice for an Account.
        """
        # EXIT CASES
        if not self.apis['invoice']:
            raise EXCP.NoComponentFound('InvoiceAPI')
        if not invoice_id:
            raise EXCP.MissingRequiredArgs('invoice_id')

        # BILLING OBJECT LOGIC
        resp = self.apis['invoice'].get_invoice_with_http_info(
            invoice_id
        )
        resp_dict = self._get_dict_from_resp(resp)
        invoice = self._build_invoice_dict(resp_dict['data'].to_dict())

        # BUILD RETURN DICT
        self.__LOGGER.debug(f"Building Return dictionary")
        return_dict = {
            'invoice': invoice
        }
        # RETURN
        return return_dict

    def get_credits(self, project_billing_id):
        """
        Get the actual credits for an account
        """
        # EXIT CASES
        if not project_billing_id:
            raise EXCP.MissingRequiredArgs('project_billing_id')

        # BILLING OBJECT LOGIC
        amount = self._get_remaining_credits(
            project_billing_id=project_billing_id
        )

        # BUILD RETURN DICT
        self.__LOGGER.debug(f"Building Return dictionary")
        return_dict = {
            'amount': amount
        }
        # RETURN
        return return_dict

    def add_order_tag(self, cluster_billing_id, tag_name, tag_value):
        """
        Add a custom tag to an existing cluster's order
        """
        # EXIT CASES
        if not cluster_billing_id:
            raise EXCP.MissingRequiredArgs('cluster_billing_id')
        if not tag_name:
            raise EXCP.MissingRequiredArgs('tag_name')

        # BILLING OBJECT LOGIC
        tag = self._add_custom_field(
            obj_type='subscription', 
            obj_id=cluster_billing_id, 
            field_name=tag_name, 
            field_value=tag_value
        )

        # BUILD RETURN DICT
        self.__LOGGER.debug(f"Building Return dictionary")
        return_dict = {
            'tag': tag
        }
        # RETURN
        return return_dict

    ####################################
    # CLIENT OBJECT REQUIRED FUNCTIONS #
    ####################################

    def get_connection_obj(self):
        configuration = killbill.Configuration()
        configuration.host = self._CONFIG["api_host"]
        configuration.api_key["X-Killbill-ApiKey"] = self._CONFIG["apikey"]
        configuration.api_key["X-Killbill-ApiSecret"] = self._CONFIG["apisecret"]
        configuration.username = self._CONFIG["username"]
        configuration.password = self._CONFIG["password"]
        kb_api_client = killbill.ApiClient(configuration)
        api_dict = {
            'account': killbill.api.AccountApi(kb_api_client),
            'subscription': killbill.api.SubscriptionApi(kb_api_client),
            'usage': killbill.api.UsageApi(kb_api_client),
            'invoice': killbill.api.InvoiceApi(kb_api_client),
            'credit': killbill.api.CreditApi(kb_api_client),
            'custom_field': killbill.api.CustomFieldApi(kb_api_client)
        }
        return api_dict

    def disconnect(self):
        self.__LOGGER.info("Disconnecting Killbill Client")
        self.apis = None

    ###########################
    # KILLBILL CLIENT HELPERS #
    ###########################

    def _get_dict_from_resp(self, response_obj):
        self.__LOGGER.debug(f"Creating dict from response")
        if not response_obj[0] or not response_obj[1] or not response_obj[2]:
            raise EXCP.BillingAPIError(f"API returned an unexpected object: {response_obj}")
        if response_obj[1] not in [200, 201, 204]:
            raise EXCP.BillingAPIFailure(f"Call was not successful -> {response_obj[2]}", response_obj[1])
        resp_dict = {
            'headers': response_obj[2],
            'status': response_obj[1],
            'data': response_obj[0]
        }
        return resp_dict

    def _add_custom_field(self, obj_type, obj_id, field_name, field_value):
        self.__LOGGER.debug(f"Adding custom field {field_name} to {obj_type}.{obj_id}")
        if obj_type not in KillbillClient.CUSTOM_FIELD_FUNCTIONS['add']:
            raise EXCP.InvalidArguments(f"obj_type:{obj_type}")
        # Bodies are sent as lists to create fields
        cust_field_body = [
            killbill.CustomField(
                name=field_name,
                value=field_value
            )
        ]
        attempt = getattr(self.apis[obj_type], KillbillClient.CUSTOM_FIELD_FUNCTIONS['add'][obj_type])(
            obj_id,
            cust_field_body,
            created_by='KillbillClient'
        )
        if attempt[1] not in [200, 201, 204]:
            raise EXCP.BillingAPIFailure(f"Call was not successful -> {response_obj[2]}", response_obj[1])
        field_id = attempt[2]['Location'].split('/')[-2]
        return field_id

    def _delete_custom_field(self, obj_type, obj_id, field_id):
        self.__LOGGER.debug(f"Deleting custom field {field_id} from {obj_type}.{obj_id}")
        if obj_type not in KillbillClient.CUSTOM_FIELD_FUNCTIONS['delete']:
            raise EXCP.InvalidArguments(f"obj_type:{obj_type}")
        attempt = getattr(self.apis[obj_type], KillbillClient.CUSTOM_FIELD_FUNCTIONS['delete'][obj_type])(
            obj_id,
            field_id,
            created_by='KillbillClient'
        )
        if attempt[1] not in [200, 201, 204]:
            raise EXCP.BillingAPIFailure(f"Call was not successful -> {response_obj[2]}", response_obj[1])
        return True

    def _get_custom_fields(self, obj_type, obj_id):
        self.__LOGGER.debug(f"Getting custom fields for {obj_type}.{obj_id}")
        if obj_type not in KillbillClient.CUSTOM_FIELD_FUNCTIONS['get']:
            raise EXCP.InvalidArguments(f"obj_type:{obj_type}")
        attempt = getattr(self.apis[obj_type], KillbillClient.CUSTOM_FIELD_FUNCTIONS['get'][obj_type])(
            obj_id,
        )
        if not attempt[0] or not attempt[1] or not attempt[2]:
            raise EXCP.BillingAPIError(f"API returned an unexpected object: {attempt}")
        if attempt[1] not in [200, 201, 204]:
            raise EXCP.BillingAPIFailure(f"Call was not successful -> {response_obj[2]}", response_obj[1])
        
        cf_list = []
        for cf in attempt[0]:
            cf_list.append(cf.to_dict())
        resp_dict = {
            'headers': attempt[2],
            'status': attempt[1],
            'data': cf_list
        }
        return resp_dict

    def _build_invoice_dict(self, invoice_data):
        self.__LOGGER.debug(f"Extracting invoice data and building invoice")
        new_items = {}
        for item in invoice_data["items"]:
            subscription_id = item["subscription_id"]
            if subscription_id is not None and item["item_type"] in ["USAGE", "RECURRING"]:
                if subscription_id not in new_items:
                    custom_fields = self._get_custom_fields('subscription', subscription_id)['data']
                    found = False
                    project_cloud_id = None
                    for field in custom_fields:
                        if field['name'] == "project_cloud_id" and len(field['value']) > 0:
                            found = True
                            project_cloud_id = field['value']
                            break
                    if found is True:
                        if subscription_id not in new_items:
                            new_items[subscription_id] = {
                                'amount': item['amount'],
                                'project_cloud_id': project_cloud_id,
                                'cluster_cloud_name': "Dummy Cluster Name",
                                'start_date': item['start_date'],
                                'end_date': item['end_date'],
                                'currency': item['currency']
                            }
                else:
                    new_items[subscription_id]['amount'] += item['amount']
        new_invoice = invoice_data
        new_invoice['items'] = new_items
        return new_invoice

    def _get_remaining_credits(self, project_billing_id):
        self.__LOGGER.debug(f"Getting remaining available credits for account {project_billing_id}")

        acct_info = self.get_account_billing_info(project_billing_id)
        account_credits = acct_info['credit_balance']

        draft_invoice_amount = 0
        draft_invoice = self.get_invoice_preview(project_billing_id)
        if 'amount' in draft_invoice['invoice'] and draft_invoice['invoice']['amount'] and draft_invoice['invoice']['amount'] >= 0:
            draft_invoice_amount = draft_invoice['invoice']['amount']
        
        self.__LOGGER.debug(f"Remaining credits = current_credits:{account_credits} - incoming_charges:{draft_invoice_amount}")
        remaining_credits = account_credits - draft_invoice_amount
        return remaining_credits


