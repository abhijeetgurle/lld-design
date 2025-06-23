from abc import ABC, abstractmethod

class ParkingGate(ABC):
    def __init__(self, number: int) -> None:
        self._number = number
        self._is_available = True

    @property
    def number(self) -> int:
        return self._number

    @property
    def is_available(self) -> bool:
        return self._is_available

    @abstractmethod
    def block_gate(self) -> None:
        pass

    @abstractmethod
    def release_gate(self) -> None:
        pass


class EntryGate(ParkingGate):
    def block_gate(self) -> None:
        self._is_available = False

    def release_gate(self) -> None:
        self._is_available = True


class ExitGate(ParkingGate):
    def block_gate(self) -> None:
        self._is_available = False

    def release_gate(self) -> None:
        self._is_available = True