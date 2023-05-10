import logging
import os

def create_logger(log_file, level):
        logger = logging.getLogger(__name__)
        levels = {'DEBUG': logging.DEBUG, 'INFO': logging.INFO, 'WARNING': logging.WARNING, 'ERROR': logging.ERROR, 'CRITICAL': logging.CRITICAL}
        logger.setLevel(levels[level.upper()])
        formatter = logging.Formatter('%(asctime)s - [%(levelname)s] (%(module)s) - %(message)s')
        if not os.path.exists(log_file):
            open(log_file, 'w').close()
        fh = logging.FileHandler(log_file)
        fh.setFormatter(formatter)
        logger.addHandler(fh)
        return logger