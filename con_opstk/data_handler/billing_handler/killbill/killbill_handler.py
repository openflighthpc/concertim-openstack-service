# Local Imports
from con_opstk.utils.service_logger import create_logger
from con_opstk.data_handler.billing_handler.billing_base import BillingHandler
# Py Packages
import sys
import json
import datetime
from dateutil.parser import parse as dt_parse

class KillbillHandler(BillingHandler):
    def __init__(self, config_obj, log_file, clients=None):
        self.clients = clients if clients else BillingHandler.DEFAULT_CLIENTS
        super().__init__(config_obj, log_file, self.clients)
        self.__LOGGER = create_logger(__name__, self._LOG_FILE, self._CONFIG['log_level'])

    def update_cost(self):
        self.__LOGGER.info("KillBill driver triggered")
        self.read_view()
        bundles = self.billing_service.get_bundles()
        self.__LOGGER.debug(bundles)
        for bundle in bundles:
            # Cycle through all subscriptions in the current tenant
            for subscription in bundle.subscriptions:
                self.__LOGGER.debug("Found subscription " + subscription.subscription_id )
                #self.__LOGGER.debug("subscription : %s", subscription)
                customFields = self.billing_service.search_custom_fields_subscription(subscription.subscription_id) 
                #self.__LOGGER.debug(kb_cf_response)

                openstack_enabled = False
                openstack_project_id = None
                openstack_kb_metrics = []

                for customField in customFields:
                    #self.__LOGGER.debug(customField)
                    if customField.name == "openstack_metering_enabled" and customField.value == "true":
                        openstack_enabled = True

                    if customField.name == "openstack_project_id":
                        openstack_project_id = customField.value

                    if customField.name == "openstack_cloudkitty_metrics":
                        openstack_kb_metrics = (customField.value).split(",")

                if openstack_enabled and openstack_project_id:
                    # Subscription is linked to an Openstack project
                    self.__LOGGER.debug("subscription %s -> openstack %s",subscription.subscription_id,openstack_project_id,)
                else:
                    # Subscription is not linked to an Openstack project
                    continue

                # Updating User cost in Concertim
                self.update_user_cost_concertim(openstack_project_id=openstack_project_id, begin=subscription.billing_start_date, end = datetime.date.today() + datetime.timedelta(days=1))
                rating_summary = self.openstack_service.handlers['cloudkitty'].get_rating_summary_project(project_id=openstack_project_id, begin = subscription.billing_start_date, end = datetime.date.today() + datetime.timedelta(days=1))
                self.__LOGGER.debug(rating_summary)

                # Loop through all metrics configured in KillBill
                for kb_metric in openstack_kb_metrics:
                    self.__LOGGER.debug("Processing kb_metric : %s", kb_metric)
                    for metric in rating_summary:
                        # if the variable name from hostbill matches the metric res type from openstack in metrics.yaml
                        if metric != kb_metric:
                            continue
                        current_rate = float(rating_summary[metric]) 

                        start_date=subscription.billing_start_date.strftime("%Y-%m-%d")
                        end_date=(datetime.date.today() + datetime.timedelta(days=1)).strftime("%Y-%m-%d")

                        kb_usage_response = self.billing_service.get_usage(kb_metric, subscription.subscription_id, start_date, end_date)

                        if len(kb_usage_response.rolled_up_units) > 0:
                            openstack_billed_units = kb_usage_response.rolled_up_units[0].amount
                        else:
                            openstack_billed_units = 0
                    
                        if float(current_rate) > openstack_billed_units:
                            amount_to_post = (float(current_rate) - openstack_billed_units)
                        else:
                            amount_to_post = 0
                        self.__LOGGER.debug("Amount to post : %s", amount_to_post)

                        self.billing_service.post_metric(kb_metric, subscription.subscription_id, amount_to_post)
                    self.__LOGGER.debug("completed metric: %s", kb_metric)
    


    # New user setup function
    def create_kb_account(self, name, **kwargs):

        response = self.billing_service.create_new_account(name, **kwargs)

        location_header = response['headers']['Location']       
        account_id = location_header.split('/')[-1]

        return account_id


    # Create order for cluster
    def create_order(self, acct_id):
        response = self.billing_service.create_order(acct_id=acct_id)

        location_header = response['headers']['Location']       
        subscription_id = location_header.split('/')[-1]

        return subscription_id


    def generate_invoice(self, acct_id, target_date):
        tar_date = self._convert_date(target_date)
        new_invoice = self.billing_service.generate_invoice(acct_id=acct_id, target_date=tar_date)

        location_header = new_invoice['headers']['Location']       
        invoice_id = location_header.split('/')[-1]

        invoice = self.billing_service.get_invoice(invoice_id)

        return invoice
     
        
    #Generate invoice html
    def generate_invoice_html(self, acct_id, target_date):
        tar_date = self._convert_date(target_date)
        new_invoice = self.billing_service.generate_invoice(acct_id=acct_id, target_date=tar_date)

        location_header = new_invoice['headers']['Location']       
        invoice_id = location_header.split('/')[-1]

        invoice_html = self.billing_service.get_invoice_html(invoice_id)
        
        return invoice_html


    def disconnect(self):
        self.__LOGGER.info(f"Disconnecting Killbill connections")
        self.billing_service.disconnect()
        super().disconnect()

