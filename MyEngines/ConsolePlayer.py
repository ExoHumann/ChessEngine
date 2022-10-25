from time import sleep

import chess
import sys


class ConsolePlayer(object):
    def __init__(self):
        self.name = "ConsolePlayer"

    def play(self, board):
        while True:
            try:
                m = input("Enter your move")
            except ValueError:
                print("Invalid move")
                m = None
            move = chess.Move.from_uci(m)
            if board.is_legal(move):
                break
            print("Illegal move")

        return move

