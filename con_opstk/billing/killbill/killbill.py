# Local Imports
from con_opstk.utils.service_logger import create_logger
from con_opstk.billing.billing_service import BillingService
# Py Packages
import sys
import json
import datetime
# Disable insecure warnings  
import requests
requests.packages.urllib3.disable_warnings() 
# Billing app imports
import killbill


# KillBill Driver
class KillbillService(BillingService):
    # Init Killbill clients
    def __init__(self, config_obj, log_file):
        super().__init__(config_obj, log_file)
        self.__LOGGER = create_logger(__name__, self._LOG_FILE, self._CONFIG['log_level'])
        self.kb_api_client = self.__create_killbill_client(self._CONFIG['killbill'])

    def get_bundles(self):

        kb_bundle_instance = killbill.BundleApi(self.kb_api_client)
        kb_bundle_response = kb_bundle_instance.get_bundles_with_http_info()[0]

        return kb_bundle_response
    

    def search_custom_fields_subscription(self, subscription_id):

        kb_cf_instance = killbill.CustomFieldApi(self.kb_api_client)
        kb_cf_response = kb_cf_instance.search_custom_fields( \
            search_key=subscription_id)
        
        return kb_cf_response


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

        kb_usage_instance = killbill.UsageApi(self.kb_api_client)

        kb_usage_response = kb_usage_instance.get_usage(
            subscription_id=subscription_id,
            unit_type=str("openstack-billed-" + kb_metric),
            start_date=start_date,
            end_date=end_date)

        self.__LOGGER.debug(kb_usage_response)

        return kb_usage_response

    def post_metric(self, kb_metric, subscription_id, amount):

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

        kb_usage_response = kb_usage_instance.record_usage(
            body=post_body, created_by="KillbillHandler"
        )
        self.__LOGGER.debug(kb_usage_response)

        return kb_usage_response

    # Create account
    def create_new_account(self, name,  **kwargs):
        self.__LOGGER.debug(f"Creating new account for {name}")
        accountApi = killbill.AccountApi(self.kb_api_client)
        body = killbill.Account(name=name, **kwargs)
        
        account = accountApi.create_account(body,created_by='KillbillHandler')
        
        self.__LOGGER.debug(account)

        return self.__transform_response(account)

    def __transform_response(self, raw_response):
        response = {}
        
        response['data'] = raw_response[0]
        response['status'] = raw_response[1]
        response['headers'] = raw_response[2]

        return response
    
    # Add subscription
    def create_subscription(self, acct_id, plan_name):
        self.__LOGGER.debug(f"Creating new order for account: {acct_id}")
        subscriptionApi = killbill.api.SubscriptionApi(self.kb_api_client)
        body = killbill.Subscription(account_id=acct_id, plan_name=plan_name)
        order = subscriptionApi.create_subscription(body, created_by='KillbillHandler')

        self.__LOGGER.debug(order)

        return self.__transform_response(order)

    # Get account(s) info
    def get_account_info(self, acct_id=None):
        accountApi = killbill.AccountApi(self.kb_api_client)
        if acct_id:
            self.__LOGGER.debug(f"Getting account info for account: {acct_id}")
            accounts = accountApi.search_accounts(acct_id)
        else:
            self.__LOGGER.debug(f"Getting account info for all accounts")
            accounts = accountApi.get_accounts()
        return self.__transform_response(accounts)


    def generate_invoice(self, acct_id, target_date):
        invoiceApi = killbill.api.InvoiceApi(self.kb_api_client)
        
        ret = invoiceApi.create_future_invoice(acct_id, 
                                 created_by='KillbillHandler',  
                                 target_date=target_date)
        
        self.__LOGGER.debug(ret)

        return self.__transform_response(ret)

    # Get invoice (raw)

    def get_invoice_raw(self, invoice_id):

        invoiceApi = killbill.api.InvoiceApi(self.kb_api_client)

        invoice = invoiceApi.get_invoice(invoice_id)

        self.__LOGGER.debug(f"{invoice}")

        return self.__transform_response(invoice)

    # Get invoice (html)

    def get_invoice_html(self, invoice_id):

        invoiceApi = killbill.api.InvoiceApi(self.kb_api_client)

        invoice = invoiceApi.get_invoice_as_html(invoice_id)

        self.__LOGGER.debug(f"{invoice}")


        return self.__transform_response(invoice)

    # Add to invoice

    # List invoices (all)

    def list_invoice(self):
        invoiceApi = killbill.api.InvoiceApi(self.kb_api_client)

        invoices = invoiceApi.get_invoices()

        return self.__transform_response(invoices)
    


    # List invoices for user (acct_id)

    def search_invoices(self, search_key):
        invoiceApi = killbill.api.InvoiceApi(self.kb_api_client)

        result = invoiceApi.search_invoices(search_key)

        self.__LOGGER.debug(f"{result}")

        return self.__transform_response(result)



    # Close account (not delete)
    def close_account(self, acct_id):
        self.__LOGGER.debug(f"Closing account: {acct_id}")
        accountApi = killbill.AccountApi(self.kb_api_client)
        close = accountApi.close_account(acct_id)
        return self.__transform_response(close)
    
    # Get subscriptions

    def list_bundles(self):
        bundleApi = killbill.BundleApi(self.kb_api_client)
        bundles = bundleApi.get_bundles()
        return self.__transform_response(bundles)

    # Email invoice

    def disconnect(self):
        self.__LOGGER.info(f"Disconnecting Killbill Services")
        self.kb_api_client = None