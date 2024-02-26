from abc import ABC, abstractmethod

class Client(ABC):
    """
    Basic Client representation:
            Client objects are used for communication with a specific
            application's API.

            A Handler object will contain one or more Client objects.

            All Client functions return a dictionary of values 
            with each key representing an object and all relevant object
            data within a subdictionary under the key
    """

    @abstractmethod
    def get_connection_obj(self):
        """
        Function to create a connection to the application
        """

    @abstractmethod
    def disconnect(self):
        """
        Function for disconnecting all streams before garbage collection.
        """

class AbsBillingClient(Client):
    """
    Basic Billing Client representaion:
            A Billing Client object will be created for communcation with
            the configured billing app's API.

            Functions are named with Concertim object naming in mind.
    """

    @abstractmethod
    def create_account(self):
        """
        Function for creating object(s) to represent the Concertim Team.
        """

    @abstractmethod
    def create_cluster_order(self):
        """
        Function to create the equivalent of an order for a new cluster.
        """
    
    @abstractmethod
    def add_usage(self):
        """
        Function to add usage data to a User's cluster item in the billing app.
        """

    @abstractmethod
    def add_credits(self):
        """
        Function to add a currency/token/credit amount to a User.
        """

    @abstractmethod
    def delete_account(self):
        """
        Function for deleting object(s) representing the Concertim User.
        """

    @abstractmethod
    def delete_cluster_order(self):
        """
        Function to delete/cancel the equivalent of an order for a new cluster.
        """
    
    @abstractmethod
    def get_account_billing_info(self):
        """
        Function to retrieve an Account's billing information from the billing app.
        """

    @abstractmethod
    def get_cluster_billing_info(self):
        """
        Function to get a cluster's billing info from the billing app.
        """
    
    @abstractmethod
    def get_all_billing_accounts(self):
        """
        Function to get all User/Account info from the billing app.
        """

    @abstractmethod
    def get_all_billing_clusters(self):
        """
        Function to get all Cluster/Order info from the billing app for a User.
        """

    @abstractmethod
    def update_account_billing_info(self):
        """
        Function to update User's info in the billing app. Address, email, password, etc.
        """

    @abstractmethod
    def get_invoice_preview(self):
        """
        Get the json data of a preview of the current invoice amounts for a User.
        """
    
    @abstractmethod
    def get_all_invoices(self):
        """
        Get the invoice history for a User. Paginated if possible.
        """

    @abstractmethod
    def get_invoice(self):
        """
        Get the invoice history for a User. Paginated if possible.
        """

    @abstractmethod
    def get_credits(self):
        """
        Get the invoice history for a User. Paginated if possible.
        """
    
class AbsCloudClient(Client):
    """
    Basic Cloud Client representaion:
        The CloudClient will be used to communicate with the API of a given
        Cloud provider (OpenStack, Azure, AWS, GoogleCloud, etc.)
    """

    @abstractmethod
    def create_cm_project(self):
        """
        Create a new Concertim Managaed account/project

        returns a Dict in the format:
        {
            id: ,
            project: {
                id: ,
                ... other obj info ...
            }
        }
        """
    
    @abstractmethod
    def create_cm_user(self):
        """
        Create a new Concertim Managed user.

        returns a Dict in the format:
        {
            id: ,
            user: {
                id: ,
                ... other obj info ...
            }
        }
        """

    @abstractmethod
    def create_keypair(self):
        """
        Create a new KeyPair for a given User/Account

        returns a Dict in the format:
        {
            keypair: {
                name: ,
                ... other obj info ...
            }
        }
        """

    @abstractmethod
    def get_metric(self):
        """
        Get the metrics for a given metric type

        returns a Dict in the format:
        {
            id: ,
            metric: {
                id: ,
                name: ,
                value: ,
                granularity: ,
                ... other obj info ...
            }
        }
        """

    @abstractmethod
    def get_user_info(self):
        """
        Get a user's cloud info
        """

    @abstractmethod
    def get_project_info(self):
        """
        Get cloud info for the given account/project
        """

    @abstractmethod
    def get_all_cm_users(self):
        """
        Get all Concertim Managed Users in the cloud.
        """

    @abstractmethod
    def get_all_cm_projects(self):
        """
        Get all Concertim Managed Accounts/Projects in the cloud.
        """
    
    @abstractmethod
    def get_cost(self):
        """
        Get the cost data for a given Cloud Object
        """

    @abstractmethod
    def get_keypair(self):
        """
        Get keypair info for a given User's/Account's keypair.
        """

    @abstractmethod
    def get_all_keypairs(self):
        """
        Get all keypairs for a user/account
        """

    @abstractmethod
    def get_server_info(self):
        """
        Get details for a given server/instance.
        """
    
    @abstractmethod
    def get_cluster_info(self):
        """
        Get details for a given cluster.
        """

    @abstractmethod
    def get_all_servers(self):
        """
        Get all servers for a given User/Account.
        """

    @abstractmethod
    def get_all_clusters(self):
        """
        Get all clusters for a given User/Account.
        """

    @abstractmethod
    def get_flavors(self):
        """
        Get all available flavors for servers in the Cloud.
        """

    @abstractmethod
    def update_server_status(self):
        """
        Change status of a server/instance (active, stopped, etc.)
        """

    @abstractmethod
    def update_cluster_status(self):
        """
        Change status of a cluster (active, stopped, etc.)
        """

    @abstractmethod
    def update_user_info(self):
        """
        Update a user's info (email, password, etc)
        """

    @abstractmethod
    def update_project_info(self):
        """
        Update an account's/project's info.
        """

    @abstractmethod
    def delete_user(self):
        """
        Remove a User from the cloud.
        """
    
    @abstractmethod
    def delete_project(self):
        """
        Remove an account/project from the cloud.
        """
    
    @abstractmethod
    def delete_keypair(self):
        """
        Delete a KeyPair from a user/account.
        """

    @abstractmethod
    def delete_cluster(self):
        """
        Destory a given cluster.
        """

    @abstractmethod
    def delete_server(self):
        """
        Destroy a given server.
        """

    @abstractmethod
    def start_message_queue(self):
        """
        Start listening to the message queue and intercepting messages
        """