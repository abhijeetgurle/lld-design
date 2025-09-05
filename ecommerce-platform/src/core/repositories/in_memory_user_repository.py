from typing import Dict, Optional, List

from core.entities.user import User, Customer
from core.interfaces.repositories.user_repository import UserRepository


class InMemoryUserRepository(UserRepository):
    def __init__(self):
        self._users: Dict[str, User] = {}

    def save(self, user: User) -> User:
        self._users[user.user_id] = user
        return user

    def find_by_id(self, user_id: str) -> Optional[User]:
        return self._users.get(user_id)

    def find_by_email(self, email: str) -> Optional[User]:
        return next(
            (user for user in self._users.values() if user.email == email),
            None
        )

    def find_customers(self) -> List[Customer]:
        return [
            user for user in self._users.values()
            if isinstance(user, Customer)
        ]