# Local Imports
from con_opstk.utils.service_logger import create_logger
from con_opstk.billing.billing_service import BillingService
from con_opstk.billing.exceptions import BillingAPIError
# Py Packages
import sys
import json
import datetime
# Disable insecure warnings  
import requests
requests.packages.urllib3.disable_warnings() 
# Billing app imports
import killbill
from dateutil.parser import parse as dt_parse


# KillBill Service
class KillbillService(BillingService):
    DEFAULT_SUB_PLAN = "openstack-standard-monthly"
    DEFAULT_CLOUDKITTY_METRICS="instance,cpu"

    def __init__(self, config_obj, log_file):
        super().__init__(config_obj, log_file)
        self.__LOGGER = create_logger(__name__, self._LOG_FILE, self._CONFIG['log_level'])
        self.kb_api_client = self.__create_killbill_client(self._CONFIG['killbill'])

    def get_bundles(self):

        self.__LOGGER.debug(f"Listing all bundles")
        
        kb_bundle_instance = killbill.BundleApi(self.kb_api_client)
        bundles = kb_bundle_instance.get_bundles_with_http_info()

        
        #self.__LOGGER.debug(bundles)

        return self._transform_response(bundles)
    

    def get_custom_fields_subscription(self, subscription_id):

        self.__LOGGER.debug(f"Getting Custom fields for subscription {subscription_id}")

        kb_subscription_api = killbill.SubscriptionApi(self.kb_api_client)
        custom_fields = kb_subscription_api.get_subscription_custom_fields(subscription_id)
        
        return self._transform_response(custom_fields)

    def remove_custom_field_subscription(self, subscription_id, custom_fields):
        subscriptionApi = killbill.api.SubscriptionApi(self.kb_api_client)
        subscriptionApi.delete_subscription_custom_fields(subscription_id=subscription_id, custom_field=custom_fields, created_by='KillbillService' )   

    
    def create_custom_field_subscription(self, subscription_id, field_name, field_value):
        self.__LOGGER.debug(f"Creating Custom fields for {subscription_id} : {field_name} = {field_value}")

        kb_subscription_api = killbill.SubscriptionApi(self.kb_api_client)

        body = killbill.CustomField(name=field_name, value=field_value)

        kb_subscription_response = kb_subscription_api.create_subscription_custom_fields(subscription_id, [body], created_by="KillbillService")

        return self._transform_response(kb_subscription_response)
    
    def create_custom_field_account(self, account_id, field_name, field_value):
        self.__LOGGER.debug(f"Creating Custom fields for {account_id} : {field_name} = {field_value}")

        kb_account_api = killbill.AccountApi(self.kb_api_client)

        body = killbill.CustomField(name=field_name, value=field_value)

        kb_subscription_response = kb_account_api.create_account_custom_fields_with_http_info(account_id, [body], created_by="KillbillService")

        return self._transform_response(kb_subscription_response)
    
    def get_custom_fields_account(self, account_id):

        accountApi = killbill.AccountApi(self.kb_api_client)

        allCustomFields = accountApi.get_all_custom_fields_with_http_info(account_id,object_type='ACCOUNT')

        return self._transform_response(allCustomFields)


    def __create_killbill_client(self, config):
        configuration = killbill.Configuration()
        configuration.host = config["api_host"]
        configuration.api_key["X-Killbill-ApiKey"] = config["apikey"]
        configuration.api_key["X-Killbill-ApiSecret"] = config["apisecret"]
        configuration.username = config["username"]
        configuration.password = config["password"]
        kb_api_client = killbill.ApiClient(configuration)
        return kb_api_client

    def get_all_usage(self, subscription_id, **kwargs):
        kb_usage_instance = killbill.UsageApi(self.kb_api_client)

        kb_usage_response = kb_usage_instance.get_all_usage_with_http_info(subscription_id=subscription_id, **kwargs)

        self.__LOGGER.debug(kb_usage_response)

        return self._transform_response(kb_usage_response)
    

    def get_usage(self, kb_metric, subscription_id, start_date, end_date):

        self.__LOGGER.debug(f"Getting Usage for {subscription_id} : {start_date} - {end_date}")

        kb_usage_instance = killbill.UsageApi(self.kb_api_client)

        kb_usage_response = kb_usage_instance.get_usage_with_http_info(
            subscription_id=subscription_id,
            unit_type=str("openstack-billed-" + kb_metric),
            start_date=start_date,
            end_date=end_date)

        self.__LOGGER.debug(kb_usage_response)

        return self._transform_response(kb_usage_response)

    def post_metric(self, kb_metric, subscription_id, amount):

        self.__LOGGER.debug(f"Posting metric for {subscription_id} : {kb_metric} - {amount}")

        post_body = {
            "subscriptionId": subscription_id,
            "unitUsageRecords": [
                {
                    "unitType": "openstack-billed-" + kb_metric,
                    "usageRecords": [
                        {
                            "recordDate": datetime.date.today().strftime(
                                "%Y-%m-%d"
                            ),
                            "amount": amount,
                        }
                    ],
                }
            ],
            "trackingId": datetime.datetime.now().isoformat(),
        }

        self.__LOGGER.debug(post_body)

        # Post usage to KillBill

        kb_usage_instance = killbill.UsageApi(self.kb_api_client)

        kb_usage_response = kb_usage_instance.record_usage_with_http_info(
            body=post_body, created_by="KillbillService"
        )
        self.__LOGGER.debug(kb_usage_response)

        return self._transform_response(kb_usage_response)

    # Create account
    def create_new_account(self, name, email, openstack_project_id,  **kwargs):
        self.__LOGGER.debug(f"Creating new account for {name}")
        accountApi = killbill.AccountApi(self.kb_api_client)
        body = killbill.Account(name=name, email=email, bill_cycle_day_local=31, currency='USD', **kwargs)
        
        account = accountApi.create_account(body,created_by='KillbillService')
        
        self.__LOGGER.debug(account)

        response = self._transform_response(account)

        location_header = response['headers']['Location']       
        account_id = location_header.split('/')[-1]

        self.create_custom_field_account(account_id=account_id,field_name="openstack_project_id", field_value=openstack_project_id)

        return response

    def _transform_response(self, raw_response):
        response = {}
        self.__LOGGER.debug(f"Formatting response.... {raw_response}")

        response['data'] = raw_response[0]
        response['status'] = raw_response[1]
        response['headers'] = raw_response[2]

        if self._check_response(response):
            return response
        else:
            raise BillingAPIError(f"API Call returned unexpected response - {raw_response}")

    def _check_response(self, response):
        self.__LOGGER.debug(f"Verifying response....")
        if 'data' not in response:
            return False
        if 'status' not in response:
            return False
        if 'headers' not in response:
            return False
        if int(response['status']) not in [200 , 201, 204]:
            return False
        self.__LOGGER.debug(f"Valid Response")
        return True
    
    # Add subscription
    def create_order(self, account_id, os_stack_id, plan_name=None):
        self.__LOGGER.debug(f"Creating new order for account {account_id}, stack id {os_stack_id}")

        if not self.__check_for_available_credits(account_id=account_id):
            raise Exception(f"Not enough credits to create a new order for account {account_id}")
        
        subscriptionApi = killbill.api.SubscriptionApi(self.kb_api_client)
        plan = plan_name if plan_name else KillbillService.DEFAULT_SUB_PLAN
        body = killbill.Subscription(account_id=account_id, plan_name=plan)
        self.__LOGGER.debug(f"Order to create: {body}")
        order = subscriptionApi.create_subscription(body, created_by='KillbillService')
        self.__LOGGER.debug(f"Killbill response: {order}")

        response = self._transform_response(order)

        location_header = response['headers']['Location']       
        subscription_id = location_header.split('/')[-1]

        self.create_custom_field_subscription(subscription_id=subscription_id, field_name="openstack_metering_enabled", field_value="true")

        self.create_custom_field_subscription(subscription_id=subscription_id, field_name="openstack_stack_id", field_value=os_stack_id)
                                                              
        self.create_custom_field_subscription(subscription_id=subscription_id, field_name="openstack_cloudkitty_metrics", field_value=KillbillService.DEFAULT_CLOUDKITTY_METRICS)   

        return response

    def __check_for_available_credits(self, account_id):

        self.__LOGGER.debug(f"Checking for available credits for account {account_id}")
        
        # Obtaining Credits present in an account
        account = self.get_account_info(account_id=account_id)

        account_credits = -1
        if 'account_cba' in account['data']:
            account_credits = account['data']['account_cba']

        self.__LOGGER.debug(f"Account Credits :  {account_credits}")
        if account_credits > 0:
            pass
        else:
            return False


        # Obtaining amount from draft invoice, how much user has spent
        draft_invoice_amount = 0
        draft_invoice = self.get_draft_invoice(account_id=account_id)

        if 'amount' in draft_invoice['data'] and draft_invoice['data']['amount'] is not None and draft_invoice['data']['amount'] >= 0:
            draft_invoice_amount = draft_invoice['data']['amount']
            self.__LOGGER.debug(f"Draft invoice amount :  {draft_invoice['data']['amount']}")
        
        remaining_credits = account_credits - draft_invoice_amount

        self.__LOGGER.debug(f"Credits left to launch new order : {remaining_credits}")
        
        # Enough credits available to create more orders
        if remaining_credits > 0:
            return True
        

        return False

    # Get account(s) info
    def get_account_info(self, account_id=None):

        accountApi = killbill.AccountApi(self.kb_api_client)
        if account_id:
            self.__LOGGER.debug(f"Getting account info for account: {account_id}")
            account = accountApi.get_account_with_http_info(account_id=account_id, account_with_balance_and_cba=True)
            response =  self._transform_response(account)
            response['data'] = response['data'].to_dict()
            return response

        self.__LOGGER.debug(f"Getting account info for all accounts")
        accounts = accountApi.get_accounts_with_http_info()
        response = self._transform_response(accounts)
        response['data'] = response['data'].to_dict()
        return response

    def get_account_bundles(self, account_id):
        self.__LOGGER.debug(f"Getting Bundles for account {account_id}")

        accountApi = killbill.AccountApi(self.kb_api_client)
        bundles = accountApi.get_account_bundles_with_http_info(account_id)

        return self._transform_response(bundles)

    def update_account(self, account_id):

        self.__LOGGER.debug(f"Updating Account  {account_id}")  

        accountApi = killbill.AccountApi(self.kb_api_client)
        body = killbill.Account(name="test", currency="USD")

        accountApi.update_account(account_id, body, created_by='KillbillService')


    """ def generate_invoice(self, account_id, target_date):

        self.__LOGGER.debug(f"Generating invoice for {account_id} : {target_date}")

        invoiceApi = killbill.api.InvoiceApi(self.kb_api_client)
        
        ret = invoiceApi.create_future_invoice_with_http_info(account_id, 
                                 created_by='KillbillService',  
                                 target_date=target_date)
        
        self.__LOGGER.debug(ret)
        return self._transform_response(ret) """

    # Get invoice (raw)
    def get_invoice_raw(self, invoice_id):
        self.__LOGGER.debug(f"Getting raw invoice for {invoice_id}")
        invoiceApi = killbill.api.InvoiceApi(self.kb_api_client)
        invoice = invoiceApi.get_invoice_with_http_info(invoice_id)
        self.__LOGGER.debug(f"{invoice}")
        response = self._transform_response(invoice)
        response['data'] = response['data'].to_dict()
        return response

    def get_latest_invoice(self, account_id):

        self.__LOGGER.debug(f"Getting latest invoice for account {account_id}")
        accountInvoices = self.list_account_invoice(account_id)

        latest_date = datetime.date(1970, 1, 1)
        latest_invoice_id = None
        for invoice in accountInvoices['data']:
            if invoice.target_date >= latest_date:
                latest_invoice_id = invoice.invoice_id
                latest_date = invoice.target_date
                self.__LOGGER.debug(f"Latest invoice found for date {latest_date}")
        
        if latest_invoice_id != None:
            return self.get_invoice_html(latest_invoice_id)['data']
        
        else:
            raise BillingAPIError(f"No latest invoice found for account {account_id}")
        
    def get_draft_invoice(self, account_id):

        self.__LOGGER.debug(f"Getting draft invoice for account {account_id}")
        
        invoiceApi = killbill.api.InvoiceApi(self.kb_api_client)

        body = killbill.InvoiceDryRun(dry_run_type='UPCOMING_INVOICE')

        invoice = invoiceApi.generate_dry_run_invoice_with_http_info(body,
                                              account_id,
                                              created_by='KillbillService')
        
        
        response = self._transform_response(invoice)

        if response['data'].items is not None:
            for item in response['data'].items:            
                if item.item_details != None:
                    item.item_details = json.loads(item.item_details)

        
        response['data'] = response['data'].to_dict()

        return response

    def list_account_invoice(self, account_id):

        self.__LOGGER.debug(f"Listing invoices for account {account_id}")
        accountApi = killbill.api.AccountApi(self.kb_api_client)

        accountInvoices = accountApi.get_invoices_for_account_with_http_info(account_id)
        
        self.__LOGGER.debug(f"{accountInvoices}")

        response =  self._transform_response(accountInvoices)


        invoice_list = []
        for invoice in accountInvoices[0]:
            invoice_list.append(invoice.to_dict())

        response['data'] = invoice_list
    
        self.__LOGGER.debug(f"{json.dumps(response['data'])}")
        return response

    def list_account_invoice_paginated(self, account_id, offset=0, limit=100):

        self.__LOGGER.debug(f"Listing paginated invoices for account {account_id}")
        accountApi = killbill.api.AccountApi(self.kb_api_client)

        accountInvoices = accountApi.get_invoices_for_account_paginated_with_http_info(account_id=account_id, offset=offset, limit=limit)
        
        self.__LOGGER.debug(f"{accountInvoices}")


        invoice_list = []
        for invoice in accountInvoices[0]:
            invoice_list.append(invoice.to_dict())

        response =  self._transform_response(accountInvoices)
        response['data'] = invoice_list
    
        self.__LOGGER.debug(f"{json.dumps(response['data'])}")
        return response
        
    # Get invoice (html)
    def get_invoice_html(self, invoice_id):

        self.__LOGGER.debug(f"Getting HTML invoice for {invoice_id}")

        invoiceApi = killbill.api.InvoiceApi(self.kb_api_client)
        
        invoice_html = invoiceApi.get_invoice_as_html_with_http_info(invoice_id)

        self.__LOGGER.debug(f"{invoice_html}")

        return self._transform_response(invoice_html)
    
    def _convert_date(self, datetime_str):
        return dt_parse(datetime_str).strftime('%Y-%m-%d')


    def generate_invoice_html(self, account_id, target_date):

        self.__LOGGER.debug(f"Genrating HTML invoice for {account_id} , date : {target_date}")
        invoice_date = self._convert_date(target_date)
        new_invoice = self.generate_invoice(account_id=account_id, target_date=invoice_date)

        self.__LOGGER.debug(f"New invoice  {new_invoice}")
        location_header = new_invoice['headers']['Location']       
        invoice_id = location_header.split('/')[-2]

        invoice_html = self.get_invoice_html(invoice_id)
        
        return invoice_html['data']

    # Add Credits
    def add_credits(self, account_id, credits_to_add):

        self.__LOGGER.debug(f"Adding Credits")

        creditApi = killbill.api.CreditApi(self.kb_api_client)

        creditBody = killbill.InvoiceItem(account_id=account_id, 
                         amount=credits_to_add, 
                         currency='USD', 
                         description='Adding Credits')

        credits = creditApi.create_credits_with_http_info([creditBody],
                         auto_commit=True,
                         created_by='KillbillService',
                         reason='reason', 
                         comment='comment')


        
        credit_list = []
        for credit in credits[0]:
            credit_list.append(credit.to_dict())
        
        response = self._transform_response(credits)
        response['data'] = credit_list

        #return json.loads(json.dumps(response['data'][0].to_dict(), default=str))
             

        return response

    # List invoices (all)
    def list_invoice(self):

        self.__LOGGER.debug(f"Listing all Invoices")

        invoiceApi = killbill.api.InvoiceApi(self.kb_api_client)

        invoices = invoiceApi.get_invoices()

        return self._transform_response(invoices)
    
    # List invoices for user (account_id)

    # Search Invoices
    def search_invoices(self, search_key):

        self.__LOGGER.debug(f"Searching invoices for search_key : {search_key}")
        invoiceApi = killbill.api.InvoiceApi(self.kb_api_client)

        result = invoiceApi.search_invoices(search_key)

        self.__LOGGER.debug(f"{result}")

        return self._transform_response(result)



    # Close account (not delete)
    def close_account(self, account_id):
        self.__LOGGER.debug(f"Closing account: {account_id}")
        accountApi = killbill.AccountApi(self.kb_api_client)
        close = accountApi.close_account(account_id)
        return self._transform_response(close)


    # Email invoice

    def disconnect(self):
        self.__LOGGER.info(f"Disconnecting Killbill Services")
        self.kb_api_client = None
