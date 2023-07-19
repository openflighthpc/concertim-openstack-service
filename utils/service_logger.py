# Py Packages
import logging
import os

def create_logger(name, log_file, level):
    logger = logging.getLogger(name)
    levels = {'DEBUG': logging.DEBUG, 'INFO': logging.INFO, 'WARNING': logging.WARNING, 'ERROR': logging.ERROR, 'CRITICAL': logging.CRITICAL}
    logger.setLevel(levels[level.upper()])
    formatter = logging.Formatter('%(asctime)s - [%(levelname)s] (%(module)s) - %(message)s')
    dir_name = os.path.dirname(log_file)
    try:
        # Create directories if they don't exist
        os.makedirs(dir_name, exist_ok=True)

        # Create the log file if it doesn't exist
        if not os.path.exists(log_file):
            open(log_file, 'w').close()
    except Exception as e:
        raise Exception(f"Could not create log file: {log_file}. Reason: {str(e)}")

    try:
        fh = logging.FileHandler(log_file)
        fh.setFormatter(formatter)
        logger.addHandler(fh)
    except Exception as e:
        raise Exception(f"Could not create FileHandler for log file: {log_file}. Reason: {str(e)}")
    
    return logger