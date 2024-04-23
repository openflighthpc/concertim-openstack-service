from abc import ABC, abstractmethod

class Handler(ABC):
    """
    Basic Handler representation: 
            Handlers are objects that contain various client objects
            and are meant to handler the processing and transformation of data.

            A Handler object will contain one or more Client objects.

            A Handler's logic should be generic and agnostic of Client types.

            All Handler functions return a dictionary of values 
            with each key representing an object and all relevant object
            data within a subdictionary under the key
    """

    @abstractmethod
    def run_process(self):
        """
        The main running loop of the Handler.
        """

    @abstractmethod
    def disconnect(self):
        """
        Function for disconnecting all clients before garbage collection.
        """

#    @abstractmethod
#    def populate_view(self):
#        """
#        A function for populating the view object that stores the mapping of 
#        data between the cloud and Concertim
#        """

class AbsBillingHandler(Handler):
    """
    Billing Handler representation:
            Billing Handlers are created for each seperate billing application
            and are resposible for the main billing data transformations and
            processing.
    """

    @abstractmethod
    def concertim_cost_update(self):
        """
        Process for updating Concertim object costs.
        """

    @abstractmethod
    def billing_app_cost_update(self):
        """
        Process for updating cost data in the Billing Application.
        """

class AbsViewHandler(Handler):
    """
    View Handler representaion:
            View Handlers are responsible for handling object status updates
            between the configured Cloud and Concertim. This is accomplished
            via APIs for the various services(Clients) and creating a mapping
            between the states of the two applications

            Update flow from the Cloud -> Concertim, using the Cloud as the 
            source of object data.

            This is saved as a view object for other processes to consume
    """
