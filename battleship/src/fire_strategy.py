from abc import ABC, abstractmethod
import random
from typing import Optional


class FireStrategy(ABC):
    @abstractmethod
    def get_coordinates(self, start_pos: list[int], x_size: int, y_size: int, hit_coordinates: list[list[int]]) -> list[int]:
        pass


class RandomFireStrategy(FireStrategy):
    def get_coordinates(self, start_pos: list[int], x_size: int, y_size: int, hit_coordinates: list[list[int]]) -> Optional[list[int]]:
        i = 0
        while True:
            x = random.randint(start_pos[0], start_pos[0] + x_size - 1)
            y = random.randint(start_pos[1], start_pos[1] + y_size - 1)
            if [x, y] not in hit_coordinates:
                return [x, y]

            i += 1
            if i == ((x_size - start_pos[0]) * (y_size - start_pos[1])):
                return None