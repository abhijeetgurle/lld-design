from abc import ABC, abstractmethod

from core.entities.user import User


class UserRepository(ABC):
    @abstractmethod
    def add(self, user: User):
        pass

    @abstractmethod
    def remove(self, user: User):
        pass
    @abstractmethod
    def find_by_id(self, id: str):
        pass

    @abstractmethod
    def find_by_email(self, email: str):
        pass

    @abstractmethod
    def get_all(self):
        pass
