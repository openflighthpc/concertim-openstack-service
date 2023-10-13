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
    


    def __create_killbill_client(self, config):
        configuration = killbill.Configuration()
        configuration.host = config["api_host"]
        configuration.api_key["X-Killbill-ApiKey"] = config["apikey"]
        configuration.api_key["X-Killbill-ApiSecret"] = config["apisecret"]
        configuration.username = config["username"]
        configuration.password = config["password"]
        kb_api_client = killbill.ApiClient(configuration)
        return kb_api_client


    def get_usage(self, kb_metric, subscription_id, start_date, end_date):

        self.__LOGGER.debug(f"Getting Usage for {subscription_id} : {start_date} - {end_date}")

        kb_usage_instance = killbill.UsageApi(self.kb_api_client)

        kb_usage_response = kb_usage_instance.get_usage(
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
    def create_new_account(self, name,  **kwargs):
        self.__LOGGER.debug(f"Creating new account for {name}")
        accountApi = killbill.AccountApi(self.kb_api_client)
        body = killbill.Account(name=name, **kwargs)
        
        account = accountApi.create_account(body,created_by='KillbillService')
        
        self.__LOGGER.debug(account)

        return self._transform_response(account)

    def _transform_response(self, raw_response):
        response = {}
        
        response['data'] = raw_response[0]
        response['status'] = raw_response[1]
        response['headers'] = raw_response[2]

        if self._check_response(response):
            return response
        raise BillingAPIError(f"API Call returned unexpected response - {raw_response}")


    def _check_response(self, response):
        if 'data' not in response:
            return False
        if 'status' not in response:
            return False
        if 'headers' not in response:
            return False
        
        if response['status'] not in [200 , 201]:
            return False
        
        return True
    
    # Add subscription
    def create_order(self, acct_id, os_stack_id, plan_name=None):
        self.__LOGGER.debug(f"Creating new order for account {acct_id}, stack id {os_stack_id}")
        subscriptionApi = killbill.api.SubscriptionApi(self.kb_api_client)
        plan = plan_name if plan_name else KillbillService.DEFAULT_SUB_PLAN
        body = killbill.Subscription(account_id=acct_id, plan_name=plan)
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

    # Get account(s) info
    def get_account_info(self, acct_id=None):

        self.__LOGGER.debug(f"Getting Account info {acct_id}")

        accountApi = killbill.AccountApi(self.kb_api_client)
        if acct_id:
            self.__LOGGER.debug(f"Getting account info for account: {acct_id}")
            accounts = accountApi.search_accounts(acct_id)
        else:
            self.__LOGGER.debug(f"Getting account info for all accounts")
            accounts = accountApi.get_accounts()
        return self._transform_response(accounts)


    def generate_invoice(self, acct_id, target_date):

        self.__LOGGER.debug(f"Generating invoice for {acct_id} : {target_date}")

        invoiceApi = killbill.api.InvoiceApi(self.kb_api_client)
        
        ret = invoiceApi.create_future_invoice(acct_id, 
                                 created_by='KillbillService',  
                                 target_date=target_date)
        
        self.__LOGGER.debug(ret)
        return self._transform_response(ret)

    # Get invoice (raw)
    def get_invoice_raw(self, invoice_id):
        self.__LOGGER.debug(f"Getting raw invoice for {invoice_id}")
        invoiceApi = killbill.api.InvoiceApi(self.kb_api_client)
        invoice = invoiceApi.get_invoice(invoice_id)
        self.__LOGGER.debug(f"{invoice}")
        return self._transform_response(invoice)

    # Get invoice (html)
    def get_invoice_html(self, invoice_id):

        self.__LOGGER.debug(f"Getting HTML invoice for {invoice_id}")

        invoiceApi = killbill.api.InvoiceApi(self.kb_api_client)
        
        invoice_html = invoiceApi.get_invoice_as_html(invoice_id)

        self.__LOGGER.debug(f"{invoice_html}")

        return self._transform_response(invoice_html)
    
    def _convert_date(self, datetime_str):
        return dt_parse(datetime_str).strftime('%Y-%m-%d')


    def generate_invoice_html(self, acct_id, target_date):
        invoice_date = self._convert_date(target_date)
        new_invoice = self.generate_invoice(acct_id=acct_id, target_date=invoice_date)

        location_header = new_invoice['headers']['Location']       
        invoice_id = location_header.split('/')[-1]

        invoice_html = self.get_invoice_html(invoice_id)
        
        return invoice_html['data']

    # Add to invoice

    # List invoices (all)
    def list_invoice(self):

        self.__LOGGER.debug(f"Listing all Invoices")

        invoiceApi = killbill.api.InvoiceApi(self.kb_api_client)

        invoices = invoiceApi.get_invoices()

        return self._transform_response(invoices)
    


    # List invoices for user (acct_id)

    # Search Invoices
    def search_invoices(self, search_key):

        self.__LOGGER.debug(f"Searching invoices for search_key : {search_key}")
        invoiceApi = killbill.api.InvoiceApi(self.kb_api_client)

        result = invoiceApi.search_invoices(search_key)

        self.__LOGGER.debug(f"{result}")

        return self._transform_response(result)



    # Close account (not delete)
    def close_account(self, acct_id):
        self.__LOGGER.debug(f"Closing account: {acct_id}")
        accountApi = killbill.AccountApi(self.kb_api_client)
        close = accountApi.close_account(acct_id)
        return self._transform_response(close)


    # Email invoice

    def disconnect(self):
        self.__LOGGER.info(f"Disconnecting Killbill Services")
        self.kb_api_client = None