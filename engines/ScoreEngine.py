import chess
import random

from chess.engine import PlayResult

from strategies import MinimalEngine

PIECE_VALUES = {
    'K': 10,
    'Q': 9,
    'R': 5,
    'B': 3,
    'N': 3,
    'P': 1
}


def material_count(new_board, turn):
    # count material in the new position
    all_pieces = new_board.piece_map().values()
    material_diff = 0
    for piece in all_pieces:
        value = PIECE_VALUES[piece.symbol().upper()]
        if piece.color == turn:
            material_diff += value
        else:
            material_diff -= value
    return material_diff


def improved_score(new_board, turn):
    score = material_count(new_board, turn)

    # If there is a checkmate possible increase the  score
    if new_board.is_checkmate():
        score += 999999

    # Compute space controlled by current color
    space = 0
    for square in chess.SQUARES:
        if new_board.is_attacked_by(turn, square):
            space += 1
        if new_board.is_attacked_by(not turn, square):
            space -= 1

    score += space * 1 / 32

    # Remove hanging pieces from material count
    all_pieces = new_board.piece_map().items()

    for square, piece in all_pieces:
        if piece.color == turn:
            attack_count = len(new_board.attackers(not turn, square))
            defender_count = len(new_board.attackers(turn, square))
            if attack_count > defender_count:
                score -= PIECE_VALUES[piece.symbol().upper()]

    return score


class ScoreEngine(MinimalEngine):
    def __init__(self, *args, name=None):
        super().__init__(*args)
        self.name = name
        self.score_function = improved_score

    def search(self, board, time_limit, ponder, draw_offered):
        # Make a list of all legal moves
        moves = list(board.legal_moves)

        best_move = None
        best_score = -float('inf')

        # Loop through each legal move
        for move in moves:

            # Copy the board and preform a move on copy of board
            new_board = board.copy()
            new_board.push(move)

            # Call the score function
            score = self.score_function(new_board, board.turn)

            if score > best_score:
                best_move = move
                best_score = score

        return PlayResult(best_move)
