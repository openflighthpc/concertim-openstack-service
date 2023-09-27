# Local Imports
from con_opstk.utils.service_logger import create_logger

# Py Packages
import sys
import json
# Disable insecure warnings  
import requests
requests.packages.urllib3.disable_warnings() 

import logging
import datetime

import killbill

from con_opstk.billing.utils.cloudkitty_helper import CloudkittyHelper
from con_opstk.billing.billing_service import BillingService
from con_opstk.billing.utils.concertim_helper import ConcertimHelper


class KillbillService(BillingService):

    # Init Openstack and Killbill clients 
    def __init__(self, config_obj, log_file):
        self._CONFIG = config_obj
        self._LOG_FILE = log_file
        self.__LOGGER = create_logger(__name__, self._LOG_FILE, self._CONFIG['log_level'])

        self.openstack_config = self.__config["openstack"]
        self.cloudkitty_helper = CloudkittyHelper(openstack_config = self.openstack_config)
        self.concertim_helper = ConcertimHelper(self.__config, self.cloudkitty_helper)
        
        self.kb_api_client = self.__create_killbill_client(self.__config)

    
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


    def __post_metric__(self, kb_usage_instance, kb_metric, subscription, rate):

        kb_usage_response = kb_usage_instance.get_usage(
            subscription_id=subscription.subscription_id,
            unit_type=str("openstack-billed-" + kb_metric),
            start_date=subscription.billing_start_date.strftime("%Y-%m-%d"),
            end_date=(
                datetime.date.today() + datetime.timedelta(days=1)
            ).strftime("%Y-%m-%d"),
        )

        logging.debug(kb_usage_response)

        if len(kb_usage_response.rolled_up_units) > 0:
            openstack_billed_units = kb_usage_response.rolled_up_units[
                0
            ].amount
        else:
            openstack_billed_units = 0
     
        if float(rate) > openstack_billed_units:
            amount_to_post = (
                float(rate) - openstack_billed_units
            )

        else:
            amount_to_post = 0

        logging.debug("Amount to post : %s", amount_to_post)

        post_body = {
            "subscriptionId": subscription.subscription_id,
            "unitUsageRecords": [
                {
                    "unitType": "openstack-billed-" + kb_metric,
                    "usageRecords": [
                        {
                            "recordDate": datetime.date.today().strftime(
                                "%Y-%m-%d"
                            ),
                            "amount": amount_to_post,
                        }
                    ],
                }
            ],
            "trackingId": datetime.datetime.now().isoformat(),
        }

        logging.debug(post_body)

        # Post usage to KillBill
        kb_usage_response = kb_usage_instance.record_usage(
            body=post_body, created_by="openstack-billing"
        )
        logging.debug(kb_usage_response)



    # Trigger periodic data transfer using open clients
    def trigger_driver(self):
        logging.info("KillBill driver triggered")

        ## FIRST RUN SETUP
        self.concertim_helper.populate_view()

        logging.debug("openstack_config: %s", self.openstack_config)

        
        kb_bundle_instance = killbill.BundleApi(self.kb_api_client)
        kb_bundle_response = kb_bundle_instance.get_bundles_with_http_info()[0]
        # logging.debug(kb_bundle_response)

        for bundle in kb_bundle_response:

            # Cycle through all subscriptions in the current tenant
            for subscription in bundle.subscriptions:
                logging.debug("Found subscription " + subscription.subscription_id )
                #logging.debug("subscription : %s", subscription)
                

                kb_cf_instance = killbill.CustomFieldApi(self.kb_api_client)
                kb_cf_response = kb_cf_instance.search_custom_fields(
                    search_key=subscription.subscription_id
                )

                #logging.debug(kb_cf_response)

                openstack_enabled = False
                openstack_project_id = None
                openstack_kb_metrics = []

                for customField in kb_cf_response:
                    #logging.debug(customField)
                    if (
                        customField.name == "openstack_metering_enabled"
                        and customField.value == "true"
                    ):
                        openstack_enabled = True

                    if customField.name == "openstack_project_id":
                        openstack_project_id = customField.value

                    if customField.name == "openstack_cloudkitty_metrics":
                        openstack_kb_metrics = (customField.value).split(",")

                if  openstack_enabled and openstack_project_id:
                    
                    # Subscription is linked to an Openstack project
                    logging.debug(
                        "subscription %s -> openstack %s",
                        subscription.subscription_id,
                        openstack_project_id,
                    )
                else:
                    # Subscription is not linked to an Openstack project
                    continue

                # Updating User cost in Concertim
                self.concertim_helper.update_user_cost_concertim(openstack_project_id=openstack_project_id, begin=subscription.billing_start_date, end = datetime.date.today() + datetime.timedelta(days=1) )

                rating_summary = self.cloudkitty_helper.get_rating_summary_project(project_id=openstack_project_id, begin = subscription.billing_start_date, end = datetime.date.today() + datetime.timedelta(days=1))

                logging.debug(rating_summary)

                kb_usage_instance = killbill.UsageApi(self.kb_api_client)

                # Loop through all metrics configured in KillBill
                for kb_metric in openstack_kb_metrics:
                    logging.debug("Processing kb_metric : %s", kb_metric)

                    for metric in rating_summary:
                    # if the variable name from hostbill matches the metric res type from openstack in metrics.yaml
                    
                        if metric != kb_metric:
                            continue

                        amount_to_post = float(rating_summary[metric]) 

                        hostbill_helper.post_metered_usage(
                                url=hostbill_api_url,
                                hostbill_account_id=account_details["id"],
                                variable_name=variable_details["variable_name"],
                                qty_to_post=str(amount_to_post),
                            )

                        self.__post_metric__(kb_usage_instance, kb_metric, subscription, amount_to_post)

                    logging.debug("completed metric: %s", kb_metric)

                    

                    
