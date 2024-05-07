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

# Custom Exceptions
###  DRIVER
class MissingConfiguration(Exception):
    def __init__(self, *args):
        self.missing = args
    def __str__(self):
        return f"Missing required fields in config.yaml file -> Missing [{self.missing}]"


### API SERVER
class APIServerDefError(Exception):
    def __init__(self, msg, code):
        self.message = msg
        self.http_status = code
    def __str__(self):
        return f"{self.http_status} - API Server failed -> {self.message}"

class MissingRequiredArgument(Exception):
    def __init__(self, msg):
        self.message = msg
        self.http_status = 415
    def __str__(self):
        return f"{self.http_status} - Call to API is missing required argument(s) -> {self.message}"

class APIAuthenticationError(Exception):
    def __init__(self, msg):
        self.message = msg
        self.http_status = 401
    def __str__(self):
        return f"{self.http_status} - API Could not authenticate with Concertim -> {self.message}"

class InvalidAPICall(Exception):
    def __init__(self, msg):
        self.message = msg
        self.http_status = 406
    def __str__(self):
        return f"{self.http_status} - Invalid API call attempted -> {self.message}"


### FACTORY
class InvalidClient(Exception):
    def __init__(self, msg):
        self.message = msg
    def __str__(self):
        return f"Invalid Client type attempted -> {self.message}"

class InvalidComponent(Exception):
    def __init__(self, msg):
        self.message = msg
    def __str__(self):
        return f"Invalid Component type attempted -> {self.message}"

class InvalidHandler(Exception):
    def __init__(self, msg):
        self.message = msg
    def __str__(self):
        return f"Invalid Handler type attempted -> {self.message}"

class HandlerNotImplemented(Exception):
    def __init__(self, msg):
        self.message = msg
    def __str__(self):
        return f"Could not find Handler -> {self.message}"

class ClientNotImplemented(Exception):
    def __init__(self, msg):
        self.message = msg
    def __str__(self):
        return f"Could not find Client -> {self.message}"

class ComponentNotImplemented(Exception):
    def __init__(self, msg):
        self.message = msg
    def __str__(self):
        return f"Could not find Component -> {self.message}"

class MissingRequiredClient(InvalidHandler):
    def __init__(self, msg):
        self.message = msg
    def __str__(self):
        return f"Missing Required Client for given Handler -> {self.message}"



### CLOUD
class CloudAuthenticationError(Exception):
    def __init__(self, msg):
        self.message = msg
        self.http_status = 401
    def __str__(self):
        return f"{self.http_status} - Could not authenticate with Cloud -> {self.message}"

class MissingCloudObject(Exception):
    def __init__(self, msg):
        self.message = msg
    def __str__(self):
        return f"Could not find object in Cloud -> {self.message}"

class MissingRequiredCloudObject(MissingCloudObject):
    def __init__(self, msg):
        self.message = msg
    def __str__(self):
        return f"Missing Required Cloud Object for attempted action -> {self.message}"

class UnknownCloudComponent(Exception):
    def __init__(self, msg):
        self.message = msg
    def __str__(self):
        return f"Cannot resolve Cloud Component -> {self.message}"

class UnsupportedObject(Exception):
    def __init__(self, msg):
        self.message = msg
    def __str__(self):
        return f"USUPPORTED -> {self.message}"

class FailureToScrub(Exception):
    def __init__(self, msg):
        self.message = msg
    def __str__(self):
        return f"Failed to scrub objects -> {self.message}"

class NoComponentFound(Exception):
    def __init__(self, *args):
        self.missing_handlers = args
    def __str__(self):
        return f"Client Components(s) Not Found -> Missing [{self.missing_handlers}]"

class InvalidArguments(Exception):
    def __init__(self, *args):
        self.missing = args
    def __str__(self):
        return f"Invalid arguments were passed to call -> [{self.missing}]"

class MissingResourceMetric(Exception):
    def __init__(self, msg):
        self.message = msg
    def __str__(self):
        return f"Could not find metric for given resource -> {self.message}"


### HANDLER SPECIFIC
class ViewNotFound(Exception):
    def __init__(self, msg):
        self.message = msg
    def __str__(self):
        return f"Could not find View object; please check containers -> {self.message}"

class NoClientFound(Exception):
    def __init__(self, *args):
        self.missing_clients = args
    def __str__(self):
        return f"Client Not Found -> Missing [{self.missing_clients}]"

class TooManyBillingOrders(Exception):
    def __init__(self, msg):
        self.message = msg
    def __str__(self):
        return f"Cluster ID returned too many billing Orders -> {self.message}"

class TooManyBillingAccounts(Exception):
    def __init__(self, msg):
        self.message = msg
    def __str__(self):
        return f"Project ID returned too many billing Accounts -> {self.message}"


### CONCERTIM
class ConcertimItemConflict(Exception):
    def __init__(self, msg):
        self.message = msg
    def __str__(self):
        return f"Item already existing in Concertim for given ID -> {self.message}"

class MissingRequiredField(Exception):
    def __init__(self, msg):
        self.message = msg
    def __str__(self):
        return f"Missing required field for Concertim -> {self.message}"

class MissingRequiredArgs(Exception):
    def __init__(self, *args):
        self.missing = args
    def __str__(self):
        return f"Missing required argument(s) for call -> Missing [{self.missing}]"

class InvalidSearchAttempt(Exception):
    def __init__(self, msg):
        self.message = msg
    def __str__(self):
        return f"Search attempted with invalid field -> {self.message}"


### BILLING
class BillingAPIError(Exception):
    def __init__(self, msg):
        self.message = msg
    def __str__(self):
        return f"Billing API Error -> {self.message}"

class BillingAPIFailure(Exception):
    def __init__(self, msg, code):
        self.message = msg
        self.http_status = code
    def __str__(self):
        return f"Billing API Call failed -> {self.message}"