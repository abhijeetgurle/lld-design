from fire_strategy import RandomFireStrategy
from player import Player
from ship import Ship


class Game:
    def __init__(self, n: int) -> None:
        self.player_a = Player([1, 1], n, n // 2, RandomFireStrategy())
        self.player_b = Player([1, n // 2 + 1], n, n // 2, RandomFireStrategy())
        self.hit_coordinates: list[list[int]] = []

    def add_ship(self, name: str, size: int, start_pos_a: list[int], start_pos_b: list[int]) -> None:
        self.player_a.add_ship(Ship(name, start_pos_a, size))
        self.player_b.add_ship(Ship(name, start_pos_b, size))

    def start_game(self) -> None:
        first_player_turn = True

        while True:
            if first_player_turn:
                attack_coordinates = self.player_a.fire(self.player_b.start_pos, self.player_b.x_size, self.player_b.y_size, self.hit_coordinates)
                self.hit_coordinates.append(attack_coordinates)
                ship_hit = self.player_b.find_ship_hit(attack_coordinates)
                if ship_hit:
                    print(f"Player A’s turn: Missile fired at ({attack_coordinates[0]}, {attack_coordinates[1]}) : “Hit” : Ships Remaining - PlayerA:{self.player_a.get_ships_count()}, PlayerB:{self.player_b.get_ships_count()}")
                else:
                    print(
                        f"Player A’s turn: Missile fired at ({attack_coordinates[0]}, {attack_coordinates[1]}) : “Miss” : Ships Remaining - PlayerA:{self.player_a.get_ships_count()}, PlayerB:{self.player_b.get_ships_count()}")

                first_player_turn = False

            else:
                attack_coordinates = self.player_b.fire(self.player_a.start_pos, self.player_a.x_size,
                                                        self.player_a.y_size, self.hit_coordinates)
                self.hit_coordinates.append(attack_coordinates)
                ship_hit = self.player_a.find_ship_hit(attack_coordinates)
                if ship_hit:
                    print(
                        f"Player B’s turn: Missile fired at ({attack_coordinates[0]}, {attack_coordinates[1]}) : “Hit” : Ships Remaining - PlayerA:{self.player_a.get_ships_count()}, PlayerB:{self.player_b.get_ships_count()}")
                else:
                    print(
                        f"Player B’s turn: Missile fired at ({attack_coordinates[0]}, {attack_coordinates[1]}) : “Miss” : Ships Remaining - PlayerA:{self.player_a.get_ships_count()}, PlayerB:{self.player_b.get_ships_count()}")

                first_player_turn = True

            if self.player_a.get_ships_count() == 0:
                print("Game Over, Player B Won!!!")
                break
            elif self.player_b.get_ships_count() == 0:
                print("Game Over, Player A Won!!!")
                break