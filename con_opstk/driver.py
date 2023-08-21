# Py Packages
import signal
import sys
import yaml
import time

# Local Imports
sys.path.append("..")
from utils.service_logger import create_logger
import app_definitions as app_paths

# GLOBAL VARS
CONFIG_FILE = app_paths.CONFIG_FILE
LOG_DIR = app_paths.LOG_DIR

def run_metrics(test=False):
    # Common
    from con_opstk.data_handler.metric_handler.metric_handler import MetricHandler
    log_file = MetricHandler.LOG_DIR + 'metrics.log'
    config = load_config(CONFIG_FILE)
    logger = create_logger(__name__, log_file, config['log_level'])
    
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
        ## FIRST RUN SETUP
        bulk_update_handler.full_update_sync()
        if not test:
            time.sleep(300)
            ## MAIN LOOP
            while True:
                try:
                    bulk_update_handler.full_update_sync()
                except Exception as e:
                    logger.error(f"Unexpected exception has caused the bulk update loop to terminate : {type(e).__name__} - {e} - {sys.exc_info()[2].tb_frame.f_code.co_filename} - {sys.exc_info()[2].tb_lineno}")
                    logger.warning(f"Continuing loop at next interval.")
                    continue
                finally:
                    time.sleep(300) # Run full sync every 5 min
        else:
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

def run_updates_aio(test=False):
    # Common
    from con_opstk.data_handler.update_handler.mq_listener import MqUpdateHandler
    from con_opstk.data_handler.update_handler.state_compare import BulkUpdateHandler
    log_file = LOG_DIR + 'updates_aio.log'
    config = load_config(CONFIG_FILE)
    logger = create_logger(__name__, log_file, config['log_level'])
    
    # Handler specific
    bulk_update_handler = None
    mq_update_handler = None

    # Add signals
    # Setup a signal handler to stop the service gracefully
    def signal_handler(sig, frame):
        stop(logger,bulk_update_handler,mq_update_handler)
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    '''
    FULL UPDATES MAIN CODE BEGIN
    '''
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
            time.sleep(300)
            ## MAIN LOOP
            while True:
                try:
                    bulk_update_handler.full_update_sync()
                except Exception as e:
                    logger.error(f"Unexpected exception has caused the full sync loop to terminate : {type(e).__name__} - {e} - {sys.exc_info()[2].tb_frame.f_code.co_filename} - {sys.exc_info()[2].tb_lineno}")
                    logger.warning(f"Continuing loop at next interval.")
                    continue
                finally:
                    time.sleep(300) # Run full sync every 5 min
        else:
            stop(logger,bulk_update_handler, mq_update_handler)
    except Exception as e:
        msg = f"Could not run All-In-One Updates process - {type(e).__name__} - {e} - {sys.exc_info()[2].tb_frame.f_code.co_filename} - {sys.exc_info()[2].tb_lineno}"
        logger.error(msg)
        stop(logger,bulk_update_handler,mq_update_handler)

def run_api_server():
    # Common
    from con_opstk.data_handler.api_server import run_app
    log_file = LOG_DIR + 'api_server.log'
    config = load_config(CONFIG_FILE)
    logger = create_logger(__name__, log_file, config['log_level'])
    logger.info("------- START -------")
    logger.info("STARTING API SERVER")
    run_app()





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
        'updates_aio': run_updates_aio,
        'api': run_api_server
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
