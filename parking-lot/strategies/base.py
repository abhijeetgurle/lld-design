from abc import ABC, abstractmethod
from typing import List, Optional

from models.parking_slot import ParkingSlot
from models.vehicle import Vehicle


class ParkingStrategy(ABC):
    @abstractmethod
    def find_spot(self, vehicle: Vehicle, slots: List[ParkingSlot]) -> Optional[ParkingSlot]:
        pass