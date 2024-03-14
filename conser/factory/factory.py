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
        "view_sync",
        "view_queue",
        "api",
        "fe_metrics",
        "fe_updates",
        "billing"
    ]
    CLIENT_OBJECTS = {
        "concertim": "concertim",
        "cloud": {
            "openstack": {
                "queues": [
                    "rmq"
                ],
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
    DEFAULT_CLOUD_COMPONENTS = {
        'api': {
            'openstack': ['keystone']
        },
        'billing': {
            'openstack': ['cloudkitty']
        },
        'fe_updates': {
            'openstack': []
        },
        'fe_metrics': {
            'openstack': ['gnocchi']
        },
        'view_sync': {
            'openstack': ['keystone', 'heat', 'nova']
        },
        'view_queue': {
            'openstack': []
        }

    }

###############################
#          MAIN GETs          #
###############################
    @staticmethod
    def get_handler(handler_type, config, log_file, cloud_auth_dict=None, cloud_components_list=None, enable_concertim_client=True, enable_cloud_client=True, enable_billing_client=True):
        """
        Returns a concrete implementation of the given handler configuration

        REQUIRED:
            handler_type : type of HANDLER_OBJECT
            config : the dict of the config file
            log_file : the string of the log file location/name
        OPTIONAL:
            cloud_auth_dict : an optional alternative cloud auth than what is in the config file (used for API)
            cloud_components_list : an optional list of cloud components to use for the cloud client (used for API)
            enable_cloud_client : flag to specify if handler needs a cloud client object
            enable_billing_client : flag to specify if a handler needs a billing client object
        """

        if handler_type not in Factory.HANDLER_OBJECTS:
            raise EXCP.InvalidHandler(handler_type)

        if handler_type == "api":
            handler = Factory._build_api_handler(config, cloud_auth_dict, cloud_components_list, log_file, enable_concertim_client, enable_cloud_client, enable_billing_client)
        elif handler_type == "billing":
            handler = Factory._build_billing_handler(config, log_file, enable_concertim_client, enable_cloud_client, enable_billing_client)
        elif handler_type == "fe_metrics":
            handler = Factory._build_metrics_handler(config, log_file, enable_concertim_client, enable_cloud_client, enable_billing_client)
        elif handler_type == "fe_updates":
            handler = Factory._build_updates_handler(config, log_file, enable_concertim_client, enable_cloud_client, enable_billing_client)
        elif handler_type == "view_sync":
            handler = Factory._build_sync_handler(config, log_file, enable_concertim_client, enable_cloud_client, enable_billing_client)
        elif handler_type == "view_queue":
            handler = Factory._build_queue_handler(config, log_file, enable_concertim_client, enable_cloud_client, enable_billing_client)
        else:
            raise EXCP.HandlerNotImplemented(handler_type)

        return handler

    @staticmethod
    def get_client(client_type, client_config, log_file, log_level, client_subtype=None, components_list=None, billing_enabled=False, mq_client=None, mq_config=None):
        """
        Returns a concrete implementation of the given client configuration

        REQUIRED:
            client_type : type of CLIENT_OBJECT (concertim, cloud, billing)
        OPTIONAL:
            client_subtype : if cloud or billing client - a name for the specific app is needed
            components_list : list of components to add for the client
        """

        if client_type not in Factory.CLIENT_OBJECTS:
            raise EXCP.InvalidClient(client_type)
        if client_type != 'concertim' and not client_subtype:
            raise EXCP.MissingRequiredArgs(f'client_subtype')

        if client_type == "concertim":
            client = Factory._build_concertim_client(client_config, log_file, log_level)
        elif client_type == "cloud":
            client = Factory._build_cloud_client(client_subtype, client_config, log_file, log_level, billing_enabled=billing_enabled, components_list=components_list, mq_client=mq_client, mq_config=mq_config)
        elif client_type == "billing":
            client = Factory._build_billing_client(client_subtype, client_config, log_file, log_level)
        else:
            raise EXCP.ClientNotImplemented(client_type)
        
        return client

    @staticmethod
    def get_opstk_component(component_name, session_obj, log_file, log_level, mq_config=None):
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
            component = Factory._build_keystone_component(session_obj, log_file, log_level)
        elif component_name == "nova":
            component = Factory._build_nova_component(session_obj, log_file, log_level)
        elif component_name == "heat":
            component = Factory._build_heat_component(session_obj, log_file, log_level)
        elif component_name == "gnocchi":
            component = Factory._build_gnocchi_component(session_obj, log_file, log_level)
        elif component_name == "cloudkitty":
            component = Factory._build_cloudkitty_component(session_obj, log_file, log_level)
        elif component_name == 'rmq':
            if not mq_config:
                raise EXCP.InvalidComponent(f"RMQ has no config passed")
            component = Factory._build_rmq_component(mq_config, log_file, log_level)
        else:
            raise EXCP.ComponentNotImplemented(f"{component_name}")

        return component


###############################
#       HANDLER BUILDERS      #
###############################

# API
    @staticmethod
    def _build_api_handler(config, cloud_auth_dict, cloud_components_list, log_file, enable_concertim_client, enable_cloud_client, enable_billing_client):
        # IMPORTS
        from conser.modules.handlers.api_handler.handler import APIHandler
        # EXIT CASES
        cloud_type = config['cloud_type']
        billing_app = config['billing_platform']
        if cloud_type not in Factory.CLIENT_OBJECTS['cloud']:
            raise EXCP.InvalidClient(cloud_type)
        if billing_app not in Factory.CLIENT_OBJECTS['billing']:
            raise EXCP.InvalidClient(billing_app)

        # HANDLER DEFAULTS
        log_level = config['log_level']
        if cloud_auth_dict:
            cloud_auth = cloud_auth_dict
        else:
            cloud_auth = config[cloud_type]
        cloud_comps = cloud_components_list if cloud_components_list else Factory.DEFAULT_CLOUD_COMPONENTS['api'][cloud_type]

        # CREATE CLIENT MAP
        #-- Create Concertim client
        if enable_concertim_client:
            concertim_client = Factory.get_client(
                'concertim',
                config['concertim'],
                log_file,
                log_level
            )
        else:
            concertim_client = None
        #-- Create Cloud client
        if enable_cloud_client:
            cloud_client = Factory.get_client(
                'cloud',
                cloud_auth,
                log_file,
                log_level,
                client_subtype=cloud_type,
                components_list=cloud_comps,
                billing_enabled=enable_billing_client
            )
        else:
            cloud_client = None
        #-- Create Billing client
        if enable_billing_client:
            billing_client = Factory.get_client(
                'billing',
                config[billing_app],
                log_file,
                log_level,
                client_subtype=billing_app
            )
        else:
            billing_client = None
        handler_clients = {
            'concertim': concertim_client,
            'cloud': cloud_client,
            'billing': billing_client
        }

        # CREATE HANDLER
        handler = APIHandler(
            handler_clients,
            log_file,
            log_level
        )

        # RETURN HANDLER
        return handler

# BILLING    
    @staticmethod
    def _build_billing_handler(config, log_file, enable_concertim_client, enable_cloud_client, enable_billing_client):
        # IMPORTS
        from conser.modules.handlers.billing_handler.handler import BillingHandler
        # EXIT CASES
        cloud_type = config['cloud_type']
        billing_app = config['billing_platform']
        if cloud_type not in Factory.CLIENT_OBJECTS['cloud']:
            raise EXCP.InvalidClient(cloud_type)
        if billing_app not in Factory.CLIENT_OBJECTS['billing']:
            raise EXCP.InvalidClient(billing_app)
        if not enable_concertim_client:
            raise EXCP.MissingRequiredClient("A Concertim Client is required for Billing Handler")
        if not enable_billing_client:
            raise EXCP.MissingRequiredClient("A Billing Client is required for Billing Handler")
        if not enable_cloud_client:
            raise EXCP.MissingRequiredClient("A Cloud Client is required for Billing Handler")

        # HANDLER DEFAULTS
        log_level = config['log_level']
        cloud_comps = Factory.DEFAULT_CLOUD_COMPONENTS['billing'][cloud_type]
        # CREATE CLIENT MAP
        #-- Create Concertim client
        concertim_client = Factory.get_client(
            'concertim',
            config['concertim'],
            log_file,
            log_level
        )
        #-- Create Cloud client
        cloud_client = Factory.get_client(
            'cloud',
            config[cloud_type],
            log_file,
            log_level,
            client_subtype=cloud_type,
            components_list=cloud_comps
        )
        #-- Create Billing client
        billing_client = Factory.get_client(
            'billing',
            config[billing_app],
            log_file,
            log_level,
            client_subtype=billing_app
        )
        handler_clients = {
            'concertim': concertim_client,
            'cloud': cloud_client,
            'billing': billing_client
        }

        # CREATE HANDLER
        handler = BillingHandler(
            handler_clients,
            log_file,
            log_level
        )

        # RETURN HANDLER
        return handler

# METRICS
    @staticmethod
    def _build_metrics_handler(config, log_file, enable_concertim_client, enable_cloud_client, enable_billing_client):
        # IMPORTS
        from conser.modules.handlers.frontend_handler.metrics.handler import MetricsHandler
        # EXIT CASES
        cloud_type = config['cloud_type']
        billing_app = config['billing_platform']
        if cloud_type not in Factory.CLIENT_OBJECTS['cloud']:
            raise EXCP.InvalidClient(cloud_type)
        if billing_app not in Factory.CLIENT_OBJECTS['billing']:
            raise EXCP.InvalidClient(billing_app)
        if not enable_concertim_client:
            raise EXCP.MissingRequiredClient("A Concertim Client is required for Metrics Handler")
        if not enable_cloud_client:
            raise EXCP.MissingRequiredClient("A Cloud Client is required for Metrics Handler")

        # HANDLER DEFAULTS
        log_level = config['log_level']
        cloud_comps = Factory.DEFAULT_CLOUD_COMPONENTS['fe_metrics'][cloud_type]
        # CREATE CLIENT MAP
        #-- Create Concertim client
        concertim_client = Factory.get_client(
            'concertim',
            config['concertim'],
            log_file,
            log_level
        )
        #-- Create Cloud client
        cloud_client = Factory.get_client(
            'cloud',
            config[cloud_type],
            log_file,
            log_level,
            client_subtype=cloud_type,
            components_list=cloud_comps
        )
        #-- Create Billing client
        if enable_billing_client:
            billing_client = Factory.get_client(
                'billing',
                config[billing_app],
                log_file,
                log_level,
                client_subtype=billing_app
            )
        else:
            billing_client = None
        handler_clients = {
            'concertim': concertim_client,
            'cloud': cloud_client,
            'billing': billing_client
        }

        # CREATE HANDLER
        handler = MetricsHandler(
            handler_clients,
            log_file,
            log_level
        )

        # RETURN HANDLER
        return handler

# UPDATES
    @staticmethod
    def _build_updates_handler(config, log_file, enable_concertim_client, enable_cloud_client, enable_billing_client):
        # IMPORTS
        from conser.modules.handlers.frontend_handler.updates.handler import UpdatesHandler
        # EXIT CASES
        cloud_type = config['cloud_type']
        billing_app = config['billing_platform']
        if cloud_type not in Factory.CLIENT_OBJECTS['cloud']:
            raise EXCP.InvalidClient(cloud_type)
        if billing_app not in Factory.CLIENT_OBJECTS['billing']:
            raise EXCP.InvalidClient(billing_app)
        if not enable_concertim_client:
            raise EXCP.MissingRequiredClient("A Concertim Client is required for Updates Handler")

        # HANDLER DEFAULTS
        log_level = config['log_level']
        cloud_comps = Factory.DEFAULT_CLOUD_COMPONENTS['fe_updates'][cloud_type]
        # CREATE CLIENT MAP
        #-- Create Concertim client
        concertim_client = Factory.get_client(
            'concertim',
            config['concertim'],
            log_file,
            log_level
        )
        #-- Create Cloud client
        cloud_client = None
        #-- Create Billing client
        billing_client = None
        handler_clients = {
            'concertim': concertim_client,
            'cloud': cloud_client,
            'billing': billing_client
        }

        # CREATE HANDLER
        handler = UpdatesHandler(
            handler_clients,
            log_file,
            log_level
        )

        # RETURN HANDLER
        return handler

# SYNC
    @staticmethod
    def _build_sync_handler(config, log_file, enable_concertim_client, enable_cloud_client, enable_billing_client):
        # IMPORTS
        from conser.modules.handlers.view_handler.sync.handler import SyncHandler
        # EXIT CASES
        cloud_type = config['cloud_type']
        billing_app = config['billing_platform']
        if cloud_type not in Factory.CLIENT_OBJECTS['cloud']:
            raise EXCP.InvalidClient(cloud_type)
        if billing_app not in Factory.CLIENT_OBJECTS['billing']:
            raise EXCP.InvalidClient(billing_app)
        if not enable_concertim_client:
            raise EXCP.MissingRequiredClient("A Concertim Client is required for Sync Handler")
        if not enable_billing_client:
            raise EXCP.MissingRequiredClient("A Billing Client is required for Sync Handler")
        if not enable_cloud_client:
            raise EXCP.MissingRequiredClient("A Cloud Client is required for Sync Handler")

        # HANDLER DEFAULTS
        log_level = config['log_level']
        cloud_comps = Factory.DEFAULT_CLOUD_COMPONENTS['view_sync'][cloud_type]
        # CREATE CLIENT MAP
        #-- Create Concertim client
        concertim_client = Factory.get_client(
            'concertim',
            config['concertim'],
            log_file,
            log_level
        )
        #-- Create Cloud client
        cloud_client = Factory.get_client(
            'cloud',
            config[cloud_type],
            log_file,
            log_level,
            client_subtype=cloud_type,
            components_list=cloud_comps
        )
        #-- Create Billing client
        billing_client = Factory.get_client(
            'billing',
            config[billing_app],
            log_file,
            log_level,
            client_subtype=billing_app
        )
        handler_clients = {
            'concertim': concertim_client,
            'cloud': cloud_client,
            'billing': billing_client
        }

        # CREATE HANDLER
        handler = SyncHandler(
            handler_clients,
            log_file,
            log_level
        )

        # RETURN HANDLER
        return handler

# QUEUE
    @staticmethod
    def _build_queue_handler(config, log_file, enable_concertim_client, enable_cloud_client, enable_billing_client):
        # IMPORTS
        from conser.modules.handlers.view_handler.queue.handler import QueueHandler
        # EXIT CASES
        if 'message_queue' not in config:
            raise MissingConfiguration('message_queue')
        cloud_type = config['cloud_type']
        queue_type = config['message_queue']
        if cloud_type not in Factory.CLIENT_OBJECTS['cloud']:
            raise EXCP.InvalidClient(cloud_type)
        if queue_type not in Factory.CLIENT_OBJECTS['cloud'][cloud_type]['queues']:
            raise EXCP.InvalidClient(f"{cloud_type}.{queue_type}")
        if not enable_cloud_client:
            raise EXCP.MissingRequiredClient("A Cloud Client is required for Queue Handler")

        # HANDLER DEFAULTS
        log_level = config['log_level']
        cloud_comps = Factory.DEFAULT_CLOUD_COMPONENTS['view_queue'][cloud_type]
        # CREATE CLIENT MAP
        #-- Create Concertim client
        concertim_client = None
        #-- Create Cloud client
        cloud_client = Factory.get_client(
            'cloud',
            config[cloud_type],
            log_file,
            log_level,
            client_subtype=cloud_type,
            components_list=cloud_comps,
            mq_client=queue_type,
            mq_config=config[queue_type]
        )
        #-- Create Billing client
        billing_client = None

        handler_clients = {
            'concertim': concertim_client,
            'cloud': cloud_client,
            'billing': billing_client
        }

        # CREATE HANDLER
        handler = QueueHandler(
            handler_clients,
            log_file,
            log_level
        )

        # RETURN HANDLER
        return handler


###############################
#       CLIENT BUILDERS       #
###############################

# CLOUD
    @staticmethod
    def _build_cloud_client(cloud_type, cloud_config, log_file, log_level, components_list=None, billing_enabled=False, mq_client=None, mq_config=None):
        # EXIT CASES
        if cloud_type not in Factory.CLIENT_OBJECTS['cloud']:
            raise EXCP.InvalidClient(cloud_type)
        if mq_client:
            if not mq_config:
                raise EXCP.InvalidComponent(f"Cloud Message Queue component has no config passed")

        # CLIENT CREATION TREE
        if cloud_type == "openstack":
            cloud_client = Factory._build_openstack_client(
                openstack_config=cloud_config,
                components_list=components_list, 
                log_file=log_file, 
                log_level=log_level,
                billing_enabled=billing_enabled,
                mq_client=mq_client,
                mq_config=mq_config
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
            billing_client = Factory._build_killbill_client(billing_config, log_file, log_level)
        
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
        if 'concertim_url' not in concertim_config \
        or 'concertim_username' not in concertim_config \
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
    def _build_openstack_client(openstack_config, components_list, log_file, log_level, billing_enabled=False, mq_client=None, mq_config=None):
        # IMPORTS
        from conser.modules.clients.cloud.openstack.client import OpenstackClient
        from conser.modules.clients.cloud.openstack.auth import OpenStackAuth
        # EXIT CASES
        for comp in components_list:
            if comp not in Factory.CLIENT_OBJECTS['cloud']['openstack']['components']:
                raise EXCP.InvalidComponent(f"openstack.{comp}")
        if mq_client:
            if mq_client not in Factory.CLIENT_OBJECTS['cloud']['openstack']['queues']:
                raise EXCP.InvalidComponent(f"openstack.queue.{mq_client}")
            mq_comp = Factory.get_opstk_component(
                component_name=mq_client, 
                session_obj=None, 
                log_file=log_file, 
                log_level=log_level, 
                mq_config=mq_config
            )
            opstk_client = OpenstackClient(
                openstack_config=openstack_config,
                components={'mq': mq_comp},
                log_file=log_file, 
                log_level=log_level, 
                required_ks_objs=None
            )
            return opstk_client

        # OPENSTACK DEFAULTS
        DEFAULT_REQUIRED_KS_OBJS = {
            'domain': [],
            'role': ['admin', 'member', 'watcher'],
            'user': ['admin', 'concertim'],
            'project': []
        }

        #-- Create Keystone required objects
        keystone_objs = {}

        #-- Create Components Dict

        sess = OpenStackAuth.get_session(openstack_config)   
        components_dict = {}
        for component_name in components_list:
            if component_name == 'keystone':
                keystone_objs = DEFAULT_REQUIRED_KS_OBJS
            components_dict[component_name] = Factory.get_opstk_component(component_name, sess, log_file, log_level)

        if billing_enabled and keystone_objs:
            keystone_objs['role'].append('rating')
            keystone_objs['user'].append('cloudkitty')

        # CREATE CLIENT
        #-- Create/Return Openstack Client
        opstk_client = OpenstackClient(
            openstack_config=openstack_config,
            components=components_dict,
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
        if 'api_host' not in killbill_config \
        or 'username' not in killbill_config \
        or 'password' not in killbill_config \
        or 'apikey' not in killbill_config \
        or 'apisecret' not in killbill_config \
        or 'plan_name' not in killbill_config:
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
        
# RMQ
    @staticmethod
    def _build_rmq_component(mq_config, log_file, log_level):
        # IMPORTS
        from conser.modules.clients.cloud.openstack.components.rmq import RMQComponent
        # CREATE/RETURN COMPONENT
        rmq_component = RMQComponent(mq_config, log_file, log_level)
        return rmq_component
        
