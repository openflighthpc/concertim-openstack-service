# Local Imports
import conser.exceptions as EXCP
# Python Imports
import importlib

class Factory(object):
    """
    Object for building the correct Handler Object with all
    Client objects.
    """

    HANDLER_OBJECTS = [
        "update_sync",
        "update_queue",
        "api",
        "metrics",
        "billing"
    ]
    CLIENT_OBJECTS = {
        "concertim": "concertim",
        "cloud": {
            "openstack": {
                "queues": [
                    "rmq"
                ]
                "components": [
                    "cloudkitty",
                    "gnocchi",
                    "heat",
                    "keystone",
                    "nova"
                ]
            }
        },
        "billing": [
            "killbill"
        ]
    }

###############################
#          MAIN GETs          #
###############################
    @staticmethod
    def get_handler(handler_type, cloud_type, billing_app, log_file, log_level, cloud_auth_dict=None, enable_cloud_client=True, enable_billing_client=True):
        """
        Returns a concrete implementation of the given handler configuration

        REQUIRED:
            handler_type : type of HANDLER_OBJECT
            cloud_type : type of cloud to connect with for the handler
            billing_app : type of billing application being used
            log_file : the string of the log file location/name
        OPTIONAL:
            cloud_auth_dict : an optional alternative cloud auth than what is in the config file (used for API)
            enable_cloud_client : flag to specify if handler needs a cloud client object
            enable_billing_client : flag to specify if a handler needs a billing client object
        """
        if handler_type not in Factory.HANDLER_OBJECTS:
            raise EXCP.InvalidHandler(handler_type)
        if cloud_type not in Factory.CLIENT_OBJECTS['cloud']:
            raise EXCP.InvalidClient(cloud_type)
        if billing_app not in Factory.CLIENT_OBJECTS['billing']:
            raise EXCP.InvalidClient(billing_app)

        if handler_type == "api":
            handler = _build_api_handler(cloud_type, billing_app, log_file, log_level, cloud_auth_dict, enable_cloud_client, enable_billing_client)
        elif handler_type == "billing":
            handler = _build_billing_handler(cloud_type, billing_app, log_file, log_level, enable_cloud_client, enable_billing_client)
        elif handler_type == "metrics":
            handler = _build_metrics_handler(cloud_type, billing_app, log_file, log_level, enable_cloud_client, enable_billing_client)
        elif handler_type == "update_sync":
            handler = _build_sync_handler(cloud_type, billing_app, log_file, log_level, enable_cloud_client, enable_billing_client)
        elif handler_type == "update_queue":
            handler = _build_queue_handler(cloud_type, billing_app, log_file, log_level, enable_cloud_client, enable_billing_client)
        else:
            raise EXCP.HandlerNotImplemented(handler_type)

        return handler

    @staticmethod
    def get_client(client_type, client_config, log_file, log_level, client_name=None, components_list=None):
        """
        Returns a concrete implementation of the given client configuration

        REQUIRED:
            client_type : type of CLIENT_OBJECT (concertim, cloud, billing)
        OPTIONAL:
            client_name : if cloud or billing client - a name for the specific app is needed
            components_list : list of components to add for the client
        """

        if client_type not in Factory.CLIENT_OBJECTS:
            raise EXCP.InvalidClient(client_type)

        if client_type == "concertim":
            client = _build_concertim_client(client_config, log_file, log_level)
        elif client_type == "cloud":
            client = _build_cloud_client(client_name, client_config, log_file, log_level, components_list=components_list)
        elif client_type == "billing":
            client = _build_billing_client(cilent_name, client_config, log_file, log_level)
        else:
            raise EXCP.ClientNotImplemented(client_type)
        
        return client

    @staticmethod
    def get_opstk_component(component_name, session_obj, log_file, log_level):
        """
        Returns a concrete implementation of the given Openstack Component object 
        using the given keystoneauth1.session object.

        REQUIRED:
            component_name : the name of the openstack component object to create (i.e. keystone, nova, ...)
            session_obj : the keystoneauth1.session object to use when connection to the Component's
                          python client
        """
        component = None
        if component_name == "keystone":
            component = _build_keystone_component(session_obj, log_file, log_level)
        elif component_name == "nova":
            component = _build_nova_component(session_obj, log_file, log_level)
        elif component_name == "heat":
            component = _build_heat_component(session_obj, log_file, log_level)
        elif component_name == "gnocchi":
            component = _build_gnocchi_component(session_obj, log_file, log_level)
        elif component_name == "cloudkitty":
            component = _build_cloudkitty_component(session_obj, log_file, log_level)
        else:
            raise EXCP.ComponentNotImplemented(f"{component_name}")

        return component


###############################
#       HANDLER BUILDERS      #
###############################

# API
    @staticmethod
    def _build_api_handler(cloud_type, billing_app, cloud_auth_dict, log_file, log_level, enable_cloud_client, enable_billing_client):
        # IMPORTS
        # EXIT CASES
        # HANDLER DEFAULTS
        #-- Load config file
        # CREATE CLIENT MAP
        #-- Create Concertim client
        #-- Create Cloud client
        #-- Create Billing client
        # CREATE HANDLER
        # RETURN HANDLER

# BILLING    
    @staticmethod
    def _build_billing_handler(cloud_type, billing_app, log_file, log_level, enable_cloud_client, enable_billing_client):
        # IMPORTS
        # EXIT CASES
        if not enable_billing_client:
            raise EXCP.MissingRequiredClient("A Billing Client is required for Billing Handler")
        if not enable_cloud_client:
            raise EXCP.MissingRequiredClient("A Cloud Client is required for Billing Handler")
        # HANDLER DEFAULTS
        #-- Load config file
        # CREATE CLIENT MAP
        #-- Create Concertim client
        #-- Create Cloud client
        #-- Create Billing client
        # CREATE HANDLER
        # RETURN HANDLER

# METRICS
    @staticmethod
    def _build_metrics_handler(cloud_type, billing_app, log_file, log_level, enable_cloud_client, enable_billing_client):
        # IMPORTS
        # EXIT CASES
        if not enable_cloud_client:
            raise EXCP.MissingRequiredClient("A Cloud Client is required for Metrics Handler")
        # HANDLER DEFAULTS
        #-- Load config file
        # CREATE CLIENT MAP
        #-- Create Concertim client
        #-- Create Cloud client
        #-- Create Billing client
        # CREATE HANDLER
        # RETURN HANDLER

# SYNC
    @staticmethod
    def _build_sync_handler(cloud_type, billing_app, log_file, log_level, enable_cloud_client, enable_billing_client):
        # IMPORTS
        # EXIT CASES
        if not enable_billing_client:
            raise EXCP.MissingRequiredClient("A Billing Client is required for Sync Handler")
        if not enable_cloud_client:
            raise EXCP.MissingRequiredClient("A Cloud Client is required for Sync Handler")
        # HANDLER DEFAULTS
        #-- Load config file
        # CREATE CLIENT MAP
        #-- Create Concertim client
        #-- Create Cloud client
        #-- Create Billing client
        # CREATE HANDLER
        # RETURN HANDLER

# QUEUE
    @staticmethod
    def _build_queue_handler(cloud_type, billing_app, log_file, log_level, enable_cloud_client, enable_billing_client):
        # IMPORTS
        # EXIT CASES
        if not enable_cloud_client:
            raise EXCP.MissingRequiredClient("A Cloud Client is required for Queue Handler")
        # HANDLER DEFAULTS
        #-- Load config file
        # CREATE CLIENT MAP
        #-- Create Concertim client
        #-- Create Cloud client
        #-- Create Billing client
        # CREATE HANDLER
        # RETURN HANDLER


###############################
#       CLIENT BUILDERS       #
###############################

# CLOUD
    @staticmethod
    def _build_cloud_client(cloud_type, cloud_config, log_file, log_level, components_list=None):
        # EXIT CASES
        if cloud_type not in Factory.CLIENT_OBJECTS['cloud']:
            raise EXCP.InvalidClient(cloud_type)

        # CLIENT CREATION TREE
        if cloud_type == "openstack":
            cloud_client = _build_openstack_client(
                openstack_config=cloud_config,
                components_list=components_list, 
                log_file=log_file, 
                log_level=log_level
            )
        
        # RETURN CLIENT
        return cloud_client

# BILLING    
    @staticmethod
    def _build_billing_client(billing_app, billing_config, log_file, log_level):
        # EXIT CASES
        if billing_app not in Factory.CLIENT_OBJECTS['billing']:
            raise EXCP.InvalidClient(billing_app)
        
        # CLIENT CREATION TREE
        if billing_app == "killbill":
            billing_client = _build_killbill_client(log_file, log_level)
        
        # RETURN CLIENT
        return billing_client


###############################
#          CLIENTs            #
###############################

# CONCERTIM
    @staticmethod
    def _build_concertim_client(concertim_config, log_file, log_level):
        # IMPORTS
        from conser.modules.clients.concertim.client import ConcertimClient
        # EXIT CASES
        if 'concertim_url' not in concertim_config
        or 'concertim_username' not in concertim_config
        or 'concertim_password' not in concertim_config:
            raise EXCP.MissingConfiguration('concertim_url', 'concertim_username', 'concertim_password')

        # CONCERTIM DEFAULTS
        # CREATE CLIENT
        concertim_client = ConcertimClient(
            concertim_config_dict=concertim_config, 
            log_file=log_file, 
            log_level=log_level
        )
        return concertim_client

# OPENSTACK
    @staticmethod
    def _build_openstack_client(openstack_config, components_list, log_file, log_level, billing_enabled=False):
        # IMPORTS
        from conser.modules.clients.cloud.openstack.client import OpenstackClient
        from conser.modules.clients.cloud.openstack.auth import OpenStackAuth
        # EXIT CASES
        for comp in components_list:
            if comp not in Factory.CLIENT_OBJECTS['cloud']['openstack']['components']:
                raise EXCP.InvalidComponent(comp)

        # OPENSTACK DEFAULTS
        DEFAULT_REQUIRED_KS_OBJS = {
            'domain': [],
            'role': ['admin', 'member', 'watcher'],
            'user': ['admin', 'concertim'],
            'project': []
        }

        #-- Create Keystone required objects
        keystone_objs = DEFAULT_REQUIRED_KS_OBJS
        if billing_enabled:
            keystone_objs['role'].append('rating')
            keystone_objs['user'].append('cloudkitty')

        #-- Create Components Dict
        sess = OpenStackAuth.get_session(openstack_config)   
        components_dict = {}
        for component_name in components_list:
            components_dict[component_name] = get_opstk_component(component_name, sess, log_file, log_level)

        # CREATE CLIENT
        #-- Create/Return Openstack Client
        opstk_client = OpenstackClient(
            openstack_config=openstack_config,
            components=components_dict
            log_file=log_file, 
            log_level=log_level, 
            required_ks_objs=keystone_objs
        )
        return opstk_client
    
# KILLBILL
    @staticmethod
    def _build_killbill_client(killbill_config, log_file, log_level):
        # IMPORTS
        from conser.modules.clients.billing.killbill.client import KillbillClient
        # EXIT CASES
        if 'api_host' not in concertim_config
        or 'username' not in concertim_config
        or 'password' not in concertim_config
        or 'apikey' not in concertim_config
        or 'apisecret' not in concertim_config
        or 'plan_name' not in concertim_config:
            raise EXCP.MissingConfiguration('api_host', 'username', 'password', 'apikey', 'apisecret', 'plan_name')

        # KILLBILL DEFAULTS
        # CREATE CLIENT
        kb_client = KillbillClient(
            killbill_config=killbill_config, 
            log_file=log_file, 
            log_level=log_level
        )
        return kb_client


###############################
#     OPENSTACK COMPONENTS    #
###############################

# KEYSTONE
    @staticmethod
    def _build_keystone_component(session_obj, log_file, log_level):
        # IMPORTS
        from conser.modules.clients.cloud.openstack.components.keystone import KeystoneComponent
        # CREATE/RETURN COMPONENT
        keystone_component = KeystoneComponent(session_obj, log_file, log_level)
        return keystone_component

# NOVA
    @staticmethod
    def _build_nova_component(session_obj, log_file, log_level):
        # IMPORTS
        from conser.modules.clients.cloud.openstack.components.nova import NovaComponent
        # CREATE/RETURN COMPONENT
        nova_component = NovaComponent(session_obj, log_file, log_level)
        return nova_component
        
# HEAT
    @staticmethod
    def _build_heat_component(session_obj, log_file, log_level):
        # IMPORTS
        from conser.modules.clients.cloud.openstack.components.heat import HeatComponent
        # CREATE/RETURN COMPONENT
        heat_component = HeatComponent(session_obj, log_file, log_level)
        return heat_component

# CLOUDKITTY
    @staticmethod
    def _build_cloudkitty_component(session_obj, log_file, log_level):
        # IMPORTS
        from conser.modules.clients.cloud.openstack.components.cloudkitty import CloudkittyComponent
        # CREATE/RETURN COMPONENT
        cloudkitty_component = CloudkittyComponent(session_obj, log_file, log_level)
        return cloudkitty_component

# GNOCCHI
    @staticmethod
    def _build_gnocchi_component(session_obj, log_file, log_level):
        # IMPORTS
        from conser.modules.clients.cloud.openstack.components.gnocchi import GnocchiComponent
        # CREATE/RETURN COMPONENT
        gnocchi_component = GnocchiComponent(session_obj, log_file, log_level)
        return gnocchi_component
        
