# API Handler/Server Component

The main functionality of the API Handler component is to provide endpoints for Concertim to interact with Openstack objects when they are updated in Concertim. API Handler functions by recieving a REST call from Concertim, performing actions in Openstack and translating the data, then sending the response back to Concertim.

The API Handler/Server is designed to run as a Flask application on the Openstack Host in a dedicated Docker container.

## Installation

The API Handler is designed to listen for communication on port `42356` of the Openstack Host server. As such, this port needs to be open and allow for traffic. It also requires the `/etc/concertim-openstack-service/config.yaml` to be available and properly configured.

The recommended method for deploying the API Handler is by using the [API Server Dockerfile](/Dockerfiles/Dockerfile.api_server).

### Example Docker commands:

- BUILD - from concertim-openstack-service root directory
	``````
	docker build --network=host --tag concertim_api_server:<version> -f Dockerfiles/Dockerfile.api_server .
	``````

- RUN - mounts the config file, data dir, and log dir as a vol, publish port 42356 on host net
	``````
	docker run -d --name concertim_api_server \
		--network=host \
		-v /etc/concertim-openstack-service/config.yaml:/etc/concertim-openstack-service/config.yaml \
		-v /var/log/concertim-openstack-service/:/app/var/log/ \
		-v /var/lib/concertim-openstack-service/data/:/app/var/data/ \
		--publish <Host>:42356:42356 \
		concertim_api_server
	``````

- LOGS - tail 50 with follow (also in log dir on localhost, or by `docker logs`)
	``````
	docker exec concertim_api_server tail -50f /app/var/log/api_server.log
    ``````


## Usage

The API Handler accepts data via REST requests, then interacts with Openstack based on the data recieved to the various endpoints.

The API is expected to recieve calls from the Concertim UI which will build the proper request before sending. Authentication data is pulled from the `Cloud Environment` page that admins in Concertim must configure before perfoming actions that contact the API.

### Endpoints

###### Status Codes:

Response messages are send along with status codes for debugging

- `2xx` - Successful transaction
- `4xx` - Request Error
- `5xx` - Internal server error

#### GET

##### `/` - Test endpoint to verify service is running

###### Example response

``````
Running
``````

##### `/key_pairs` - List keypairs in Openstack for a Concertim user

###### Example request json:

``````
{
"cloud_env":
    {
        ...
    }
}   
``````

###### Example response:

``````
{
    "success": True,
	"key_pairs": <list of keypairs>
}
``````

#### POST

##### `/create_user_project` - Create a new user and project in openstack

###### Example request json:

``````
{
"cloud_env":
    {
        "auth_url":"<auth data>",
        "username":"<auth data>",
        "password":"<auth data>",
        "project_name":"<auth data>",
        "user_domain_name":"<auth data>",
        "project_domain_name":"<auth data>"
    },
"username":"<New user>",
"password":"<New user's password>"
}   
``````

###### Example response:

``````
{
    "project_id":"<new openstack project ID>",
    "user_id":"new openstack user ID",
    "username":"<New user's concertim username>"
}
``````

##### `/update_status/<type>/<id>` - Control the corresponding Openstack object for a given Concertim object

###### Example request json:

``````
{
"cloud_env":
    {
        ...
    },
"action": <action>
}   
``````

- `<type>` - The type of component to be updated ("racks", "devices")
- `<id>` - The openstack ID for the component
- `<action>` - The action to perform (Racks: 'destroy'; Devices: 'on', 'off', 'suspend', 'resume', 'destroy')

###### Example response:

``````
{
    "success": True
}
``````

##### `/key_pairs` - Create a new keypair in Openstack for a Concertim user

###### Example request json:

``````
{
"cloud_env":
    {
        ...
    },
"key_pair":
	{
		"name": <name>,
		"key_type": 'ssh',
		"public_key": <optional public key>
	}
}   
``````

###### Example response:

``````
{
    "success": True,
	"key_pair":
	{
		"name":
		"private_key":
		"public_key":
	}
}
``````

#### DELETE

##### `/key_pairs` - Delete a keypair in Openstack for a Concertim user

###### Example request json:

``````
{
"cloud_env":
    {
        ...
    },
"keypair_name": <name of key to delete>
}   
``````

###### Example response:

``````
{
    "success": True
}
``````
