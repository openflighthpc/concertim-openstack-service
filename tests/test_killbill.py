
from  con_opstk.billing.killbill.killbill import KillbillService 
from  con_opstk.data_handler.billing_handler.killbill.killbill_handler import KillbillHandler 

import con_opstk.app_definitions as app_paths
from con_opstk.utils.service_logger import create_logger
import yaml
import datetime

CONFIG_FILE = app_paths.CONFIG_FILE
LOG_DIR = app_paths.LOG_DIR

def load_config(config_file):
    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)
    return config


config = load_config(CONFIG_FILE)
log_file = LOG_DIR + 'billing.log'
logger = create_logger(__name__, log_file, config['log_level'])
logger.info(f"Log File: {log_file}")

killbillservice = KillbillService(config, log_file )
killbillhandler = KillbillHandler(config, log_file)

#ret = killbillservice.create_new_account("testaccount", "test@gmail.com")
#logger.info(f"{ret['headers']['Location']}")


#ret = killbillservice.get_account_info(acct_id="a2f6a0aa-adf4-4abe-9745-eab09c82286e")


#ret = killbillservice.create_subscription(acct_id="a2f6a0aa-adf4-4abe-9745-eab09c82286e", plan_name="openstack-standard-monthly")

#ret = killbillservice.generate_invoice(acct_id="6e5b776f-0e13-4266-aebf-941c35482f08", target_date=datetime.date(2023, 11, 5))

#ret = killbillservice.get_invoice_raw(invoice_id="14f8cca0-e4e9-41f3-99d5-6c1cfe344907")

#ret = killbillservice.get_invoice_html(invoice_id="14f8cca0-e4e9-41f3-99d5-6c1cfe344907")

#ret = killbillservice.list_invoice()

#ret = killbillservice.search_invoices(search_key="6e5b776f-0e13-4266-aebf-941c35482f08")

#ret = killbillservice.get_bundles()


#ret = killbillhandler.create_kb_account("testaccount-handler")

#ret = killbillhandler.create_order(acct_id = "a2f6a0aa-adf4-4abe-9745-eab09c82286e")

#**
# ret = killbillhandler.generate_invoice(acct_id = "6e5b776f-0e13-4266-aebf-941c35482f08", target_date=datetime.date(2023, 11, 5))

ret = killbillhandler.get_invoice_html(acct_id="6e5b776f-0e13-4266-aebf-941c35482f08")

logger.info(f"{ret}")

logger.info("Test completed")
    