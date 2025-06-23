from abc import ABC, abstractmethod

from enums.vehicle_type import VehicleType
from models.vehicle import Vehicle


class ParkingSlot(ABC):
    def __init__(self, slot_number: int, level: int):
        self._slot_number = slot_number
        self._level = level
        self._is_available = True
        self._vehicle = None

    @property
    def slot_number(self) -> int:
        return self._slot_number

    @property
    @abstractmethod
    def type(self) -> VehicleType:
        pass

    @abstractmethod
    def can_assign_vehicle(self, vehicle: Vehicle) -> bool:
        pass

    @abstractmethod
    def assign_vehicle(self, vehicle: Vehicle) -> None:
        pass

    @abstractmethod
    def exit_vehicle(self) -> None:
        pass

    @abstractmethod
    def is_vehicle_parked(self, vehicle: Vehicle) -> bool:
        pass


class CarSlot(ParkingSlot):
    @property
    def type(self) -> VehicleType:
        return VehicleType.CAR

    def can_assign_vehicle(self, vehicle: Vehicle) -> bool:
        return self._is_available and vehicle.type == VehicleType.CAR

    def assign_vehicle(self, vehicle: Vehicle) -> None:
        if not self.can_assign_vehicle(vehicle):
            raise ValueError('cannot assign vehicle to this slot')

        self._is_available = False
        self._vehicle = vehicle

    def exit_vehicle(self) -> None:
        self._is_available = True
        self._vehicle = None

    def is_vehicle_parked(self, vehicle: Vehicle) -> bool:
        return not self._is_available and vehicle.number == self._vehicle.number


class BikeSlot(ParkingSlot):
    @property
    def type(self) -> VehicleType:
        return VehicleType.BIKE

    def can_assign_vehicle(self, vehicle: Vehicle) -> bool:
        return self._is_available and vehicle.type == VehicleType.BIKE

    def assign_vehicle(self, vehicle: Vehicle) -> None:
        if not self.can_assign_vehicle(vehicle):
            raise ValueError('cannot assign vehicle to this slot')

        self._is_available = False
        self._vehicle = vehicle

    def exit_vehicle(self) -> None:
        self._is_available = True
        self._vehicle = None

    def is_vehicle_parked(self, vehicle: Vehicle) -> bool:
        return not self._is_available and vehicle.number == self._vehicle.number


class TruckSlot(ParkingSlot):
    @property
    def type(self) -> VehicleType:
        return VehicleType.TRUCK

    def can_assign_vehicle(self, vehicle: Vehicle) -> bool:
        return self._is_available and vehicle.type == VehicleType.TRUCK

    def assign_vehicle(self, vehicle: Vehicle) -> None:
        if not self.can_assign_vehicle(vehicle):
            raise ValueError('cannot assign vehicle to this slot')

        self._is_available = False
        self._vehicle = vehicle

    def exit_vehicle(self) -> None:
        self._is_available = True
        self._vehicle = None

    def is_vehicle_parked(self, vehicle: Vehicle) -> bool:
        return not self._is_available and vehicle.number == self._vehicle.number