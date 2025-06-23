import threading
import time

from managers.parking_lot import ParkingLot
from models.vehicle import Car, Bike, Truck, Vehicle
from strategies.implementation import NearestSpotStrategy

def simulate_vehicle_entry(parking_lot: ParkingLot, vehicle: Vehicle, delay: float):
    """Simulate a vehicle entering the parking lot after a delay."""
    time.sleep(delay)
    try:
        slot = parking_lot.park_vehicle(vehicle)
        print(f"Vehicle {vehicle.number} parked in slot {slot.slot_number}")
    except Exception as e:
        print(f"Error parking vehicle {vehicle.number}: {str(e)}")

def simulate_vehicle_exit(parking_lot: ParkingLot, vehicle: Vehicle, delay: float):
    """Simulate a vehicle exiting the parking lot after a delay."""
    time.sleep(delay)
    try:
        slot = parking_lot.remove_vehicle(vehicle)
        print(f"Vehicle {vehicle.number} removed from slot {slot.slot_number}")
    except Exception as e:
        print(f"Error remove vehicle {vehicle.number}: {str(e)}")


def main():
    # Create parking lot
    parking_lot = ParkingLot(
        levels=3,
        slots_per_level=10,
        number_of_entries=2,
        number_of_exits=2,
        parking_strategy=NearestSpotStrategy()
    )

    # Create some vehicles
    vehicles = [
        Car("CAR001"),
        Bike("BIKE001"),
        Truck("TRUCK001"),
        Car("CAR002"),
        Bike("BIKE002")
    ]

    # Simulate concurrent parking operations
    threads = []
    for i, vehicle in enumerate(vehicles):
        # Create entry thread
        entry_thread = threading.Thread(
            target=simulate_vehicle_entry,
            args=(parking_lot, vehicle, i * 0.5)
        )
        threads.append(entry_thread)
        entry_thread.start()

        # Create exit thread (after some delay)
        exit_thread = threading.Thread(
            target=simulate_vehicle_exit,
            args=(parking_lot, vehicle, i * 0.5 + 2.0)
        )
        threads.append(exit_thread)
        exit_thread.start()

    # Wait for all threads to complete
    for thread in threads:
        thread.join()

    # Print final status
    print("\nFinal Parking Lot Status:")
    print(f"Available slots: {parking_lot.get_available_slots()}")


if __name__ == "__main__":
    main()