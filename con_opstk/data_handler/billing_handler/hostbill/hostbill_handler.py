# Local Imports
from con_opstk.utils.service_logger import create_logger
from con_opstk.data_handler.billing_handler.billing_base import BillingHandler
from con_opstk.billing.hostbill.hostbill import HostbillService
# Py Packages
import sys
import json
import logging
import datetime

class HostbillHandler(BillingHandler):
    def __init__(self, config_obj, log_file, clients=None):
        self.clients = clients if clients else BillingHandler.DEFAULT_CLIENTS
        super().__init__(config_obj, log_file, self.clients)
        self.__LOGGER = create_logger(__name__, self._LOG_FILE, self._CONFIG['log_level'])
        self.hostbill_service = HostbillService(self._CONFIG, self._LOG_FILE)

    # Trigger periodic data transfer using open clients
    def update_cost(self):
        logging.info("HostBill driver triggered")
       
        self.read_view()
    
        # get all hostbill customers that have metered billing requirements and their account details
        metered_customers = self.hostbill_service.get_metered_customers()

        # intereate through the metered_customers and get the metered usage from openstack for each tenant
        logging.info("\n\n *** Processing HostBill Metered Customers and building usage report ***")
        for account, account_details in metered_customers.items():
            logging.debug("account: %s", account)
            logging.debug("account_details: %s", account_details)

            if account_details["custom"] == False:
                continue

            logging.debug(account_details["custom"])
            openstack_project_id = None
            for key in account_details["custom"]:
                if account_details["custom"][key]["name"] == "openstack_project_id":
                    openstack_project_id = account_details["custom"][key]["data"][key]
                    break

            if openstack_project_id == None:
                continue

            logging.debug("openstack_project_id: %s", openstack_project_id)

            # Updating User cost in Concertim
            self.update_user_cost_concertim(openstack_project_id=openstack_project_id, begin=account_details["previous_invoice"], end = datetime.date.today() + datetime.timedelta(days=1) )


            rating_summary = self.openstack_service.handlers['cloudkitty'].get_rating_summary_project(project_id=openstack_project_id, begin = account_details["previous_invoice"], end = datetime.date.today() + datetime.timedelta(days=1))

            logging.debug(rating_summary)

            # interate over all the metered variables and get their usage from openstack for the tenant then post the hostbill
            for variable_id, variable_details in account_details[
                "metered_vars"
            ].items():
                logging.debug("variable_details: %s", variable_details)
                logging.debug("checking variable: %s", variable_details["variable_name"])
                logging.debug("variable_id: %s", variable_id)
                for metric in rating_summary:
                    # if the variable name from hostbill matches the metric res type from openstack in metrics.yaml
                    
                    if metric != variable_details["variable_name"]:
                        continue

                    amount_to_post = float(rating_summary[metric]) 

                    self.hostbill_service.post_metered_usage(
                            hostbill_account_id=account_details["id"],
                            variable_name=variable_details["variable_name"],
                            qty_to_post=str(amount_to_post),
                        )
                logging.debug(
                    "completed variable: %s", variable_details["variable_name"]
                )
            
            logging.debug("completed Project: %s", openstack_project_id)
        logging.info(
            "Finished processing HostBill Metered Customers and posting usage report from Openstack"
        )