# Concertim Openstack Service

The Concertim Openstack Service is a Python daemon process that sends metric and usage data from OpenStack resources to a REST API owned by the application 'CONCERTIM'. The program uses the Gnocchi client to poll all available resources in the OpenStack build and sends the metric data to CONCERTIM at a specific interval. The 'device' has a unique identifier in both the CONCERTIM and OpenStack backends, which is used to match and filter the data.

## Configuration

The configuration for the Concertim Openstack Service is stored in the `/etc/concertim-openstack-service/config.json` file. This file contains the following configuration data:

- `auth_url`: URL for the OpenStack authentication endpoint
- `username`: Username for authenticating with OpenStack
- `password`: Password for authenticating with OpenStack
- `project_name`: Name of the OpenStack project
- `project_domain_name`: Name of the domain for the OpenStack project
- `user_domain_name`: Name of the domain for the OpenStack user
- `gnocchi_url`: URL for the Gnocchi API endpoint
- `concertim_url`: URL for the Concertim API endpoint

## Installation

1. Clone the repository: `git clone https://github.com/username/concertim-service.git`
2. Install the required packages: `pip install -r <path_to_concertim_service>/requirements.txt`

## Usage

To run the Concertim Openstack Service as a systemd service:

1. Create a new file named `concertim.service` in the `/etc/systemd/system/` directory with the following contents:

```
[Unit]
Description=Concertim Openstack Service
After=network.target

[Service]
User=<user>
Group=<group>
WorkingDirectory=<path_to_concertim_service>
ExecStart=<path_to_python> <path_to_concertim_service>/concertim_service.py
Restart=always
RestartSec=5s

[Install]
WantedBy=multi-user.target
```

2. Replace `<user>`, `<group>`, `<path_to_concertim_service>`, and `<path_to_python>` with the appropriate values for your system. Note that `<path_to_python>` should be the path to your Python executable.
3. Reload the systemd daemon: `sudo systemctl daemon-reload`
4. Start the Concertim Openstack Service: `sudo systemctl start concertim.service`
5. Verify that the service is running: `sudo systemctl status concertim.service`
6. Enable the service to start on boot: `sudo systemctl enable concertim.service`
7. To stop the service, run: `sudo systemctl stop concertim.service`
8. To disable the service from starting on boot, run: `sudo systemctl disable concertim.service`

Note that the Concertim Openstack Service logs will be written to the `/var/logs/concertim-openstack-service.log` file as configured in the `/etc/concertim-openstack-service/config.json` file.

The service will run indefinitely, sending metric data to the Concertim API at the interval specified in the configuration file. Log data is stored in the `/var/logs/concertim-openstack-service.log` file.

## Changing Configuration

To change the configuration for the Concertim Openstack Service, modify the `/etc/concertim-openstack-service/config.json` file. 

Note that any changes made to the configuration file will only take effect when the Concertim Openstack Service is restarted.
