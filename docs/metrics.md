# Metric Handler Component

The main functionality of the Concertim-Openstack-Service Metric Handler component is to gather, calculate, transform, and send metrics polled from Openstack resource metric data stored in a Gnocchi database. MetricHandler maps Openstack resources with the corresponding Concertim objects and gathers useful metrics by querying the Gnocchi database at a set interval. Calcualtions are done against the retrieved metrics and then the data is transformed and send to the Concertim Application via REST.

MetricHandler is intended to be run in a dedicated Docker container. Scaling / multithreading is to be added in future releases to help with larger clouds and HA requirements.

## Installation

The MetricHandler requires the `/etc/concertim-openstack-service/config.yaml` to be available and properly configured.

The recommended method for deploying the MetricHandler is by using the [MetricHandler Dockerfile](/Dockerfiles/Dockerfile.metrics).

### Example Docker commands:

- BUILD - from concertim-openstack-service root directory
    ``````
    docker build --network=host --tag concertim_metrics:<version> -f Dockerfiles/Dockerfile.metrics .
    ``````
- RUN - mounts the config file, data dir, and log dir as a vol
    ``````
    docker run -d --name concertim_metrics \
		--network=host \
		-v /etc/concertim-openstack-service/config.yaml:/etc/concertim-openstack-service/config.yaml \
		-v /var/log/concertim-openstack-service/:/app/var/log/ \
		-v /var/lib/concertim-openstack-service/data/:/app/var/data/ \
		concertim_metrics
    ``````
- LOGS - tail 50 with follow (also in log dir on localhost, or by `docker logs`)
    ``````
    docker exec concertim_metrics tail -50f /app/var/log/metrics.log
    ``````

## Configuration

The MetricHandler leverages the Openstack Telemetry service - Ceilometer - and a time-series database - Gnocchi. Both of these need to be configured and available on the Openstack Host.

Please see [the example config.yaml](/etc/config-sample.yaml) for how the authentication is configured.

### Openstack

Each component in the Concertim-Openstack sesrvice makes use of various openstack objects for tracking Concertim-managed systems. To achieve this, the folling needs to be created in Openstack:

- Openstack Role : `watcher`
- Openstack User : `concertim`

#### Gnocchi

The MetricHandler assumes the existance of the `concertim_rate_policy` and `concertim_policy` archive-policies to be created in gnocchi in the Openstack env. An example [creation script](/etc/concertim-archive-policy-create.sql) for this is provided - it is recommended to run the sql in your Openstack database.

#### Ceilometer

Sample files for configuring Openstack Ceilometer's policies are also provided: [polling.yaml](/etc/polling-sample.yaml), [pipeline.yaml](/etc/pipeline-sample.yaml). These files should be used to configure the telemtry service unless the user is experienced with altering Openstack configurations.

*Sample commands if Openstack is deployed with kolla-ansible*
``````
cp ./etc/pipeline-sample.yaml /etc/kolla/ceilometer-central/pipeline.yaml
cp ./etc/pipeline-sample.yaml /etc/kolla/ceilometer-compute/pipeline.yaml
cp ./etc/pipeline-sample.yaml /etc/kolla/ceilometer-notification/pipeline.yaml

cp ./etc/polling-sample.yaml /etc/kolla/ceilometer-central/polling.yaml
cp ./etc/polling-sample.yaml /etc/kolla/ceilometer-compute/polling.yaml
cp ./etc/polling-sample.yaml /etc/kolla/ceilometer-notification/polling.yaml

# add to /etc/kolla/ceilometer*/config.json
       {
           "source": "/var/lib/kolla/config_files/polling.yaml",
           "dest": "/etc/ceilometer/polling.yaml",
           "owner": "ceilometer",
           "perm": "0600"
       },

docker restart ceilometer_compute ceilometer_central ceilometer_notification gnocchi_metricd gnocchi_api
``````

## Usage

The MetricHandler is configured to gather and send metrics at a `5 second` interval by default. This can only be changed by directly editing the [MetricHandler](/driver.py) process and rebuilding the docker image.

After running the Docker container the process will run until stopped, sending metrics to the Concertim app configured in `/etc/concertim-openstack-service/config.yaml`.
