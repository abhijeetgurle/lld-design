class Ship:
    def __init__(self, name: str, start_pos: list[int], size: int) -> None:
        self.name = name
        self.start_pos = start_pos
        self.size = size

    def is_hit(self, hit_position: list[int]) -> bool:
        if self.start_pos[0] <= hit_position[0] < self.start_pos[0] + self.size and self.start_pos[1] <= hit_position[1] < self.start_pos[1] + self.size:
            return True
        return False

