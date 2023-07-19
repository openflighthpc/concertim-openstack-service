# User Handler Component

The main functionality of the UserHandler component is to provide an endpoint for concertim to interact with Openstack user / project when they are updated in Concertim. UserHandler helps with mapping users / projects in Openstack to users in Conceritm.

UserHandler is designed to run as a Flask application on the Openstack Host in a dedicated Docker container.

## Installation

The UserHandler is designed to listen for communication on port `42356` of the Openstack Host server. As such, this port needs to be open and allow for traffic. It also requires the `/etc/concertim-openstack-service/config.yaml` to be available and properly configured.

The recommended method for deploying the UserHandler is by using the [UserHandler Dockerfile](/Dockerfiles/Dockerfile.user_handler).

### Example Docker commands:
- BUILD - from concertim-openstack-service root directory
    ``````
     docker build --network=host --tag concertim-user-handler:<version> -f Dockerfiles/Dockerfile.user_handler .
    ``````
- RUN - mounts the config file as a vol, publish port 42356 on host net
    ``````
    docker run -d --name concertim-user-handler --network=host -v /etc/concertim-openstack-service/config.yaml:/etc/concertim-openstack-service/config.yaml --publish <ip>:42356:42356 concertim-user-handler
    ``````
- LOGS - tail 50 with follow
    ``````
     docker exec concertim-metrics tail -50f /var/log/concertim-openstack-service/user-handler.log
     ``````

## Usage

The UserHandler accepts data via REST requests, then interacts with Openstack based on the data recieved to the various endpoints.

The Handler is expected to recieve calls from the Concertim UI which will build the proper request before sending. Authentication data is pulled from the `Cloud Environment` page that admins in Concertim control.

### Endpoints

#### GET

##### `/` - Test endpoint to verify service is running

###### Example response

``````
Running
``````

#### POST

##### `/create_user_project` - Create a new user and project in openstack

###### Status Codes:

Response messages are send along with status codes for debugging

- `2xx` - Successful transaction
- `4xx` - Request Error
- `5xx` - Internal server error

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