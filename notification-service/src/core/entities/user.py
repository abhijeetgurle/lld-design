import uuid
from dataclasses import dataclass


@dataclass
class User:
    name: str
    email: str
    phone_no: str = None
    device_id: str = None
    id: str = None

    def __post_init__(self):
        if self.id is None:
            self.id = str(uuid.uuid4())

        if self.name is None:
            raise ValueError("Name cannot be None")

        if self.email is None:
            raise ValueError("Email cannot be None")

    def update_name(self, name: str):
        self.name = name

    def update_email(self, email: str):
        self.email = email

    def update_phone(self, phone_no: str):
        self.phone_no = phone_no

    def update_device_id(self, device_id: str):
        self.device_id = device_id