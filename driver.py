# Local Imports
from conser.utils.service_logger import create_logger
import conser.utils.common as Helpers
import conser.app_definitions as app_paths
import conser.factory.factory.Factory as Factory
import conser.exceptions as EXCP
# Py Packages
import signal
import sys
import yaml
import time
import importlib
import argparse
from datetime import datetime

# GLOBAL VARS
CONFIG_FILE = app_paths.CONFIG_FILE
LOG_DIR = app_paths.LOG_DIR
ROOT_DIR = app_paths.ROOT_DIR
DATA_DIR = app_paths.DATA_DIR
print(f"Config File: {CONFIG_FILE}")
print(f"Root DIR: {ROOT_DIR}")
print(f"Log DIR: {LOG_DIR}")
print(f"Data DIR: {DATA_DIR}")

# Create Args Parsing branches
parser = argparse.ArgumentParser(prog="Concertim Cloud Service", 
                                description="This package is made for the purpose of facilitating communication between Alces Flight Ltd. Concertim"
                                            " and the backend applications configured.",)
parser.add_argument("--process", type=str, required=True, help="The type of handler process to be run - possible values are "
                                                             "metrics, update_sync, update_queue, billing, api")
parser.add_argument("--run_once", "-t", action="store_true", required=False, help="Specify whether to run the process only once (for testing purpose)")

# Main method to call runners and pars args
def main(args):
    # PARSE ARGS
    arguments = parser.parse_args()
    valid_process = [
        'metrics',
        'update_sync',
        'update_queue',
        'api',
        'billing'
    ]
    if arguments.process not in valid_process:
        raise argparse.ArgumentTypeError(f"Invalid process type -> {arguments.process}")

    # CREATE CONFIG DICT
    conf_dict = Helpers.load_config()
    # CREATE LOG FILE STRING
    log_file = LOG_DIR + arguments.process + datetime.now().strftime("%d-%m-%Y") + ".log"
    # MAIN PROCESS TREE
    if arguments.process == 'metrics':
        start_metrics_process(conf_dict, log_file, run_once=arguments.run_once)
    elif arguments.process == 'update_sync':
        start_sync_process(conf_dict, log_file, run_once=arguments.run_once)
    elif arguments.process == 'update_queue':
        start_queue_process(conf_dict, log_file, run_once=arguments.run_once)
    elif arguments.process == 'api':
        start_api_server(conf_dict, log_file)
    elif arguments.process == 'billing':
        start_billing_process(conf_dict, log_file, run_once=arguments.run_once)
    else:
        raise argparse.ArgumentTypeError(f"Invalid process type -> {arguments.process}")


def start_metrics_process(config, log_file, run_once=False):
    log_level = config["log_level"]
    logger = create_logger(__name__, log_file, log_level)
    logger.info("========== STARTING METRICS PROCESS ==========")
    logger.info(f"Log File: {log_file}")

    # METRICS SETUP
    # interval = 15 to match concertim MRD polling interval
    interval = 15
    retries = 0

    # CREATE HANDLER
    handler = Factory.get_handler(
        "metrics", 
        config['cloud_type'], 
        config['billing_platform'], 
        log_file, 
        enable_cloud_client=True, 
        enable_billing_client=False
    )

    # MAIN METRICS LOOP
    while True:
        try:
            handler.run_process()
        except Exception as e:
            logger.error(f"Unexpected exception has caused the Metrics loop to terminate : {type(e).__name__} - {e}")
            logger.warning(f"Continuing loop at next interval.")
            retries += 1
            continue
        finally:
            if run_once:
                break
            if retries >= 5:
                raise Exception(f"Metrics Loop continually failing - please check logs - {log_file}")
            time.sleep(interval)


def start_billing_process(config, log_file, run_once=False):
    log_level = config["log_level"]
    logger = create_logger(__name__, log_file, log_level)
    logger.info("========== STARTING BILLING PROCESS ==========")
    logger.info(f"Log File: {log_file}")

    # BILLING SETUP
    # interval = 15 to match concertim MRD polling interval
    interval = 15
    retries = 0

    # CREATE HANDLER
    handler = Factory.get_handler(
        "billing", 
        config['cloud_type'], 
        config['billing_platform'], 
        log_file, 
        enable_cloud_client=True, 
        enable_billing_client=True
    )

    # MAIN BILLING LOOP
    while True:
        try:
            handler.run_process()
        except Exception as e:
            logger.error(f"Unexpected exception has caused the Billing loop to terminate : {type(e).__name__} - {e}")
            logger.warning(f"Continuing loop at next interval.")
            retries += 1
            continue
        finally:
            if run_once:
                break
            if retries >= 5:
                raise Exception(f"Billing Loop continually failing - please check logs - {log_file}")
            time.sleep(interval)


def start_sync_process(config, log_file, run_once=False):
    log_level = config["log_level"]
    logger = create_logger(__name__, log_file, log_level)
    logger.info("========== STARTING SYNC PROCESS ==========")
    logger.info(f"Log File: {log_file}")

    # SYNC SETUP
    # interval = 15 to match concertim MRD polling interval
    resync_interval = 15
    resync_checks_amount = 10
    retries = 0

    # CREATE HANDLER
    handler = Factory.get_handler(
        "update_sync", 
        config['cloud_type'], 
        config['billing_platform'],
        log_file, 
        enable_cloud_client=True, 
        enable_billing_client=True
    )

    # MAIN SYNC LOOP
    while True:
        try:
            handler.run_process()
        except Exception as e:
            logger.error(f"Unexpected exception has caused the Update Sync loop to terminate : {type(e).__name__} - {e}")
            logger.warning(f"Continuing loop at next interval.")
            retries += 1
            continue
        finally:
            if run_once:
                handler.check_resync()
                break
            if retries >= 5:
                raise Exception(f"Update Sync Loop continually failing - please check logs - {log_file}")
            for _ in range(0,resync_checks_amount):
                time.sleep(resync_interval)
                handler.check_resync()


def start_queue_process(config, log_file, run_once=False):
    log_level = config["log_level"]
    logger = create_logger(__name__, log_file, log_level)
    logger.info("========== STARTING QUEUE PROCESS ==========")
    logger.info(f"Log File: {log_file}")

    # QUEUE SETUP

    # CREATE HANDLER
    handler = Factory.get_handler(
        "update_queue", 
        config['cloud_type'], 
        config['billing_platform'], 
        log_file, 
        enable_cloud_client=True, 
        enable_billing_client=False
    )

    # MAIN QUEUE LOOP
    try:
        handler.run_process()
    except Exception as e:
        logger.error(f"Unexpected exception has caused the Update Queue process to terminate : {type(e).__name__} - {e}")
        raise e


def start_api_server(config, log_file):
    from conser.api.api_server import run_api
    run_api(config)


# The main entry point of the package
if __name__ == "__main__":
    main(sys.argv[1:])