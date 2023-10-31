# Local Imports
from con_opstk.utils.service_logger import create_logger
from con_opstk.data_handler.billing_handler.billing_base import BillingHandler
# Py Packages
import sys
import json
from datetime import datetime, timedelta
from dateutil.parser import parse as dt_parse

class KillbillHandler(BillingHandler):
    
    def __init__(self, config_obj, log_file, clients=None):
        self.clients = clients if clients else BillingHandler.DEFAULT_CLIENTS
        super().__init__(config_obj, log_file, self.clients)
        self.__LOGGER = create_logger(__name__, self._LOG_FILE, self._CONFIG['log_level'])

    def update_cost(self):
        self.__LOGGER.info("== KillBill driver triggered ==")
        self.read_view()
        
        accounts = self.billing_service.get_account_info()['data']

        begin_date = datetime.today().date().replace(day=1)
        end_date = (begin_date + timedelta(days=32)).replace(day=1)

        for account in accounts:
            self.update_cost_account(account.account_id, begin_date, end_date)
        
        self.__LOGGER.info("== KillBill Process Completed ==")


    def update_cost_account(self, account_id, begin_date, end_date):

        self.__LOGGER.debug(f"Updating cost for Killbill account {account_id} : {begin_date} - {end_date}")

        accountCustomFields = self.billing_service.get_custom_fields_account(account_id)['data']

        openstack_project_id = None

        for customField in accountCustomFields:
            if customField.name == "openstack_project_id":
                openstack_project_id = customField.value
                break

        if openstack_project_id != None:
            self.update_user_cost_concertim(openstack_project_id=openstack_project_id, begin=begin_date, end = end_date)
        else:
            #Killbill account not associated with any Openstack project
            return
        
        bundles = self.billing_service.get_account_bundles(account_id)['data']
        for bundle in bundles:
            # Cycle through all subscriptions in the current bundle
            for subscription in bundle.subscriptions:
                if subscription.state != "ACTIVE":
                    continue
                #self.__LOGGER.debug(f" subscription {subscription}")
                self.update_cost_subscription(subscription.subscription_id, begin_date, end_date)


    def update_cost_subscription(self, subscription_id, begin_date, end_date):

        self.__LOGGER.debug(f"Updating cost for Killbill Subscription {subscription_id} : {begin_date} - {end_date}")

        customFields = self.billing_service.get_custom_fields_subscription(subscription_id)['data']

        openstack_enabled = False
        openstack_stack_id = None
        openstack_kb_metrics = []

        for customField in customFields:
            #self.__LOGGER.debug(customField)
            if customField.name == "openstack_metering_enabled" and customField.value == "true":
                openstack_enabled = True

            if customField.name == "openstack_stack_id":
                openstack_stack_id = customField.value

            if customField.name == "openstack_cloudkitty_metrics":
                openstack_kb_metrics = (customField.value).split(",")

        if openstack_enabled and openstack_stack_id:
            # Subscription is linked to an Openstack project
            self.__LOGGER.debug("subscription %s linked to openstack stack %s", subscription_id, openstack_stack_id,)
            
        else:
            # Subscription is not linked to an Openstack project
            return
        
        rack_rating_summary = self._get_rack_rating_summary(openstack_stack_id, begin_date, end_date)

        # Loop through all metrics configured in KillBill
        for kb_metric in openstack_kb_metrics:
            self.__LOGGER.debug("Processing kb_metric : %s", kb_metric)
            for metric in rack_rating_summary:
                # if the variable name from hostbill matches the metric res type from openstack in metrics.yaml
                if metric != kb_metric:
                    continue
                current_rate = float(rack_rating_summary[metric]) 

                kb_usage_response = self.billing_service.get_usage(kb_metric, subscription_id, begin_date, end_date)['data']

                if len(kb_usage_response.rolled_up_units) > 0:
                    openstack_billed_units = kb_usage_response.rolled_up_units[0].amount
                else:
                    openstack_billed_units = 0
            
                if float(current_rate) > openstack_billed_units:
                    amount_to_post = (float(current_rate) - openstack_billed_units)
                else:
                    amount_to_post = 0
                self.__LOGGER.debug("Amount to post : %s", amount_to_post)

                self.billing_service.post_metric(kb_metric, subscription_id, amount_to_post)

            self.__LOGGER.debug("completed metric: %s", kb_metric)



    def _get_rack_rating_summary(self, openstack_stack_id, begin_date, end_date):

        instances = self.openstack_service.get_stack_instances(stack_id=openstack_stack_id)

        self.__LOGGER.debug(f"Heat Stack {openstack_stack_id} : instances {instances}")

        rack_rating_summary = {}

        for instance in instances:
            self.__LOGGER.debug(f"Getting rating for Instance {instance}")
            instance_rating_summary = self.openstack_service.handlers['cloudkitty'].get_rating_summary_resource(instance.id, begin_date, end_date, resource_type='instance' )
            
            for metric in instance_rating_summary:
                if metric in rack_rating_summary:
                    rack_rating_summary[metric] += instance_rating_summary[metric]
                else:
                    rack_rating_summary[metric] = instance_rating_summary[metric]

        
        self.__LOGGER.debug(f"Rack Rating Summary : \n {rack_rating_summary} ")

        return rack_rating_summary


    def disconnect(self):
        self.__LOGGER.info(f"Disconnecting Killbill connections")
        self.billing_service.disconnect()
        super().disconnect()

