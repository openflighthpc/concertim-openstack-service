# Local Imports
from con_opstk.utils.service_logger import create_logger
import con_opstk.app_definitions as app_paths
# Py Packages
import signal
import sys
import yaml
import time

# GLOBAL VARS
CONFIG_FILE = app_paths.CONFIG_FILE
LOG_DIR = app_paths.LOG_DIR
ROOT_DIR = app_paths.ROOT_DIR
DATA_DIR = app_paths.DATA_DIR
print(f"Config File: {CONFIG_FILE}")
print(f"Root DIR: {ROOT_DIR}")
print(f"Log DIR: {LOG_DIR}")
print(f"Data DIR: {DATA_DIR}")

def run_metrics(test=False):
    # Common
    from con_opstk.data_handler.metric_handler.metric_handler import MetricHandler
    log_file = LOG_DIR + 'metrics.log'
    config = load_config(CONFIG_FILE)
    logger = create_logger(__name__, log_file, config['log_level'])
    logger.info(f"Log File: {log_file}")
    
    # Handler specific
    # granularity=60 to match IRV refresh rate
    # interval=15 to match concertim MRD polling interval
    metric_handler = None
    interval = 15
    granularity = 60

    # Add signals
    # Setup a signal handler to stop the service gracefully
    def signal_handler(sig, frame):
        stop(logger,metric_handler)
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    '''
    METRICS MAIN CODE BEGIN
    '''
    logger.info("------- START -------")
    logger.info("CONNECTING SERVICES")
    try:
        metric_handler = MetricHandler(config, log_file, granularity=granularity, interval=interval)
        logger.info("BEGINNING COMMUNICATION")
        if not test:
            while True:
                try:
                    metric_handler.run()
                except Exception as e:
                    logger.error(f"Unexpected exception has caused the metric loop to terminate : {type(e).__name__} - {e}")
                    logger.warning(f"Continuing loop at next interval.")
                    continue
                finally:
                    time.sleep(interval)
        else:
            try:
                metric_handler.run()
            except Exception as e:
                logger.error(f"Unexpected exception has caused the metric process to terminate : {type(e).__name__} - {e}")
                raise e
            stop(logger,metric_handler)
    except Exception as e:
        msg = f"Could not run Metrics process - {type(e).__name__} - {e} - {sys.exc_info()[2].tb_frame.f_code.co_filename} - {sys.exc_info()[2].tb_lineno}"
        logger.error(msg)
        stop(logger,metric_handler)

def run_bulk_updates(test=False):
    # Common
    from con_opstk.data_handler.update_handler.state_compare import BulkUpdateHandler
    log_file = LOG_DIR + 'updates_bulk.log'
    config = load_config(CONFIG_FILE)
    logger = create_logger(__name__, log_file, config['log_level'])
    logger.info(f"Log File: {log_file}")
    
    # Handler specific
    bulk_update_handler = None

    # Add signals
    # Setup a signal handler to stop the service gracefully
    def signal_handler(sig, frame):
        stop(logger,bulk_update_handler)
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    '''
    FULL UPDATES MAIN CODE BEGIN
    '''
    logger.info("------- START -------")
    logger.info("CONNECTING SERVICES")
    try:
        bulk_update_handler = BulkUpdateHandler(config, log_file)
        logger.info("BEGINNING COMMUNICATION")
        ## MAIN LOOP
        while True:
            try:
                bulk_update_handler.full_update_sync()
                if test:
                    break
            except Exception as e:
                logger.error(f"Unexpected exception has caused the bulk update loop to terminate : {type(e).__name__} - {e} - {sys.exc_info()[2].tb_frame.f_code.co_filename} - {sys.exc_info()[2].tb_lineno}")
                logger.warning(f"Continuing loop at next interval.")
                continue
            finally:
                # Run full sync every 2.5 min / check for resync every 15 seconds
                if not test:
                    for _ in range(1,11):
                        time.sleep(15)
                        bulk_update_handler._check_resync()
                else:
                    bulk_update_handler._check_resync()
        stop(logger,bulk_update_handler)
    except Exception as e:
        msg = f"Could not run All-In-One Updates process - {type(e).__name__} - {e} - {sys.exc_info()[2].tb_frame.f_code.co_filename} - {sys.exc_info()[2].tb_lineno}"
        logger.error(msg)
        stop(logger,bulk_update_handler)

def run_mq_updates(test=False):
    # Common
    from con_opstk.data_handler.update_handler.mq_listener import MqUpdateHandler
    log_file = LOG_DIR + 'updates_mq.log'
    config = load_config(CONFIG_FILE)
    logger = create_logger(__name__, log_file, config['log_level'])
    logger.info(f"Log File: {log_file}")
    
    # Handler specific
    mq_update_handler = None

    # Add signals
    # Setup a signal handler to stop the service gracefully
    def signal_handler(sig, frame):
        stop(logger,mq_update_handler)
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    '''
    MQ UPDATES MAIN CODE BEGIN
    '''
    logger.info("------- START -------")
    logger.info("CONNECTING SERVICES")
    try:
        mq_update_handler = MqUpdateHandler(config, log_file)
        logger.info("BEGINNING COMMUNICATION")
        mq_update_handler.start_listener()
    except Exception as e:
        msg = f"Could not run MQ Listener Updates process - {type(e).__name__} - {e} - {sys.exc_info()[2].tb_frame.f_code.co_filename} - {sys.exc_info()[2].tb_lineno}"
        logger.error(msg)
        stop(logger,mq_update_handler)

'''
def run_updates_aio(test=False):
    # Common
    from con_opstk.data_handler.update_handler.mq_listener import MqUpdateHandler
    from con_opstk.data_handler.update_handler.state_compare import BulkUpdateHandler
    log_file = LOG_DIR + 'updates_aio.log'
    config = load_config(CONFIG_FILE)
    logger = create_logger(__name__, log_file, config['log_level'])
    logger.info(f"Log File: {log_file}")
    
    # Handler specific
    bulk_update_handler = None
    mq_update_handler = None

    # Add signals
    # Setup a signal handler to stop the service gracefully
    def signal_handler(sig, frame):
        stop(logger,bulk_update_handler,mq_update_handler)
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


    #FULL UPDATES MAIN CODE BEGIN

    logger.info("------- START -------")
    logger.info("CONNECTING SERVICES")
    try:
        bulk_update_handler = BulkUpdateHandler(config, log_file)
        mq_update_handler = MqUpdateHandler(config, log_file)
        logger.info("BEGINNING COMMUNICATION")
        ## FIRST RUN SETUP
        bulk_update_handler.full_update_sync()
        mq_update_handler.load_view()
        mq_update_handler.start_listener()
        if not test:
            time.sleep(150)
            ## MAIN LOOP
            while True:
                try:
                    bulk_update_handler.full_update_sync()
                except Exception as e:
                    logger.error(f"Unexpected exception has caused the full sync loop to terminate : {type(e).__name__} - {e} - {sys.exc_info()[2].tb_frame.f_code.co_filename} - {sys.exc_info()[2].tb_lineno}")
                    logger.warning(f"Continuing loop at next interval.")
                    continue
                finally:
                    time.sleep(150) # Run full sync every 2.5 min
        else:
            stop(logger,bulk_update_handler, mq_update_handler)
    except Exception as e:
        msg = f"Could not run All-In-One Updates process - {type(e).__name__} - {e} - {sys.exc_info()[2].tb_frame.f_code.co_filename} - {sys.exc_info()[2].tb_lineno}"
        logger.error(msg)
        stop(logger,bulk_update_handler,mq_update_handler)
'''

def run_api_server():
    # Common
    from con_opstk.data_handler.api_server import run_app
    log_file = LOG_DIR + 'api_server.log'
    config = load_config(CONFIG_FILE)
    logger = create_logger(__name__, log_file, config['log_level'])
    logger.info(f"Log File: {log_file}")
    logger.info("------- START -------")
    logger.info("STARTING API SERVER")
    run_app()

def run_billing_server():

    from  con_opstk.data_handler.billing_handler.killbill.killbill_handler import KillbillHandler 
    from  con_opstk.data_handler.billing_handler.hostbill.hostbill_handler import HostbillHandler 
    

    log_file = LOG_DIR + 'billing.log'
    config = load_config(CONFIG_FILE)
    logger = create_logger(__name__, log_file, config['log_level'])
    logger.info(f"Log File: {log_file}")

    config = load_config(CONFIG_FILE)
    billing_backend = config["billing_platform"].lower()
    

    billers = {"hostbill": HostbillHandler, "killbill": KillbillHandler}
    billing_handler = billers[config["billing_platform"]](config, log_file)


    while True:

        billing_handler.update_cost()

        break
            
        if int(self.config["sleep_timer"]) > 0:
            time.sleep(int(self.config["sleep_timer"]))
        else:
            time.sleep(10)


### COMMON METHODS ###

def load_config(config_file):
    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)
    return config

# Setup a stop process for when the service is over
def stop(logger, *handlers):
    logger.info("STOPPING PROCESS")
    for handler in handlers:
        if handler:
            handler.disconnect()
    logger.info("EXITING PROCESS")
    logger.info("------- END -------\n")
    raise SystemExit

# Main method to call runners and pars args
def main(args):
    args_dict = {}
    valid = {
        'metrics': run_metrics,
        'updates_bulk': run_bulk_updates,
        'updates_mq': run_mq_updates,
        #'updates_aio': run_updates_aio,
        'api': run_api_server,
        'billing': run_billing_server
    }
    for arg in args:
        comm, value = arg.split('=')
        args_dict[comm] = value
    if not 'run' in args_dict or not args_dict['run']:
        raise SystemExit("No 'run' command found")
    if 'test' in args_dict and eval(args_dict['test']) == True and args_dict['run'] != 'api':
        if args_dict['run'] in valid:
            valid[args_dict['run']](test=True)
        else:
            raise SystemExit(f"'run' command set to invalid arg - valid run commands: {valid.keys()}")

    if args_dict['run'] in valid:
        valid[args_dict['run']]()
    else:
        raise SystemExit(f"'run' command set to invalid arg - valid run commands: {valid.keys()}")

# The main entry point of the package
if __name__ == "__main__":
    main(sys.argv[1:])
