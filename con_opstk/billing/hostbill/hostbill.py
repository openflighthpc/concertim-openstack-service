import logging
import sys
import datetime

from keystoneauth1 import session
from keystoneauth1.identity import v3

# Disable insecure warnings  
import requests
requests.packages.urllib3.disable_warnings() 


# Local Imports
from con_opstk.utils.service_logger import create_logger
from con_opstk.billing.billing_service import BillingService


# HostBill Driver
class HostbillService(BillingService):

    # Init Openstack and HostBill clients
    def __init__(self, config, log_file):
        self.__config = config

        self.hostbill_api_url = self.__get_api_url(self.__config["hostbill"])
    

    def __call_url(self, path):

        url = self.hostbill_api_url + path
        logging.info("Calling url: %s", url)
        try:
            response = requests.get(url, verify=False)
            logging.debug("Response: %s", response)
            return response.json()
        except Exception as e:
            logging.error("Error calling url: %s", e)
            sys.exit(1)


    # Create hostbill API URL
    # e.x. https://95.154.198.65/admin/api.php?api_id=398fc836c1c8081c2dca&api_key=76cfefa1213286f6b720
    def __get_api_url(self, config):
        url = (
            config["api_url"]
            + "api_id="
            + config["api_id"]
            + "&api_key="
            + config["api_key"]
        )
        logging.debug("Hosbill API URL: %s", url)
        return url


    # get all hostbill accounts
    def get_hostbill_accounts(self):
        logging.info("Getting customer accounts from HostBill")
        accounts_list = self.__call_url("&call=getAccounts")
        logging.debug("accounts_list: %s", accounts_list)
        return accounts_list["accounts"]


    # Get metered variable information for a hostbill account
    def get_metered_var_info(self, account_id):
        metered_var_details = self.__call_url(
            "&call=meteredGetUsage&account_id=" + account_id
        )
        return metered_var_details["variables"]


    # get details for a hostbill account
    def get_hostbill_account_details(self, account_id):
        account_information = self.__call_url(
            "&call=getAccountDetails&id=" + account_id
        )
        #logging.debug("account_information: %s", account_information)
        account_details = account_information["details"]

        # If the account is a metered account, append the metered variable details
        if account_details["paytype"] == "Metered":
            account_details["metered_vars"] = self.get_metered_var_info(account_id)

        return account_details


    # Get all hostbill customers that have metered billing requirements and their account details
    def get_metered_customers(self):
        logging.info("Building metered customers details from HostBill")
        all_accounts_details = {}

        account_list = self.get_hostbill_accounts()
        for account in account_list:
            logging.debug("Getting acount details for account: %s", str(account["id"]))
            account_details = self.get_hostbill_account_details(account["id"])

            if (account_details["paytype"] == "Metered") and (account_details["status"] == "Active"):
                logging.debug("Adding metered customer: %s", account["id"])
                all_accounts_details[account["id"]] = account_details
        return all_accounts_details


    # Post usage for a specific variable for a specific hostbill account - returns true if successful
    def post_metered_usage(self, hostbill_account_id, variable_name, qty_to_post):
        logging.info("Posting usage for variable: %s", variable_name)
        post = self.__call_url(
            "&call=meteredAddUsage&account_id="
            + hostbill_account_id
            + "&variable="
            + variable_name
            + "&qty="
            + qty_to_post
        )
        logging.debug("post: %s", post)
        return True


    def get_product_details(self, product_id):
        product_information = self.__call_url(
            "&call=getProductDetails&id=" + product_id
        )
        #logging.debug("product_information: %s", product_information)
        product_details = product_information["details"]

        return product_details 
        

    