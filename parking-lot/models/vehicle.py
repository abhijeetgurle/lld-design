from abc import ABC, abstractmethod

from enums.vehicle_type import VehicleType


class Vehicle(ABC):
    """
    Abstract class for a vehicle.
    """
    def __init__(self, number: str):
        self._number = number

    @property
    @abstractmethod
    def type(self) -> VehicleType:
        pass

    @property
    def number(self) -> str:
        return self._number


class Car(Vehicle):
    @property
    def type(self) -> VehicleType:
        return VehicleType.CAR


class Bike(Vehicle):
    @property
    def type(self) -> VehicleType:
        return VehicleType.BIKE


class Truck(Vehicle):
    @property
    def type(self) -> VehicleType:
        return VehicleType.TRUCK

