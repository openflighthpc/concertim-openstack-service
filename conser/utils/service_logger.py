"""
==============================================================================
 Copyright (C) 2024-present Alces Flight Ltd.

 This file is part of Concertim Openstack Service.

 This program and the accompanying materials are made available under
 the terms of the Eclipse Public License 2.0 which is available at
 <https://www.eclipse.org/legal/epl-2.0>, or alternative license
 terms made available by Alces Flight Ltd - please direct inquiries
 about licensing to licensing@alces-flight.com.

 Concertim Openstack Service is distributed in the hope that it will be useful, but
 WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, EITHER EXPRESS OR
 IMPLIED INCLUDING, WITHOUT LIMITATION, ANY WARRANTIES OR CONDITIONS
 OF TITLE, NON-INFRINGEMENT, MERCHANTABILITY OR FITNESS FOR A
 PARTICULAR PURPOSE. See the Eclipse Public License 2.0 for more
 details.

 You should have received a copy of the Eclipse Public License 2.0
 along with Concertim Openstack Service. If not, see:

  https://opensource.org/licenses/EPL-2.0

 For more information on Concertim Openstack Service, please visit:
 https://github.com/openflighthpc/concertim-openstack-service
==============================================================================
"""

# Py Packages
import logging
import os
import re

def create_logger(name, log_file, level):
    logger = logging.getLogger(name)
    if logger.hasHandlers(): 
        logger.handlers.clear()
    levels = {
        'DEBUG': logging.DEBUG, 
        'INFO': logging.INFO, 
        'WARNING': logging.WARNING, 
        'ERROR': logging.ERROR, 
        'CRITICAL': logging.CRITICAL
    }
    lvl = (levels[level.upper()])
    logger.setLevel(lvl)
    formatter = SensitiveFormatter('[%(asctime)s] - %(levelname)-8s: %(module)-12s: %(funcName)-26s===>  %(message)s')
    dir_name = os.path.dirname(log_file)
    try:
        # Create directories if they don't exist
        os.makedirs(dir_name, exist_ok=True)
        # Create the log file if it doesn't exist
        if not os.path.exists(log_file):
            open(log_file, 'w').close()
    except Exception as e:
        raise e(f"Could not create log file: {log_file} - {type(e).__name__} - {e}")

    try:
        # File handler for log file with given log level from CONFIG
        fh = logging.FileHandler(log_file)
        fh.setLevel(lvl)
        fh.setFormatter(formatter)
        # Console handler for console output with WARNING log level
        ch = logging.StreamHandler()
        ch.setLevel(logging.WARNING)
        ch.setFormatter(formatter)

        logger.addHandler(fh)
        logger.addHandler(ch)
    except Exception as e:
        raise e(f"Could not create FileHandler for log file: {log_file} - {type(e).__name__} - {e}")
    
    return logger


class SensitiveFormatter(logging.Formatter):
    def format(self, record):
        original = logging.Formatter.format(self, record)
        pattern = r'(\b\w*password\w*\b[\'\"]?:)\s?[\w\d!@#$%^&*.\'\"]+,*'
        split = re.split(pattern, original)
        filtered = ""
        needs_comma = False
        for s in split:
            if s and needs_comma:
                filtered += ","
                needs_comma = False
            if "password" in s:
                filtered += f"{s}************"
                needs_comma = True
            else:
                filtered += s
        return filtered