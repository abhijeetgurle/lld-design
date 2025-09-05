from entity.entity import Entity


class UserEntity(Entity):
    """
    Represents a user in the system.
    """
    def __init__(self, user_id: str, username: str):
        self.user_id = user_id
        self.username = username

    def get_id(self) -> str:
        return self.user_id

    def __str__(self) -> str:
        return f"UserEntity(id={self.user_id}, username={self.username})"