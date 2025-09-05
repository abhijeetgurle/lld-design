from abc import ABC, abstractmethod


class Service(ABC):
    """
    Base class for all services in the system.
    """
    def __init__(self, service_name: str):
        self.service_name = service_name

    def get_service_name(self) -> str:
        """
        Returns the name of the service.
        """
        return self.service_name

    @abstractmethod
    def call(self):
        """
        Placeholder for service call logic.
        This method should be overridden by subclasses to implement specific service behavior.
        """
        pass