from game import Game

if __name__ == "__main__":
    game = Game(6)
    game.add_ship("SH1", 2, [5, 1], [4, 4])
    game.add_ship("SH2", 2, [2, 2], [2, 5])
    game.start_game()