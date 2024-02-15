# Update Handler Components

The main functionality of the Concertim-Openstack-Service Update Handler components are to register new updates that occur in the Openstack backend and send the corresponding update to the Concertim Application. The Update Handler is comprised of 2 parts: first, there is a 'bulk' update process that does a full comparison of Concertim and Openstack and updates any delta found (this run periodically); second, there is a Rabbit MQ listener that is enabled that runs continuously to update Concertim with Openstack updates as they occur. Updates are sent to the Concertim Application via REST requests.

The Update Components are intended to be run in dedicated Docker containers. Scaling / multithreading is to be added in future releases to help with larger clouds and HA requirements.

The Update process for the components generates a 'view' of the state of both Concertim and Openstack - this view is stored to be shared among various services as `view.pickle` in the data dir location.

## Installation

The Update Handlers require the `/etc/concertim-openstack-service/config.yaml` to be available and properly configured.

The recommended method for deploying the Update Components are by using the Dockerfile for the corresponding service.

- [Bulk Updates Dockerfile](/Dockerfiles/Dockerfile.updates_bulk)
- [MQ Listener Dockerfile](/Dockerfiles/Dockerfile.updates_mq)

### Example Docker commands:

Bulk Updates Handler

- BUILD - from concertim-openstack-service root directory
    ``````
     docker build --network=host --tag concertim_bulk_updates:<version> -f Dockerfiles/Dockerfile.updates_bulk .
    ``````
- RUN - mounts the config file, data dir, and log dir as a vol
    ``````
    docker run -d --name concertim_bulk_updates \
		--network=host \
		-v /etc/concertim-openstack-service/config.yaml:/etc/concertim-openstack-service/config.yaml \
		-v /var/log/concertim-openstack-service/:/app/var/log/ \
		-v /var/lib/concertim-openstack-service/data/:/app/var/data/ \
		concertim_bulk_updates
    ``````
- LOGS - tail 50 with follow (also in log dir on localhost, or by `docker logs`)
    ``````
    docker exec concertim_bulk_updates tail -50f /app/var/log/updates_bulk.log
    ``````
	
Messaging Queue Updates Handler

- BUILD - from concertim-openstack-service root directory
    ``````
     docker build --network=host --tag concertim_mq_listener:<version> -f Dockerfiles/Dockerfile.updates_mq .
    ``````
- RUN - mounts the config file, data dir, and log dir as a vol
    ``````
    docker run -d --name concertim_mq_listener \
		--network=host \
		-v /etc/concertim-openstack-service/config.yaml:/etc/concertim-openstack-service/config.yaml \
		-v /var/log/concertim-openstack-service/:/app/var/log/ \
		-v /var/lib/concertim-openstack-service/data/:/app/var/data/ \
		concertim_mq_listener
    ``````
- LOGS - tail 50 with follow (also in log dir on localhost, or by `docker logs`)
    ``````
    docker exec concertim_mq_listener tail -50f /app/var/log/updates_mq.log
    ``````

## Configuration

The Update Handlers makes use of the base Openstack Components APIs as well as the RabbitMQ messaging queue for Openstack. All of these should be configured and available in the Openstack environment that the Update Handlers are running on.

Please see [the example config.yaml](/etc/config-sample.yaml) for how the authentication is configured.

### Openstack

Each component in the Concertim-Openstack sesrvice makes use of various openstack objects for tracking Concertim-managed systems. To achieve this, the folling needs to be created in Openstack:

- Openstack Role : `watcher`
- Openstack User : `concertim`
- Openstack Role : `rating`
- Openstack User : `cloudkitty`

## Usage

The Update Handlers are intended to function as a daemon process that continuously update Concertim with changes that occure in Openstack. As such, once the docker containers are completely configured and running the services should act on their own.
