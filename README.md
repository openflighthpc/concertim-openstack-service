# Concertim Openstack Service

The Concertim-Openstack Service is a package of python modules intended to facilitate the communication between an Openstack cloud, a generic billing application, and an Alces Flight Ltd. Concertim application. The Concertim-Openstack package handles multiple aspects of the data communication pipeline between Openstack, Billing, and Concertim - including data retrieval, data transfomation, and manipulation of Billing, Concertim, and Openstack objects.

There are 3 main components within the Concertim-Openstack Service package: User Handler, Mertics Handler, and Update Handler.
- [API Server/Handler](/docs/api_handler.md) - Resposible for receiving REST requests from other services and performing back end actions in Openstack and Concertim
- [Metrics Handler](/docs/metrics.md) - Manages polling, calculating, and sending of Openstack resource metrics to the Concertim app
- [Update Handler](/docs/update_handler.md) - Manages collecting, transforming, and sending Openstack updates to the Concertim front-end UI - a two part service that contains both the `bulk_update_handler` and the `mq_update_handler`
- [Billing Handler](/docs/billing.md) - A collection of functions that manages interations between the chosen billing application and other services.

Each individual component is **highly recommended** to run in seperate Docker containers on the Openstack host, however admins that are familiar with these types of environments may wish to alter the setup. This README assumes the recommended setup method. 

This service is a package that is intended for use with the Alces Flight Cluster Portal product, but can be forked and expanded to fit other requirements.

## Installation

These instructions assume the recommended way of setting up the Concertim-Openstack service (Docker containers)

1. Clone the repository
    ```
    git clone https://<user>@github.com/alces-flight/concertim-openstack-service.git
    ```
2. Install `Docker` if not already installed

For Non-Docker ENVs:

3. Install `python3.8+` if not already installed
4. Install the package
    ```
    python3 setup.py build
    python3 setup.py install
    ```

If **Killbill** is being used as the Billing App (default):

5. Clone the [Alces fork of the Killbill API Client](https://github.com/alces-flight/killbill_fork) into the Conceritm-Openstack billing directory
    ```
    cd concertim-openstack-service/con_opstk/billing/killbill/
    git clone https://<user>@github.com/alces-flight/killbill_fork.git
    ```

## Configuration

NOTE: This configuration is for the service as a whole - please see the [individual component docs](/docs/) for more detailed configuration instructions for each component.

### Openstack

The Concertim-Openstack package was developed and tested using the Openstack `Yoga` release deployed via [kolla-ansible](https://docs.openstack.org/kolla-ansible/yoga/user/quickstart.html#).

The minimum requirements for the Openstack Cloud configuration requires some extra Openstack modules to be installed:

- [Openstack Telemetry](https://docs.openstack.org/ceilometer/yoga/) (Ceilometer)
- [Openstack Rating](https://docs.openstack.org/cloudkitty/yoga/) (Cloudkitty)
- A time-seriese database for storing metrics (The default and **recommended** databse is [Gnocchi](https://gnocchi.osci.io/))
- [Openstack Orchestration](https://docs.openstack.org/heat/yoga/) (Heat)

There is also support for more customizable clustering options through use of

- [Openstack Data Processing](https://docs.openstack.org/sahara/yoga/) (Sahara)
- [Openstack Containerization](https://docs.openstack.org/magnum/yoga/) (Magnum)

Each component in the Concertim-Openstack sesrvice makes use of various openstack objects for tracking Concertim-managed systems. To achieve this, the following need to be presesnt in Openstack:

- Openstack Role : `watcher` - Concertim Manager
- Openstack User : `concertim` - Concertim Manager
- Openstack Role : `rating` - Cloudkitty Role
- Openstack User : `cloudkitty` - Cloudkitty User

### Host Server Env

As of the current release, configuration of the Concertim-Openstack service is managaed through use of a `config.yaml` file that is read upon execution of the individual components. The configuration file for the Concertim-Openstack Service should be stored in the path `/etc/concertim-openstack-service/config.yaml`. ([Example config.yaml](/etc/config-sample.yaml))

#### Required Values

The minimum requirement of the Concertim-Openstack service calls for an Openstack environment, a Billing Application, and an Alces Flight Ltd. Concertim deployment to be correctly deployed and configured. The service needs the following values for this:

##### **Global Values**

Values with no header:

- `log_level` : Desired logging level (debug, info, error... etc.)
- `billing_platform` : The configure billing app to use

##### **Openstack Values**

###### AUTH

In order for the service to connect to the openstack deployment, authentication data is required. A `keystoneauth1.identity.[v3,v2].password.Password` object is used to authenticate against the keystone service and can accept any variation of password-based authentication ([accepted value sets source](/openstack/opstk_auth.py))

Values under the `openstack` header:

- `auth_url` : URL for the OpenStack authentication endpoint

  PLUS ONE OF THE FOLLOWING SETS:

1. Name-based authentication
    - `username` : Username for authenticating with OpenStack - recommended to use an admin user
    - `password` : Password for authenticating with OpenStack
    - `project_name` : Namme of the OpenStack project - recommended to use an admin project
    - `project_domain_name` : Name of the domain for the OpenStack project
    - `user_domain_name` : Name of the domain for the OpenStack user
2. ID-based authentication
    - `user_id` : User ID for authenticating with OpenStack - recommended to use an admin user
    - `password` : Password for authenticating with OpenStack
    - `project_id` : ID of the OpenStack project - recommended to use an admin project

###### RABBIT MQ

The [Update Handler](/docs/updater.md) listens to the Openstack Rabbit MQ messaging queue to catch updates that happen in the openstack backend. RabbitMQ requires its own auth details.

- `rmq_username` : The username for the Openstack notification queue inside RabbitMQ (default is `openstack`)
- `rmq_password` : The password for the RabbitMQ user
- `rmq_address` : The IP of the RabbitMQ host
- `rmq_port` : Port that RabbitMQ is running on
- `rmq_path` : RabbitMQ message path (default is `/`)

##### **Concertim Values**

The service send data to the Concretim front end via REST requests, authentication data is neeeded to be passed in the header of the requests. 

Values under the `concertim` header:

- `concertim_url` : URL for the Concertim API endpoint
- `concertim_username` : Admin Username for authenticating with Concertim
- `concertim_password` : Admin Password for authenticating with Concertim
- `default_rack_height` : Default rack height for newly created racks (racks will scale up if needed)

##### **Billing Values**

These will change depending on the configure billing application, please see the [billing](docs/billing.md) docs for the selected billing app for more information.

##### **Optional Values**

- `sleep_timer` : Override for the defulat sleep amount (10s) for the billing_handler

### Changing Configuration

To change the configuration for the Concertim Openstack Service, modify the `/etc/concertim-openstack-service/config.yaml` file. 

Note that any changes made to the configuration file will only take effect when the Concertim Openstack Service is restarted.

## Usage

### Docker

The recommended method for using the Concertim-Openstack service is by deploying each individual component in a seperate docker container. All service related Dockerfiles are stored in `../Dockerfiles/Dockerfile.<service_type>`. Users will need to build and run the containers on their Openstack host server.


##### API Handler/Server setup

- BUILD - from concertim-openstack-service root directory
	```
	docker build --network=host --tag concertim_api_server:<version> -f Dockerfiles/Dockerfile.api_server .
	```

- RUN - mounts the config file, data dir, and log dir as a vol, publish port 42356 on host net
	```
	docker run -d --name concertim_api_server \
		--network=host \
		-v /etc/concertim-openstack-service/config.yaml:/etc/concertim-openstack-service/config.yaml \
		-v /var/log/concertim-openstack-service/:/app/var/log/ \
		-v /var/lib/concertim-openstack-service/data/:/app/var/data/ \
		--publish <Host>:42356:42356 \
		concertim_api_server
	```

- LOGS - tail 50 with follow (also in log dir on localhost, or by `docker logs`)
	```
	docker exec concertim_api_server tail -50f /app/var/log/api_server.log
     ```

##### Update Handler(s) setup

Bulk Updates Handler

- BUILD - from concertim-openstack-service root directory
    ```
     docker build --network=host --tag concertim_bulk_updates:<version> -f Dockerfiles/Dockerfile.updates_bulk .
    ```
- RUN - mounts the config file, data dir, and log dir as a vol
    ```
    docker run -d --name concertim_bulk_updates \
		--network=host \
		-v /etc/concertim-openstack-service/config.yaml:/etc/concertim-openstack-service/config.yaml \
		-v /var/log/concertim-openstack-service/:/app/var/log/ \
		-v /var/lib/concertim-openstack-service/data/:/app/var/data/ \
		concertim_bulk_updates
    ```
- LOGS - tail 50 with follow (also in log dir on localhost, or by `docker logs`)
    ```
    docker exec concertim_bulk_updates tail -50f /app/var/log/updates_bulk.log
    ```
	
Messaging Queue Updates Handler

- BUILD - from concertim-openstack-service root directory
    ```
     docker build --network=host --tag concertim_mq_listener:<version> -f Dockerfiles/Dockerfile.updates_mq .
    ```
- RUN - mounts the config file, data dir, and log dir as a vol
    ```
    docker run -d --name concertim_mq_listener \
		--network=host \
		-v /etc/concertim-openstack-service/config.yaml:/etc/concertim-openstack-service/config.yaml \
		-v /var/log/concertim-openstack-service/:/app/var/log/ \
		-v /var/lib/concertim-openstack-service/data/:/app/var/data/ \
		concertim_mq_listener
    ```
- LOGS - tail 50 with follow (also in log dir on localhost, or by `docker logs`)
    ```
    docker exec concertim_mq_listener tail -50f /app/var/log/updates_mq.log
    ```

##### Metric Handler setup

- BUILD - from concertim-openstack-service root directory
    ```
    docker build --network=host --tag concertim_metrics:<version> -f Dockerfiles/Dockerfile.metrics .
    ```
- RUN - mounts the config file, data dir, and log dir as a vol
    ```
    docker run -d --name concertim_metrics \
		--network=host \
		-v /etc/concertim-openstack-service/config.yaml:/etc/concertim-openstack-service/config.yaml \
		-v /var/log/concertim-openstack-service/:/app/var/log/ \
		-v /var/lib/concertim-openstack-service/data/:/app/var/data/ \
		concertim_metrics
    ```
- LOGS - tail 50 with follow (also in log dir on localhost, or by `docker logs`)
    ```
    docker exec concertim_metrics tail -50f /app/var/log/metrics.log
    ```

##### Billing Handler setup

- BUILD - from concertim-openstack-service root directory
    ```
    docker build --network=host --tag concertim_billing:latest -f Dockerfiles/Dockerfile.billing .
    ```

- RUN - mounts the config file, data dir, and log dir as a vol
    ```
    docker run -d --name concertim_billing \
		--network=host \
		-v /etc/concertim-openstack-service/config.yaml:/etc/concertim-openstack-service/config.yaml \
		-v /var/log/concertim-openstack-service/:/app/var/log/ \
		-v /var/lib/concertim-openstack-service/data/:/app/var/data/ \
		concertim_billing
    ```

- LOGS - tail 50 with follow (also in log dir on localhost, or by `docker logs`)
    ```
    docker exec concertim_billing tail -50f /var/log/concertim-openstack-service/billing.log
    ```

## Importing Package For Use in Other Modules

The Concertim-Openstack-Service contains many components and modules that can be used in developent of other packages. To import, follow the installation instruction to build and install the package so that is availbale in your python environment. Then in the code import the module that is needed - like `from con_opstk.concertim.components.rack import ConcertimRack`

## Development

TBD

## Releases

Release and product change notes can be found [here](/release.md).
