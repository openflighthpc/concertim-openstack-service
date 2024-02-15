# Local Imports
import conser.app_definitions as app_paths
import conser.exceptions as EXCP
import pickle

# HELPERS
def load_config():
    CONFIG_FILE = app_paths.CONFIG_FILE
    with open(config_file, 'r') as f:
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
        raise e(f"Could not load view from {view_location}")

def save_view(view_to_save):
    view_location = app_paths.DATA_DIR + "view.pickle"
    try:
        if not os.path.exists(view_location):
            os.mknod(view_location, mode = 0o660)
        with open(view_location, 'wb') as pkl_file:
            pickle.dump(view_to_save, pkl_file, protocol=pickle.HIGHEST_PROTOCOL)
    except Exception as e:
        raise e(f"Could not save View to {view_location}")

def create_resync_flag():
    flag_location = app_paths.DATA_DIR + "resync.flag"
    try:
        if not os.path.exists(flag_location):
            os.mknod(flag_location, mode = 0o660)
        with open(flag_location, 'wb') as flag_file:
            flag_file.write(" ")
    except Exception as e:
        raise e(f"Could not create flag file at {flag_location}")

def check_resync_flag():
    flag_location = app_paths.DATA_DIR + "resync.flag"
    try:
        if os.path.exists(flag_location):
            return True
        return False
    except Exception as e:
        raise e(f"Could not check for flag file at {flag_location}")

def delete_resync_flag():
    flag_location = app_paths.DATA_DIR + "resync.flag"
    try:
        if os.path.exists(flag_location):
            os.remove(flag_location)
    except Exception as e:
        raise e(f"Could not delete flag file at {flag_location}")