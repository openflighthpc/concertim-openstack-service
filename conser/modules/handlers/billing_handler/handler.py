# Local Imports
from conser.utils.service_logger import create_logger
from conser.factory.abs_classes.handlers import Handler
import conser.exceptions as EXCP
import conser.utils.common as UTILS

# Py Packages
import time
from datetime import datetime, timedelta

class BillingHandler(AbsBillingHandler):
    ############
    # DEFAULTS #
    ############
    BILLING_INTERVAL = 300

    ########
    # INIT #
    ########
    def __init__(self, clients_dict, log_file, log_level):
        self._LOG_LEVEL = log_level
        self._LOG_FILE = log_file
        self.__LOGGER = create_logger(__name__, self._LOG_FILE, self._LOG_LEVEL)
        self.clients = clients_dict
        self.view = None

    #############################
    # BILLING HANDLER FUNCTIONS #
    #############################

    def pull_cost_data(self):
        self.__LOGGER.debug(f"Starting -- Pulling cost data from Cloud for all objects")
        # EXIT CASES
        if not self.view:
            self.__LOGGER.debug("No view data present - continuing at next interval")
            return

        # OBJECT LOGIC
        start_date = datetime.today().date().replace(day=1)
        end_date = (begin_date + timedelta(days=32)).replace(day=1)

        self.update_device_costs(start_date, end_date)
        self.update_rack_costs(start_date, end_date)
        self.update_user_costs_credits(start_date, end_date)
        
        self.__LOGGER.debug(f"Finished -- Pulling cost data from Cloud for all objects")

    def update_device_costs(self, start_date, end_date):
        self.__LOGGER.debug(f"Starting --- Updating cost data from Cloud for all devices")
        # OBJECT LOGIC
        #-- Loop over all billable devices and push cost data to concertim for each
        for device_id_tup, device in self.view.devices.items():
            containing_rack = self.view.racks[device.rack_id_tuple]
            owner = self.view.users[containing_rack.user_id_tuple]
            if not owner.id[2] or not containing_rack.id[2]:
                self.__LOGGER.debug(f"Device {device_id_tup} is not billable - Owner:{owner.id} Containing Rack:{containing_rack.id} - skipping")
                continue
            cost_dict = self.clients['cloud'].get_cost(
                obj_type='server',
                obj_cloud_id=device_id_tup[1],
                start=start_date,
                stop=end_date
            )
            self.view.devices[device_id_tup].cost = float(cost_dict['total_cost'])
            #-- Total device cost into containing rack cost
            self.view.racks[containing_rack.id].cost += float(cost_dict['total_cost'])
            for charge_type, amt in cost_dict['detailed_cost'].items():
                if charge_type in self.view.racks[containing_rack.id]._detailed_cost:
                    self.view.racks[containing_rack.id]._detailed_cost[charge_type] += amt
                else:
                    self.view.racks[containing_rack.id]._detailed_cost[charge_type] = amt
            #-- Push cost to concertim
            self.concertim_cost_update('device', self.view.devices[device_id_tup])
        self.__LOGGER.debug(f"Finished --- Updating cost data from Cloud for all devices")

    def update_rack_costs(self, start_date, end_date):
        self.__LOGGER.debug(f"Starting --- Updating cost data from Cloud for all racks")
        # OBJECT LOGIC
        #-- Loop over all billable racks and push cost data to concertim and billing app for each
        for rack_id_tup, rack in self.view.racks.items():
            owner = self.view.users[rack.user_id_tuple]
            if not owner.id[2] or not rack_id_tup[2]:
                self.__LOGGER.debug(f"Rack {rack_id_tup} is not billable - Owner:{owner.id} - skipping")
                continue
            #-- Cost has been totalled from updating device, just need to push the final amounts to billing/concertim
            #-- Push to concertim
            self.concertim_cost_update('rack', rack)
            #-- Push detailed cost to billing app
            self.billing_app_cost_update(rack)
        self.__LOGGER.debug(f"Finished --- Updating cost data from Cloud for all racks")

    def update_user_costs_credits(self, start_date, end_date):
        self.__LOGGER.debug(f"Starting --- Updating cost data from Cloud and billing credits for all users")
        # OBJECT LOGIC
        #-- Loop over all Users
        for user_id_tup in self.view.users:
            self.view.users[user_id_tup].billing_period_start = start_date
            self.view.users[user_id_tup].billing_period_end = end_date
            #-- Loop over all Teams
            for team_id_tup, team in self.view.teams.items():
                #-- If team is billable and user is it's primary billing user, get its cost and remaining credits
                if team._primary_billing_user_cloud_id != user_id_tup[1]:
                    continue
                if not team_id_tup[1] or not team_id_tup[2]:
                    self.__LOGGER.warning(f"Team {team_id_tup} is not billable - Primary User: {team._primary_billing_user_cloud_id} - skipping")
                    continue
                #-- Get team cloud cost
                team_cost_dict = self.clients['cloud'].get_cost(
                    obj_type='project', 
                    obj_cloud_id=team_id_tup[1], 
                    start=start_date, 
                    stop=end_date
                )
                #-- Get team remaining credits
                team_remaining_credits = self.clients['billing'].get_credits(
                    project_billing_id=team_id_tup[2]
                )['amount']
                #-- Update primary billing user's cost/credits
                self.view.users[user_id_tup].cost += float(team_cost_dict['total_cost'])
                self.view.users[user_id_tup].credits += float(team_remaining_credits)
            #-- Update User in Concertim
            self.concertim_cost_update(
                obj_type='user',
                obj=self.view.users[user_id_tup]
            )
        self.__LOGGER.debug(f"Finished --- Updating cost data from Cloud and billing credits for all users")

    def billing_app_cost_update(self, cluster_rack_obj):
        """
        Process for updating cost data in the Billing Application.
        """
        self.__LOGGER.debug(f"Updating cost in Billing App for {cluster_rack_obj.id}")
        for charge_type, amt in cluster_rack_obj._detailed_cost.items():
            try:
                self.clients['billing'].update_usage(
                    usage_metric_type=charge_type,
                    usage_metric_value=amt,
                    cluster_billing_id=cluster_rack_obj.id[2]
                )
            except Exception as e:
                self.__LOGGER.error(f"FAILED - Could not update cost in Billing App for rack.{cluster_rack_obj.id} - {e} - skipping")

    def concertim_cost_update(self, obj_type, obj):
        """
        Process for updating Concertim object costs.
        """
        obj_updates = {
            'device': [
                'cost'
            ],
            'rack': [
                'cost'
            ]
            'user': [
                'cost',
                'billing_period_start',
                'billing_period_end',
                'credits'
            ]
        }
        self.__LOGGER.debug(f"Updating cost in Concertim for {obj_type}.{obj.id}")
        if obj_type not in obj_updates:
            raise EXCP.InvalidArguments(f"obj_type:{obj_type}")
        v_dict = {}
        for field in obj_updates[obj_type]:
            v_dict[field] = getattr(obj, field)
        try:
            getattr(self.clients['concertim'], 'update_'+obj_type)(
                ID=obj.id[0],
                variables_dict=v_dict
            )
        except Exception as e:
            self.__LOGGER.error(f"FAILED - Could not update cost in Concertim for {obj_type}.{obj.id} - {e} - skipping")

    ##############################
    # HANDLER REQUIRED FUNCTIONS #
    ##############################

    def run_process(self):
        """
        The main running loop of the Handler.
        """
        self.__LOGGER.info(f"=====================================================================================\n" \
            f"Starting - Updating Concertim Front-end and Billing app with Usage and Billing data")
        # EXIT CASES
        if 'concertim' not in self.clients or not self.clients['concertim']:
            raise EXCP.NoClientFound('concertim')
        if 'cloud' not in self.clients or not self.clients['cloud']:
            raise EXCP.NoClientFound('cloud')
        if 'billing' not in self.clients or not self.clients['billing']:
            raise EXCP.NoClientFound('billing')

        #-- Load current view
        try:
            self.view = UTILS.load_view()
        except Exception as e:
            self.__LOGGER.error(f"Could not load view - waiting for next loop - {e}")

        self.pull_cost_data()

        time.sleep(BillingHandler.BILLING_INTERVAL)
        self.__LOGGER.info(f"Finished - Updating Concertim Front-end and Billing app with Usage and Billing data" \
            f"=====================================================================================\n\n")

    def disconnect(self):
        """
        Function for disconnecting all clients before garbage collection.
        """
        self.__LOGGER.info("Disconnecting Billing Clients and Components")
        for name, client in self.clients.items():
            client.disconnect()
        self.clients = None

    ###########################
    # BILLING HANDLER HELPERS #
    ###########################