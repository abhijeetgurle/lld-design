import uuid


class User:
    def __init__(self, name: str, email: str):
        self._id = str(uuid.uuid4())
        self._name = name
        self._email = email
        self._reputation = 0

    @property
    def id(self):
        return self._id

    @property
    def reputation(self):
        return self._reputation

    def increment_reputation(self, increment: float):
        self._reputation += increment

    def decrement_reputation(self, decrement: float):
        self._reputation -= decrement