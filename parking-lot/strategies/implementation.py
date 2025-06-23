from typing import List, Optional

from models.parking_slot import ParkingSlot
from models.vehicle import Vehicle
from strategies.base import ParkingStrategy


class NearestSpotStrategy(ParkingStrategy):
    def find_spot(self, vehicle: Vehicle, slots: List[ParkingSlot]) -> Optional[ParkingSlot]:
        for slot in slots:
            if slot.can_assign_vehicle(vehicle):
                return slot

        return None