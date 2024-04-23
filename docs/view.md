# View Handlers

The main functionality of the Concertim-Openstack-Service View Handlers are to pull information from both Concertim and the Cloud, and create a `view` object that maps the views of the two applications together. This `view` object is then stored in a `view.pickle` file for shared use by other services in the Concertim-Openstack-Service suite.

The View components are intended to be ran in dedicated Docker containers. Scaling / async concurrency is to be added in future states of the project to account for larger clouds and HA requirements.

### View Sync

The View Sync Handler is used to sync the object data from Concertim, the Cloud, and the configured Billing Application - pulling all data into memory then mapping the data in a layered fashion.

### View Queue

The View Queue Handler is used for listening to the configured Cloud/Message Queue and updating the view with realtime updates.

## Installation

The View handlers require the `/etc/concertim-openstack-service/config.yaml` to be available and properly configured.

The recommended method for deploying the Update Components are by using the Dockerfile for the corresponding service.

- [View Sync Dockerfile](../Dockerfiles/Dockerfile.view_sync)
- [View Queue Dockerfile](../Dockerfiles/Dockerfile.view_queue)

Example Docker commands can be found in the [example docker commands file](../Dockerfiles/docker_commands_ex.txt)

## Configration

The View Handlers make use of the base Cloud Component APIs as well as the messaging queue for the Cloud. All of these should be configured and available in the Cloud environment that the view Handlers are running on.

Please see [the example config.yaml](../etc/config-sample.yaml) for how the authentication is configured.

## Cloud

### Openstack

Each component in the Concertim-Openstack-service makes use of various openstack objects for tracking Concertim-managed systems. To achieve this, the following need to be created in Openstack:

- Openstack Role : `watcher`
- Openstack User : `concertim`
- Openstack Role : `rating`
- Openstack User : `cloudkitty`

## Usage

The View Handlers are intended to function as a daemon process that continuously pull data from Concertim and the Cloud. As such, once the docker containers are completely configured and running the services should act on their own.
