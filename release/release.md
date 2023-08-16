# Release Notes and Product Changes

### v0.1.0

#### New

- Added Dockerfiles for components
- Added examples for configuration / installation files
- Added example Openstack config files for Ceilometer
- Added Gnocchi SQL scripts for cleanup of database
- Added Gnocchi SQL script for archive-policy creation
- Added functionality to track Openstack Nova components and send the information to the Concertim UI
- Added functionality to track Openstack Heat components and send the information to the Concertim UI
- Added functionality to create Openstack Keystone components via the Concertim new user signup
- Added functionality to intercept RabbitMQ Notification messages for Openstack components
- Added functionality to gather metrics for Openstack resources from Openstack Gnocchi database
    - CPU load (%)
    - RAM usage (%)
    - Network usage (B/s)
    - Disk Throughput (B/s)
    - Disk IOPs (Ops/s)
- Added functionality to send data to Concertim endpoints dynamically - [endpoints](/concertim/components/endpoints.py)
- New infrastructure for handling data transformation logic
    - DataHandler
    - MetricHandler
- New infrastructure for handling user / project creation within Openstack based on data from Concertim
    - [/user_handler/user_handler.py](/user_handler/user_handler.py)
- New infrastructure for interacting with Openstack and Concertim
    - OpenstackService
    - ConcertimService
- New Infrastructure for handling Concertim objects
    - ConcertimDevice
    - ConcertimTemplate
    - ConcertimRack
    - ConcertimUser
    - ConcertimData
    - ConcertimMap
- New Infrastructure for interacting with Openstack components
    - GnocchiHandler
    - HeatHandler
    - NovaHandler
    - KeystoneHandler
    - OpenStackAuth

