from typing import Optional

from core.entities.user import User
from core.interfaces.repositories.user_repository import UserRepository


class InMemoryUserRepository(UserRepository):
    def __init__(self):
        self.users = []

    def add(self, user: User):
        self.users.append(user)

    def remove(self, user: User):
        self.users.remove(user)

    def find_by_id(self, id: str) -> Optional[User]:
        for user in self.users:
            if user.id == id:
                return user

        return None

    def find_by_email(self, email: str) -> Optional[User]:
        for user in self.users:
            if user.email == email:
                return user

        return None

    def get_all(self):
        return self.users
