# API Handler/Server Component

The main functionality of the API Handler component is to provide endpoints for Concertim to interact with Cloud objects when they are updated in Concertim. API Handler functions by recieving a REST call from Concertim, performing actions in Cloud and translating the data, then sending the response back to Concertim.

The API Handler/Server is designed to run as a Flask application on the Cloud Host in a dedicated Docker container.

## Installation

The API Handler is designed to listen for communication on port `42356` of the Cloud Host server. As such, this port needs to be open and allow for traffic. It also requires the `/etc/concertim-openstack-service/config.yaml` to be available and properly configured.

The recommended method for deploying the API Handler is by using the [API Server Dockerfile](../Dockerfiles/Dockerfile.api_server).

### Example Docker commands:

- BUILD - from concertim-openstack-service root directory
	``````
	docker build --network=host --tag concertim_api_server:latest -f Dockerfiles/Dockerfile.api_server .
	``````

- RUN - mounts the config file, data dir, and log dir as a vol, publish port 42356 on host net
	``````
	docker docker run -d --name concertim_api_server \
        --network=host \
        -v /etc/concertim-openstack-service/config.yaml:/etc/concertim-openstack-service/config.yaml \
        -v /var/log/concertim-openstack-service/:/app/var/log/ \
        -v /var/lib/concertim-openstack-service/data/:/app/var/data/ \
        --publish hostIP:42356:42356 \
        concertim_api_server
	``````

- LOGS - in `/var/log/concertim-openstack-service/` on localhost, or by `docker logs` (if deployed using the [ansible playbook](https://github.com/alces-flight/concertim-ansible-playbook/tree/main) the log dir is `/opt/concertim/var/log/openstack-service/`)


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

##### `/key_pairs` - List keypairs in the cloud for a Concertim user

###### Example request json:

``````
{
    cloud_env: {
        ...
    }
}   
``````

###### Example response:

``````
{
	key_pairs:
}
``````

#### POST

##### `/user` - Create a new user in the cloud

###### Example request json:

``````
{
    cloud_env: {
        ...
    },
    username: , 
    name: , 
    email: , 
    password: 
}
``````

###### Example response:

``````
{
    username: ,
    user_cloud_id: 
}
``````

##### `/team` - Create a new team in the cloud

###### Example request json:

``````
{
    cloud_env: {
        ...
    },
    name: 
}
``````

###### Example response:

``````
{
    project_id: ,
    billing_acct_id: 
}
``````

##### `/team_role` - Create a team role in the cloud

###### Example request json:

``````
{
    cloud_env: {
        ...
    },
    team_role: {
        project_id:,
        user_id:,
        role:
    }
}
``````

###### Example response:

``````
{
    success: True
}
``````

##### `/update_status/<type>/<id>` - Control the corresponding Openstack object for a given Concertim object

###### Example request json:

``````
{
    cloud_env: {
        ...
    },
    action:
}   
``````

- `<type>` - The type of component to be updated ("racks", "devices")
- `<id>` - The openstack ID for the component
- `<action>` - The action to perform (Racks: 'destroy'; Devices: 'on', 'off', 'suspend', 'resume', 'destroy')

###### Example response:

``````
{
    cloud_response:
}
``````

##### `/key_pairs` - Create a new keypair in Openstack for a Concertim user

###### Example request json:

``````
{
    cloud_env: {
        ...
    },
    key_pair: {
        name:,
        key_type:,
        public_key: <optional public key>
    }
}   
``````

###### Example response:

``````
{
	key_pair: {
		name:
		private_key:
		public_key:
	}
}
``````

##### `/get_draft_invoice` - Retrieves a given user's most current invoice

###### Example request json:

``````
{
    invoice: {
        billing_acct_id:
    }
}   
``````

###### Example response:

``````
{
	draft_invoice: {
        ...
	}
}
``````

##### `/list_paginated_invoices` - Retrieves a given user's invoices in a paginated response

###### Example request json:

``````
{
    invoices: {
        billing_acct_id: ,
        offset: , #optional
        limit: #optional
    }
}   
``````

###### Example response:

``````
{
	total_invoices: ,
    invoices: {
        ...
	}
}
``````

##### `/get_account_invoice` - Retrieves a given user's specific invoice

###### Example request json:

``````
{
    invoice: {
        billing_acct_id: ,
        invoice_id:
    }
}   
``````

###### Example response:

``````
{
    invoice: {
        ...
	}
}
``````

#### DELETE

##### `/user` - Delete a user in the cloud

###### Example request json:

``````
{
    cloud_env: {
        ...
    },
    user_info: {
        cloud_user_id: 
    }
}
``````

###### Example response:

``````
{
    success: True
}
``````

##### `/team` - Delete a team in the cloud

###### Example request json:

``````
{
    cloud_env: {
        ...
    },
    team_info: {
        project_id:,
        billing_acct_id:
    }
}
``````

###### Example response:

``````
{
    success: True
}
``````

##### `/team_role` - Delete a team role in the cloud

###### Example request json:

``````
{
    cloud_env: {
        ...
    },
    team_role: {
        project_id:,
        user_id:,
        role:
    }
}
``````

###### Example response:

``````
{
    success: True
}
``````

##### `/key_pairs` - Delete a keypair in Openstack for a Concertim user

###### Example request json:

``````
{
    cloud_env: {
        ...
    },
    keypair_name:
}   
``````

###### Example response:

``````
{
    success: True
}
``````