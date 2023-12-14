from abc import ABC, abstractmethod

class Service(ABC):
    """
    Basic Service representation:
            Service objects are used for communication with a specific
            application's API.

            A Handler object will contain one or more Service objects.
    """

    @abstractmethod
    def get_connection_client(self):
        """
        Function to create a connection to the application
        """

    @abstractmethod
    def disconnect(self):
        """
        Function for disconnecting all clients before garbage collection.
        """

class AbsBillingService(Service):
    """
    Basic Billing Service representaion:
            A Billing Service object will be created for communcation with
            the configured billing app's API.

            Functions are named with Concertim object naming in mind.
    """

    @abstractmethod
    def create_user(self):
        """
        Function for creating object(s) to represent the Concertim User.
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
    def add_currency(self):
        """
        Function to add a currency/token/credit amount to a User.
        """

    @abstractmethod
    def delete_user(self):
        """
        Function for deleting object(s) representing the Concertim User.
        """

    @abstractmethod
    def delete_cluster_order(self):
        """
        Function to delete/cancel the equivalent of an order for a new cluster.
        """
    
    @abstractmethod
    def get_user_billing_info(self):
        """
        Function to retrieve a User's billing information from the billing app.
        """

    @abstractmethod
    def get_cluster_billing_info(self):
        """
        Function to get a cluster's billing info from the billing app.
        """
    
    @abstractmethod
    def get_all_billing_users(self):
        """
        Function to get all User/Account info from the billing app.
        """

    @abstractmethod
    def get_all_billing_clusters(self):
        """
        Function to get all Cluster/Order info from the billing app for a User.
        """

    @abstractmethod
    def update_user_billing_info(self):
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
    
class AbsCloudService(Service):
    """
    Basic Cloud Service representaion:
        The CloudService will be used to communicate with the API of a given
        Cloud provider (OpenStack, Azure, AWS, GoogleCloud, etc.)
    """

    @abstractmethod
    def create_cm_account(self):
        """
        Create a new Concertim Managaed account/project
        """
    
    @abstractmethod
    def create_cm_user(self):
        """
        Create a new Concertim Managed user.
        """

    @abstractmethod
    def create_keypair(self):
        """
        Create a new KeyPair for a given User/Account
        """

    @abstractmethod
    def get_metric(self):
        """
        Get the metrics for a given metric type
        """

    @abstractmethod
    def get_user_info(self):
        """
        Get a user's cloud info
        """

    @abstractmethod
    def get_account_info(self):
        """
        Get cloud info for the given account/project
        """

    @abstractmethod
    def get_all_cm_users(self):
        """
        Get all Concertim Managed Users in the cloud.
        """

    @abstractmethod
    def get_all_cm_accounts(self):
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
    def update_account_info(self):
        """
        Update an account's/project's info.
        """

    @abstractmethod
    def delete_user(self):
        """
        Remove a User from the cloud.
        """
    
    @abstractmethod
    def delete_account(self):
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

    

    

    


