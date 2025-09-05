from entity.entity import Entity


class IPEntity(Entity):
    """
    Represents an IP address in the system.
    """
    def __init__(self, ip_address: str):
        self.ip_address = ip_address

    def get_id(self) -> str:
        return self.ip_address

    def __str__(self) -> str:
        return f"IPEntity(ip_address={self.ip_address})"