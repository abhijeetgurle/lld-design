from entity.entity import Entity


class DeviceEntity(Entity):
    """
    Represents a device in the system.
    """
    def __init__(self, device_id: str, device_name: str):
        self.device_id = device_id
        self.device_name = device_name

    def get_id(self) -> str:
        return self.device_id

    def __str__(self) -> str:
        return f"DeviceEntity(id={self.device_id}, name={self.device_name})"