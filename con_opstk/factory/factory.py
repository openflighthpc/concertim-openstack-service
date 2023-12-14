# Local Imports
from con_opstk.utils.service_logger import create_logger
import con_opstk.app_definitions as app_paths
import con_opstk.factory.handlers as HANDLERS
import con_opstk.factory.services as SERVICES
import con_opstk.factory.exceptions as EXCP

# Python Imports
import importlib

class Factory(object):
    """
    Object for building the correct Handler Object with all
    Service objects.
    """

    HANDLER_OBJECTS = {
        "update_bulk": con_opstk.modules.handlers.update_handler.bulk.state_compare.BulkUpdateHandler,
        "update_mq": con_opstk.modules.handlers.update_handler.mq.mq_listener.MqUpdateHandler,
        "api": con_opstk.modules.handlers.api_handler.api_handler.APIHandler,
        "metric": con_opstk.modules.handlers.metric_handler.metric_handler.MetricHandler,
        "billing": con_opstk.modules.handlers.billing_handler.billing_handler.BillingHandler
    }
    SERVICE_OBJECTS = {
        "concertim": con_opstk.modules.services.concertim.concertim.Concertim,
        "cloud": {
            "openstack": {
                "service": con_opstk.modules.services.cloud.openstack.openstack.OpenstackService,
                "component": {
                    "cloudkitty": con_opstk.modules.services.cloud.openstack.components.cloudkitty.CloudkittyComponent,
                    "gnocchi": con_opstk.modules.services.cloud.openstack.components.gnocchi.GnocchiComponent,
                    "heat": con_opstk.modules.services.cloud.openstack.components.heat.HeatComponent,
                    "keystone": con_opstk.modules.services.cloud.openstack.components.keystone.KeystoneComponent,
                    "nova": con_opstk.modules.services.cloud.openstack.components.nova.NovaComponent
                }
            }
        },
        "billing": {
            "killbill": con_opstk.modules.services.billing.killbill.killbill.KillbillService
        }
    }

    @staticmethod
    def build_handler(handler_type):
        pass

    @staticmethod
    def build_service(service_type, service_name=None, components_list=None):
        if service_type not in Factory.SERVICE_OBJECTS:
            raise EXCP.InvalidService(service_type)
        if service_name and service_name not in Factory.SERVICE_OBJECTS[service_type]:
            raise EXCP.InvalidService(f"{service_type} : {service_name}")
        if components_list:
            for component in components_list:
                if component not in Factory.SERVICE_OBJECTS[service_type][service_name][component]:
                    raise EXCP.InvalidComponent(f"{service_name} : {component}")

        
        

        
