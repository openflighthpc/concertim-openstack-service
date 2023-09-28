# Local Imports
from con_opstk.utils.service_logger import create_logger

# Py Packages
import sys
import json
# Disable insecure warnings  
import requests
requests.packages.urllib3.disable_warnings() 

from keystoneauth1 import session
from keystoneauth1.identity import v3

import logging
import datetime
import killbill

from con_opstk.billing.billing_service import BillingService


# KillBill Driver
class KillbillService(BillingService):

    # Init Openstack and Killbill clients
    def __init__(self, config, log_file):
        self.__config = config
        self.kb_api_client = self.__create_killbill_client(self.__config)

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
        killbill_config = config["killbill"]

        configuration = killbill.Configuration()
        configuration.host = killbill_config["api_host"]
        configuration.api_key["X-Killbill-ApiKey"] = killbill_config["apikey"]
        configuration.api_key["X-Killbill-ApiSecret"] = killbill_config["apisecret"]
        configuration.username = killbill_config["username"]
        configuration.password = killbill_config["password"]

        kb_api_client = killbill.ApiClient(configuration)

        return kb_api_client


    def get_usage(self, kb_metric, subscription_id, start_date, end_date):

        kb_usage_instance = killbill.UsageApi(self.kb_api_client)

        kb_usage_response = kb_usage_instance.get_usage(
            subscription_id=subscription_id,
            unit_type=str("openstack-billed-" + kb_metric),
            start_date=start_date,
            end_date=end_date)

        logging.debug(kb_usage_response)

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

        logging.debug(post_body)

        # Post usage to KillBill

        kb_usage_instance = killbill.UsageApi(self.kb_api_client)

        kb_usage_response = kb_usage_instance.record_usage(
            body=post_body, created_by="openstack-billing"
        )
        logging.debug(kb_usage_response)

        return kb_usage_response
    
                    

                    