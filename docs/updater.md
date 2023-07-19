# Update Handler Component

The main functionality of the Concertim-Openstack service Update Handler component is to register new updates that occur in the Openstack backend and send the corresponding update to the Concertim Application. The UpdateHandler runs in 2 parts: first, there is a mapping process that gathers then maps Concertim objects to Openstack objects and sends updates for any discrepancies (this run periodically); second, there is a Rabbit MQ listener that is enabled that runs continuously to update Concertim with Openstack updates as they occur. Updates are sent to the Concertim Application via REST requests.

UpdateHandler is intended to be run in a dedicated Docker container. Scaling / multithreading is to be added in future releases to help with larger clouds and HA requirements.

## Installation

The UpdateHandler requires the `/etc/concertim-openstack-service/config.yaml` to be available and properly configured.

The recommended method for deploying the UpdateHandler is by using the [UpdateHandler Dockerfile](/Dockerfiles/Dockerfile.updates).

### Example Docker commands:

- BUILD - from concertim-openstack-service root directory
    ``````
     docker build --network=host --tag concertim-updates:<version> -f Dockerfiles/Dockerfile.updates .
    ``````
- RUN - mounts the config file as a vol
    ``````
     docker run -d --name concertim-updates --network=host -v /etc/concertim-openstack-service/config.yaml:/etc/concertim-openstack-service/config.yaml concertim-updates
     ``````
- LOGS - tail 50 with follow
    ``````
     docker exec concertim-updates tail -50f /var/log/concertim-openstack-service/updates.log
     ``````

## Configuration

The UpdateHandler makes use of the base Openstack Components APIs as well as the RabbitMQ messaging queue for Openstack. All of these should be configured and available in the Openstack environment that the UpdateHandler is running on.

Please see [the example config.yaml](/etc/config-sample.yaml) for how the authentication is configured.

## Usage

The UserHnalder is intended to function as a daemon process that continuously updates Concertim with changes that occure in Openstack. As such, once the docker container is completely configured and running the service should act on its own.