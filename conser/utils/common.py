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

# Local Imports
import conser.app_definitions as app_paths
import conser.exceptions as EXCP
from conser.modules.clients.concertim.objects.view import ConcertimView

# Py Packages
import pickle
import os
import yaml
from datetime import datetime

# HELPERS
def load_config():
    CONFIG_FILE = app_paths.CONFIG_FILE
    with open(CONFIG_FILE, 'r') as f:
        config = yaml.safe_load(f)
    
    if "cloud_type" not in config:
        raise EXCP.MissingConfiguration("cloud_type")
    if "billing_platform" not in config:
        raise EXCP.MissingConfiguration("billing_platform")

    if config["cloud_type"] not in config:
        raise EXCP.MissingConfiguration(config["cloud_type"], "FULL CONFIG BLOCK")
    if config["billing_platform"] not in config:
        raise EXCP.MissingConfiguration(config["billing_platform"], "FULL CONFIG BLOCK")

    if "message_queue" in config:
        if config["message_queue"] not in config:
            raise EXCP.MissingConfiguration(config["message_queue"], "FULL CONFIG BLOCK")

    return config

def load_view():
    view_location = app_paths.DATA_DIR + "view.pickle"
    try:
        with open(view_location, 'rb') as pkl_file:
            view = pickle.load(pkl_file)
        return view
    except Exception as e:
        raise Exception(f"Could not load view from {view_location} -> {e}")

def merge_views():
    view_location = app_paths.DATA_DIR
    # Load initial view - use current view file; if none exists make an empty view
    try:
        latest_view = load_view()
    except Exception as e:
        latest_view = ConcertimView()
    # Sort all files in acending order (when merging this will make the most recent view applied last)
    sorted_files = sorted(os.listdir(view_location))
    # Loop over all files
    for file_name in sorted_files:
        # Grab only view files with a timestamp
        if file_name.endswith('.pickle') and '~' in file_name:
            # Merge
            print(f"Merging {file_name}")
            with open(view_location+file_name, 'rb') as t_view:
                temp_view = pickle.load(t_view)
                if temp_view:
                    latest_view.merge(temp_view)
            os.remove(view_location+file_name)

    # Delete any stale items from the view after merge
    latest_view.delete_stale_items()
    
    # Save merged view as new view.pickle
    save_location = app_paths.DATA_DIR + "view.pickle"
    try:
        if not os.path.exists(save_location):
            os.mknod(save_location, mode = 0o660)
        with open(save_location, 'wb') as pkl_file:
            pickle.dump(latest_view, pkl_file, protocol=pickle.HIGHEST_PROTOCOL)
    except Exception as e:
        raise Exception(f"Could not save View after merging to {save_location} -> {e}")

def save_view(view_to_save):
    view_location = app_paths.DATA_DIR + "view~" + datetime.now().strftime("%Y-%m-%d-%H-%M-%S") + ".pickle"
    try:
        if not os.path.exists(view_location):
            os.mknod(view_location, mode = 0o660)
        with open(view_location, 'wb') as pkl_file:
            pickle.dump(view_to_save, pkl_file, protocol=pickle.HIGHEST_PROTOCOL)
    except Exception as e:
        raise Exception(f"Could not save View to {view_location} -> {e}")

def create_resync_flag():
    flag_location = app_paths.DATA_DIR + "resync.flag"
    try:
        if not os.path.exists(flag_location):
            os.mknod(flag_location, mode = 0o660)
        with open(flag_location, 'wb') as flag_file:
            flag_file.write(b" ")
    except Exception as e:
        raise Exception(f"Could not create flag file at {flag_location} -> {e}")

def check_resync_flag():
    flag_location = app_paths.DATA_DIR + "resync.flag"
    try:
        if os.path.exists(flag_location):
            return True
        return False
    except Exception as e:
        raise Exception(f"Could not check for flag file at {flag_location} -> {e}")

def delete_resync_flag():
    flag_location = app_paths.DATA_DIR + "resync.flag"
    try:
        if os.path.exists(flag_location):
            os.remove(flag_location)
    except Exception as e:
        raise Exception(f"Could not delete flag file at {flag_location} -> {e}")

def create_resync_hold():
    hold_location = app_paths.DATA_DIR + "resync.hold"
    try:
        if not os.path.exists(hold_location):
            os.mknod(hold_location, mode = 0o660)
        with open(hold_location, 'wb') as hold_file:
            hold_file.write(b" ")
    except Exception as e:
        raise Exception(f"Could not create hold file at {hold_location} -> {e}")

def check_resync_hold():
    hold_location = app_paths.DATA_DIR + "resync.hold"
    try:
        if os.path.exists(hold_location):
            return True
        return False
    except Exception as e:
        raise Exception(f"Could not check for hold file at {hold_location} -> {e}")

def delete_resync_hold():
    hold_location = app_paths.DATA_DIR + "resync.hold"
    try:
        if os.path.exists(hold_location):
            os.remove(hold_location)
    except Exception as e:
        raise Exception(f"Could not delete hold file at {hold_location} -> {e}")
