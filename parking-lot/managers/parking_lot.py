import threading
from typing import List, Dict, Tuple, Optional

from exceptions.parking_exceptions import ParkingLotFullException, InvalidVehicleTypeException, \
    GateNotAvailableException, VehicleNotFoundException, InvalidSlotException
from models.parking_gate import EntryGate, ExitGate
from models.parking_slot import ParkingSlot, CarSlot
from models.vehicle import Vehicle
from strategies.base import ParkingStrategy


class ParkingLot:
    def __init__(
            self,
            levels: int,
            slots_per_level: int,
            number_of_entries: int,
            number_of_exits: int,
            parking_strategy: ParkingStrategy,
    ):
        if levels <= 0 or slots_per_level <= 0:
            raise ValueError("Levels and slots per level must be positive")
        if number_of_entries <= 0 or number_of_exits <= 0:
            raise ValueError("Number of entries and exits must be positive")

        self._levels = levels
        self._slots_per_level = slots_per_level
        self._parking_strategy = parking_strategy

        # Initialize gates
        self._entries = [EntryGate(i) for i in range(number_of_entries)]
        self._exits = [ExitGate(i) for i in range(number_of_exits)]

        # Initialize slots
        self._slots = self._initialize_slots()
        self._available_slots = levels * slots_per_level

        # Thread safety
        self._lot_lock = threading.Lock()  # Lock for entire parking lot operations
        self._gate_locks = {  # Individual locks for each gate
            'entry': [threading.Lock() for _ in range(number_of_entries)],
            'exit': [threading.Lock() for _ in range(number_of_exits)]
        }

        # Tracking
        self._vehicle_to_slot: Dict[str, Tuple[int, int]] = {}  # vehicle_number -> (level, slot_number)

    def _initialize_slots(self) -> List[List[ParkingSlot]]:
        """Initialize parking slots for all levels."""
        slots = []
        slot_number = 0
        for level in range(self._levels):
            level_slots = []
            for _ in range(self._slots_per_level):
                # In a real implementation, you might want to create different types of slots
                # based on some configuration or pattern
                level_slots.append(CarSlot(slot_number, level))
                slot_number += 1
            slots.append(level_slots)
        return slots

    def _get_available_entry_gate(self) -> Optional[EntryGate]:
        """Get an available entry gate with proper locking."""
        for i, gate in enumerate(self._entries):
            with self._gate_locks['entry'][i]:
                if gate.is_available:
                    gate.block_gate()
                    return gate
        return None

    def _get_available_exit_gate(self) -> Optional[ExitGate]:
        """Get an available exit gate with proper locking."""
        for i, gate in enumerate(self._exits):
            with self._gate_locks['exit'][i]:
                if gate.is_available:
                    gate.block_gate()
                    return gate
        return None

    def _release_entry_gate(self, gate: EntryGate) -> None:
        """Release an entry gate with proper locking."""
        with self._gate_locks['entry'][gate.number]:
            gate.release_gate()

    def _release_exit_gate(self, gate: ExitGate) -> None:
        """Release an exit gate with proper locking."""
        with self._gate_locks['exit'][gate.number]:
            gate.release_gate()

    def park_vehicle(self, vehicle: Vehicle) -> Optional[ParkingSlot]:
        """
            Park a vehicle in the parking lot.

            Args:
                vehicle: The vehicle to park

            Returns:
                The parking slot where the vehicle was parked

            Raises:
                ParkingLotFullException: If parking lot is full
                GateNotAvailableException: If no entry gates are available
                InvalidVehicleTypeException: If vehicle type is not supported
        """
        with self._lot_lock:
            if self._available_slots == 0:
                raise ParkingLotFullException("Parking lot is full")

            if vehicle.number in self._vehicle_to_slot:
                raise InvalidVehicleTypeException("Vehicle is already parked")

            # Get entry gate
            entry_gate = self._get_available_entry_gate()
            if not entry_gate:
                raise GateNotAvailableException("No entry gates available")

            try:
                # Flatten slots list for strategy
                all_slots = [slot for level in self._slots for slot in level]
                spot = self._parking_strategy.find_spot(vehicle, all_slots)

                if not spot:
                    raise InvalidVehicleTypeException("No suitable spot found for vehicle type")

                for level_idx, level in enumerate(self._slots):
                    for slot_idx, slot in enumerate(level):
                        if slot == spot:
                            # Update tracking
                            self._vehicle_to_slot[vehicle.number] = (level_idx, slot_idx)

                            # Park the vehicle
                            spot.assign_vehicle(vehicle)
                            self._available_slots -= 1

                            return spot

            except Exception as e:
                # If anything goes wrong, release the gate
                self._release_entry_gate(entry_gate)
                raise e
            finally:
                # Always release the gate
                self._release_entry_gate(entry_gate)

            return None

    def remove_vehicle(self, vehicle: Vehicle) -> Optional[ParkingSlot]:
        """Remove a vehicle from the parking lot."""
        with self._lot_lock:
            if vehicle.number not in self._vehicle_to_slot:
                raise VehicleNotFoundException("Vehicle not found in parking lot")

            # Get exit gate
            exit_gate = self._get_available_exit_gate()
            if not exit_gate:
                raise GateNotAvailableException("No exit gates available")

            try:
                level, slot_idx = self._vehicle_to_slot[vehicle.number]
                slot = self._slots[level][slot_idx]

                if not slot.is_vehicle_parked(vehicle):
                    raise InvalidSlotException("Vehicle not found in expected slot")

                slot.exit_vehicle()
                self._available_slots += 1

                # Update tracking
                del self._vehicle_to_slot[vehicle.number]

                return slot

            except Exception as e:
                self._release_exit_gate(exit_gate)
                raise e
            finally:
                self._release_exit_gate(exit_gate)

            return None

    def get_available_slots(self) -> int:
        """Get the number of available slots."""
        with self._lot_lock:
            return self._available_slots