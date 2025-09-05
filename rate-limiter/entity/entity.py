from abc import ABC, abstractmethod


class Entity(ABC):
    """
    Base class for all entity in the system.
    """
    @abstractmethod
    def get_id(self) -> str:
        """
        Returns the unique identifier for the entity.
        """
        pass