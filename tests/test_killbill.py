
from  con_opstk.billing.killbill.killbill import KillbillService 
from  con_opstk.data_handler.billing_handler.killbill.killbill_handler import KillbillHandler 
from con_opstk.data_handler.api_handler.api_handler import APIHandler

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

apihandler = APIHandler(config, log_file=log_file, enable_concertim=True, billing_enabled=True)

#ret = killbillservice.create_new_account("testaccount")

#ret = killbillservice.get_account_info(acct_id="a2f6a0aa-adf4-4abe-9745-eab09c82286e")


#ret = killbillservice.create_order(acct_id="a2f6a0aa-adf4-4abe-9745-eab09c82286e")

#ret = killbillservice.generate_invoice(acct_id="6e5b776f-0e13-4266-aebf-941c35482f08", target_date=datetime.date(2023, 11, 5))

#ret = killbillservice.get_invoice_raw(invoice_id="14f8cca0-e4e9-41f3-99d5-6c1cfe344907")

#ret = killbillservice.get_invoice_html(invoice_id="14f8cca0-e4e9-41f3-99d5-6c1cfe344907")

#ret = killbillservice.list_invoice()

#ret = killbillservice.search_invoices(search_key="6e5b776f-0e13-4266-aebf-941c35482f08")

#ret = killbillservice.get_bundles()

#ret = killbillservice.get_custom_fields_subscription("917aeb66-9672-4ef0-b6b2-ffc0c2fffbfb")

#ret = killbillservice.remove_custom_field_subscription(subscription_id="c4ebe214-e1d0-4d85-b75f-c805a0eb3202", custom_fields=["e402c55f-7395-41ae-81b5-74c5da872345", "55181542-1c27-4001-a730-b74bc5c883b3", "53827a02-8242-4b89-8a31-4ae95ddabced"])

#ret = killbillservice.post_metric(kb_metric="instance", subscription_id="73952906-5019-42b6-984e-f4eb08ffdf1c", amount="14" )

#ret = killbillservice.get_all_usage("73952906-5019-42b6-984e-f4eb08ffdf1c", start_date="2023-01-01", end_date="2023-10-14")



account = killbillservice.get_account_info(acct_id="06f0cab3-62d0-4920-a40b-27d99a53e834")['data'][0]

account.currency = 'USD'

killbillservice.update_account(account_id="06f0cab3-62d0-4920-a40b-27d99a53e83")


#ret = killbillservice.get_all_usage("d2a0bdb1-3046-431a-bdfb-b8a0f9ee7361", start_date="2023-01-01", end_date="2023-10-13")

#ret=killbillservice.delete_account()

#ret=killbillservice.delete_subscription()

# ****************
#ret = killbillhandler.create_kb_account("testaccount-handler")

#ret = killbillhandler.create_order(acct_id = "c4ebe214-e1d0-4d85-b75f-c805a0eb3202", os_stack_id = "placeholder-stack-id")

#**
#ret = killbillhandler.generate_invoice(acct_id = "6e5b776f-0e13-4266-aebf-941c35482f08", target_date="2013-11-05")

#ret = killbillhandler.generate_invoice_html(acct_id="6e5b776f-0e13-4266-aebf-941c35482f08", target_date="2013-11-05")




#ret = apihandler.create_new_billing_acct("test-api", "api@gmail.com")

logger.info(f"{ret}")

logger.info("Test completed")
    