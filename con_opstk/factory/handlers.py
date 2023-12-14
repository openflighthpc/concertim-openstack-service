from abc import ABC, abstractmethod

class Handler(ABC):
    """
    Basic Handler representation: 
            Handlers are objects that contain various service/client objects
            and are meant to handler the processing and transformation of data.

            A Handler object will contain one or more Service objects.

            A Handler's logic should be generic and agnostic of Service types.
    """

    @abstractmethod
    def run_process(self):
        """
        The main running loop of the Handler.
        """

    @abstractmethod
    def disconnect(self):
        """
        Function for disconnecting all services before garbage collection.
        """

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
        Process for updating all Concertim object costs.
        """

    @abstractmethod
    def billing_app_cost_update(self):
        """
        Process for updating all cost data in the Billing Application.
        """

class AbsUpdateHandler(Handler):
    """
    Update Handler representaion:
            Update Handlers are responsible for handling object status updates
            between the configured Cloud and Concertim. This is accomplished
            via APIs for the various services.

            Update flow from the Cloud -> Concertim, using the Cloud as the 
            source of object data.
    """

    @abstractmethod
    def populate_view(self):
        """
        A function for populating the view object that stores the mapping of 
        data between the cloud and Concertim
        """

    @abstractmethod
    def update_concertim(self):
        """
        Process for handling the necessary updates to Concertim.
        """