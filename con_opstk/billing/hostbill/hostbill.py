
import logging
import sys
import datetime

# Disable insecure warnings  
import requests
requests.packages.urllib3.disable_warnings() 

# Local Imports
from con_opstk.utils.service_logger import create_logger
from con_opstk.billing.utils.cloudkitty_helper import CloudkittyHelper
from con_opstk.billing.hostbill import hostbill_helper
from con_opstk.billing.billing_service import BillingService
from con_opstk.billing.utils.concertim_helper import ConcertimHelper



class HostbillService(BillingService):
    def __init__(self, config_obj, log_file):
        self._CONFIG = config_obj
        self._LOG_FILE = log_file
        self.__LOGGER = create_logger(__name__, self._LOG_FILE, self._CONFIG['log_level'])

        self.openstack_config = self._CONFIG["openstack"]
        self.cloudkitty_helper = CloudkittyHelper(openstack_config = self.openstack_config)
        self.concertim_helper = ConcertimHelper(self._CONFIG, self.cloudkitty_helper)
        

    # Trigger periodic data transfer using open clients
    def trigger_driver(self):
        logging.info("HostBill driver triggered")

        ## FIRST RUN SETUP
        self.concertim_helper.populate_view()

        self.__hostbill_driver(hostbill_details=self.__config["hostbill"],        openstack_details=self.__config["openstack"])
        


    

    # Main entry point for hostbill - define the global config and call the runner
    def __hostbill_driver(self, hostbill_details, openstack_details):
        global hostbill_config
        hostbill_config = hostbill_details
        logging.debug("hostbill_config: %s", hostbill_config)

        global openstack_config
        openstack_config = openstack_details
        logging.debug("openstack_config: %s", openstack_config)

        # Try to run the hostbill process and catch any exceptions
        #try:
        self.__run_hostbill_process()
        #except Exception as e:
        #    logging.error("Error running hostbill process: %s", e)
        #    sys.exit(1)


    # Function to run the hostbill process
    def __run_hostbill_process(self):
        # Get the cloudkitty client with the passed openstack credentials
        #cloudkitty_client = cloudkitty_helper.get_cloudkitty_client(openstack_config, "1")

        # get the hostbill API URL
        hostbill_api_url = hostbill_helper.get_api_url(hostbill_config)

        # get the list of tenants (openstack projects) that have cloudkitty ratings in the db
        #cloudkitty_tenant_list = cloudkitty_client.report.get_tenants()
        #logging.debug("tenant_list: %s", tenant_list)

        # get the detailed summary (openstack rating summary get) for each tenant in one dictionary
        #rating_summary_dict = cloudkitty_helper.get_rating_summary_all(
        #    tenants=tenant_list, client=cloudkitty_client
        #)

        # get all hostbill customers that have metered billing requirements and their account details
        metered_customers = hostbill_helper.get_metered_customers(url=hostbill_api_url)

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
            self.concertim_helper.update_user_cost_concertim(openstack_project_id=openstack_project_id, begin=account_details["previous_invoice"], end = datetime.date.today() + datetime.timedelta(days=1) )


            rating_summary = self.cloudkitty_helper.get_rating_summary_project(project_id=openstack_project_id, begin = account_details["previous_invoice"], end = datetime.date.today() + datetime.timedelta(days=1))

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

                    hostbill_helper.post_metered_usage(
                            url=hostbill_api_url,
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
