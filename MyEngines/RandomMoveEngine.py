import random


class RandomMoveEngine(object):

    def __init__(self):
        self.name = "RandomMoveEngine"

    def play(self, board, time_limit, ponder):
        moves = list(board.legal_moves)
        return random.choice(moves)
