from typing import Optional

from fire_strategy import FireStrategy
from ship import Ship


class Player:
    def __init__(self, start_pos: list[int], x_size: int, y_size: int, fire_strategy: FireStrategy) -> None:
        self.start_pos = start_pos
        self.x_size = x_size
        self.y_size = y_size
        self.ships: list[Ship] = []
        self.fire_strategy = fire_strategy

    def is_ship_in_bounds(self, ship: Ship) -> bool:
        if (self.start_pos[0] <= ship.start_pos[0] <= self.start_pos[0] + self.x_size
                and self.start_pos[1] <= ship.start_pos[1] <= self.start_pos[1] + self.y_size
                and self.start_pos[0] <= ship.start_pos[0] + ship.size <= self.start_pos[0] + self.x_size
                and self.start_pos[1] <= ship.start_pos[1] + ship.size <= self.start_pos[1] + self.y_size):
            return True

        return False

    def is_ship_overlapping(self, ship: Ship) -> bool:
        for cur_ship in self.ships:
            x_overlap = cur_ship.start_pos[0] < ship.start_pos[0] + ship.size and ship.start_pos[0] < \
                        cur_ship.start_pos[0] + cur_ship.size
            y_overlap = cur_ship.start_pos[1] < ship.start_pos[1] + ship.size and ship.start_pos[1] < \
                        cur_ship.start_pos[1] + cur_ship.size
            if x_overlap and y_overlap:
                return True

        return False

    def add_ship(self, ship: Ship) -> None:
        if self.is_ship_overlapping(ship):
            raise Exception("Ship already overlapping with another ship")

        if not self.is_ship_in_bounds(ship):
            raise Exception("Ship outside of user bounds")
        
        self.ships.append(ship)

    def fire(self, enemy_start_pos: list[int], enemy_x_size: int, enemy_y_size: int, hit_coordinates: list[list[int]]) -> list[int]:
        coordinates = self.fire_strategy.get_coordinates(enemy_start_pos, enemy_x_size, enemy_y_size, hit_coordinates)
        if not coordinates:
            raise Exception("No coordinates left to attack")

        return coordinates

    def find_ship_hit(self, attack_coordinates: list[int]) -> Optional[Ship]:
        for cur_ship in self.ships:
            if cur_ship.is_hit(attack_coordinates):
                self.ships.remove(cur_ship)
                return cur_ship

        return None

    def get_ships_count(self) -> int:
        return len(self.ships)

