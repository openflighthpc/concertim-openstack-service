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
from conser.utils.service_logger import create_logger
from conser.factory.abs_classes.handlers import AbsBillingHandler
import conser.exceptions as EXCP
import conser.utils.common as UTILS

# Py Packages
import math
import time
from datetime import datetime, timedelta

class BillingHandler(AbsBillingHandler):
    ############
    # DEFAULTS #
    ############
    BILLING_INTERVAL = 60

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
        end_date = (start_date + timedelta(days=32)).replace(day=1)

        self.update_device_costs(start_date, end_date)
        self.update_rack_costs(start_date, end_date)
        self.update_team_costs_credits(start_date, end_date)
        
        self.__LOGGER.debug(f"Finished -- Pulling cost data from Cloud for all objects")

    def update_device_costs(self, start_date, end_date):
        self.__LOGGER.debug(f"Starting --- Updating cost data from Cloud for all devices")
        # OBJECT LOGIC
        #-- Loop over all billable devices and push cost data to concertim for each
        for device_id_tup, device in self.view.devices.items():
            containing_rack = self.view.racks[device.rack_id_tuple]
            owner = self.view.teams[containing_rack.team_id_tuple]
            if not owner.id[2] or not containing_rack.id[2]:
                self.__LOGGER.debug(f"Device {device_id_tup} is not billable - Owner:{owner.id} Containing Rack:{containing_rack.id} - skipping")
                continue
            cost_dict = self.clients['cloud'].get_cost(
                obj_type='server',
                obj_cloud_id=device_id_tup[1],
                start=start_date,
                stop=end_date
            )
            original_cost = self.view.devices[device_id_tup].cost
            self.view.devices[device_id_tup].cost = float(cost_dict['total_cost'])
            #-- Total device cost into containing rack cost
            self.view.racks[containing_rack.id].cost += float(cost_dict['total_cost'])
            for charge_type, amt in cost_dict['detailed_cost'].items():
                if charge_type in self.view.racks[containing_rack.id]._detailed_cost:
                    self.view.racks[containing_rack.id]._detailed_cost[charge_type] += amt
                else:
                    self.view.racks[containing_rack.id]._detailed_cost[charge_type] = amt

            if original_cost == self.view.devices[device_id_tup].cost:
                continue

            self.__LOGGER.debug(f"Cost changed: from {original_cost} to {self.view.devices[device_id_tup].cost}")
            #-- Push cost to concertim
            device =  self.view.devices[device_id_tup]
            if device.type == "Instance":
                type = "compute_device"
            elif device.type == "Volume":
                type = "volume_device"
            elif device.type == "Network":
                type = "network_device"
            self.concertim_cost_update(type, self.view.devices[device_id_tup])
        self.__LOGGER.debug(f"Finished --- Updating cost data from Cloud for all devices")

    def update_rack_costs(self, start_date, end_date):
        self.__LOGGER.debug(f"Starting --- Updating cost data from Cloud for all racks")
        # OBJECT LOGIC
        #-- Loop over all billable racks and push cost data to concertim and billing app for each
        for rack_id_tup, rack in self.view.racks.items():
            owner = self.view.teams[rack.team_id_tuple]
            if not owner.id[2] or not rack_id_tup[2]:
                self.__LOGGER.debug(f"Rack {rack_id_tup} is not billable - Owner:{owner.id} - skipping")
                continue
            #-- Cost has been totalled from updating device, just need to push the final amounts to billing/concertim
            #-- Push to concertim
            self.concertim_cost_update('rack', rack)
            #-- Push detailed cost to billing app
            self.billing_app_cost_update(rack)
        self.__LOGGER.debug(f"Finished --- Updating cost data from Cloud for all racks")

    def update_team_costs_credits(self, start_date, end_date):
        self.__LOGGER.debug(f"Starting --- Updating cost data from Cloud and billing credits for all teams")
        # OBJECT LOGIC
        #-- Loop over all teams
        for team_id_tup in self.view.teams:
            if not team_id_tup[1] or not team_id_tup[2]:
                self.__LOGGER.warning(f"Team {team_id_tup} is not billable - skipping")
                continue
            self.view.teams[team_id_tup].billing_period_start = start_date
            self.view.teams[team_id_tup].billing_period_end = end_date

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

            # Some queries return rounded costs, some not - rounding cost here makes slightly more consistent
            self.view.teams[team_id_tup].cost = math.ceil(float(team_cost_dict['total_cost']))
            self.view.teams[team_id_tup].credits = float(team_remaining_credits)
            #-- Update team in Concertim
            self.concertim_cost_update(
                obj_type='team',
                obj=self.view.teams[team_id_tup]
            )
        self.__LOGGER.debug(f"Finished --- Updating cost data from Cloud and billing credits for all teams")

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
            'compute_device': [
                'cost'
            ],
            'volume_device': [
                'cost'
            ],
            'network_device': [
                'cost'
            ],
            'rack': [
                'cost'
            ],
            'team': [
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
        self.__LOGGER.info(f"=====================================================================================")
        self.__LOGGER.info(f"Starting - Updating Concertim Front-end and Billing app with Usage and Billing data")
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

        self.__LOGGER.info(f"Finished - Updating Concertim Front-end and Billing app with Usage and Billing data")
        self.__LOGGER.info(f"=====================================================================================\n\n")
        time.sleep(BillingHandler.BILLING_INTERVAL)

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