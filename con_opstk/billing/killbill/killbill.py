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
    def create_new_account(self, name, email):
        self.__LOGGER.debug(f"Creating new account for {name}")
        accountApi = killbill.AccountApi(self.kb_api_client)
        body = Account(name=name, 
               email=email)
        acct = accountApi.create_account(body,created_by='KillbillHandler')
        return acct

    # Add subscription
    def create_order(self, acct_id, cluster_type):
        self.__LOGGER.debug(f"Creating new order for account: {acct_id}")
        subscriptionApi = killbill.api.SubscriptionApi(self.kb_api_client)
        body = Subscription(account_id=acct_id, plan_name=cluster_type)
        order = subscriptionApi.create_subscription(body, created_by='KillbillHandler')
        return order

    # Get account(s) info
    def get_account_info(self, acct_id=None):
        accountApi = killbill.AccountApi(self.kb_api_client)
        if acct_id:
            self.__LOGGER.debug(f"Getting account info for account: {acct_id}")
            accounts = accountApi.search_accounts(account_id)
        else:
            self.__LOGGER.debug(f"Getting account info for all accounts")
            accounts = accountApi.get_accounts()
        return accounts

    # Get invoice (raw)

    # Get invoice (html)

    # Add to invoice

    # List invoices (all)

    # List invoices for user (acct_id)

    # Close account (not delete)
    def close_account(self, acct_id):
        self.__LOGGER.debug(f"Closing account: {acct_id}")
        accountApi = killbill.AccountApi(self.kb_api_client)
        close = accountApi.close_account(acct_id)
        return close
    
    # Get subscriptions

    # Email invoice

    def disconnect(self):
        self.__LOGGER.info(f"Disconnecting Killbill Services")
        self.kb_api_client = None