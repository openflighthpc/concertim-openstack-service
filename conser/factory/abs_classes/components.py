from abc import ABC, abstractmethod

class Component(ABC):
    """
    Basic Component representation:
            Components are objects that are used to handle the
            different aspects of a client when needed. (An
            example being Nova for Openstack)

            A Client will be made of 0 or more Components
    """

    @abstractmethod
    def get_connection_obj(self):
        """
        Function to create a connection to the Component
        """

    @abstractmethod
    def disconnect(self):
        """
        Function for disconnecting all streams before garbage collection.
        """

class QueueComponent(Component):
    """
    QueueComponent representation:
            QueueComponents are a specialized type of Component
            meant to handle communication with a Cloud Client's
            messaging queue if necessary.
    """

    @abstractmethod
    def get_connection_obj(self):
        """
        Function to create a connection channel to the Queue
        """

    @abstractmethod
    def start_listening(self):
        """
        Function that is first called on the Component
        to begin listening to the queue for messages
        """

    @abstractmethod
    def handle_message(self):
        """
        The main function of the Component. Used
        to house the logic for parsing the message and
        performing the necessary action in the Client.
        """
