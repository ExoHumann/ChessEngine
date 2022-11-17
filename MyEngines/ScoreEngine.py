from collections import namedtuple
from math import inf as INFINITY

import chess
import time

PIECE_VALUES = {
    chess.KING: 10000,
    chess.QUEEN: 900,
    chess.ROOK: 500,
    chess.BISHOP: 300,
    chess.KNIGHT: 300,
    chess.PAWN: 100
}


def evaluate_count(new_board):
    # count material in the new position
    all_pieces = new_board.piece_map().values()

    material_diff = 0

    for piece in all_pieces:
        value = PIECE_VALUES[piece.piece_type]

        if piece.color == new_board.turn:
            material_diff += value
        else:
            material_diff -= value


def material_count(board):
    # count material in the new position
    if board.is_checkmate():
        return INFINITY

    all_pieces = board.piece_map().values()
    material_diff = 0
    for piece in all_pieces:
        value = PIECE_VALUES[piece.piece_type]
        if piece.color == board.turn:
            material_diff -= value
        else:
            material_diff += value

    return material_diff


def improved_score(board):
    score = material_count(board)

    # Compute space controlled by current color
    space = 0
    for square in chess.SQUARES:
        if board.is_attacked_by(board.turn, square):
            space += 100
        if board.is_attacked_by(not board.turn, square):
            space -= 100

    score += space * 1 / 64

    return score

num_pruned = 0
cache_hits = 0
positions = 0

Config = namedtuple("Config",
                    ['prune', 'cache', 'sort', 'max_depth'],
                    defaults=[True, True, True, 4])


def minimax_score(board, alpha=-INFINITY, beta=INFINITY, current_depth=0,
                  cache=(), config=Config(), sort_heuristic=material_count, timelimit=1500000000):
    global cache_hits, num_pruned, positions
    positions += 1

    outcome = board.outcome(claim_draw=False)

    if outcome:
        if outcome.winner is None:
            return 0
        else:
            return 10000 / current_depth  # prefer shallower checkmates

    turn = board.turn

    if current_depth == config.max_depth or outcome or board.is_checkmate() or board.is_stalemate():  # or (timelimit and time.time() > timelimit):
        return improved_score(board)

    # Make a list of all legal moves
    moves = list(board.legal_moves)
    best_move = None
    best_score = -INFINITY

    children = []

    # Loop through each legal move
    for move in moves:
        # Make the move in the current position
        board.push(move)

        # Sorted score
        sort_score = sort_heuristic(board) if config.sort else 0

        # Take the move back
        board.pop()

        children.append((sort_score, move))

    for _, move in sorted(children, key=lambda x: x[0], reverse=True):
        board.push(move)

        if config.cache:
            key = board._transposition_key()
            score, cached_depth = cache[key] if key in cache else (0, 0)

            # Compute depth of score estimate
            new_depth = config.max_depth - current_depth

            # If we could get a deeper estimate than what is in the cache
            if new_depth > cached_depth:
                score = minimax_score(board, -alpha, -beta, current_depth + 1, cache, config, sort_heuristic)

                cache[key] = (score, new_depth)
            else:
                cache_hits += 1
        else:
            score = minimax_score(board, -alpha, -beta, current_depth + 1, cache, config, sort_heuristic)

        board.pop()

        if score > best_score:
            best_move = move
            best_score = score
            alpha = max(best_score, alpha)

        if config.prune:
            if score >= beta:
                num_pruned += 1
                return -best_score

    # print("Opponent's best move is {}".format(best_move))
    return -best_score


class ScoreEngine:
    def __init__(self, score_function=material_count, config=Config()):
        self.config = config
        self.score_function = minimax_score
        self.name = "ScoreEngine"
        self.known_positions = {}
        self.visited_positions = set()

    def store_position(self, board):
        key = board._transposition_key()

        if key in self.visited_positions:
            self.known_positions[key] = (0, INFINITY)
        else:
            self.visited_positions.add(key)

    def cached_score_difference(self, board):
        key = board._transposition_key()

        if key in self.known_positions:
            score, _ = self.known_positions[key]
            return score
        return material_count(board)

    def play(self, board):
        start_time = time.time()

        self.store_position(board)

        # Make a list of all legal moves
        moves = list(board.legal_moves)

        best_move = None
        best_score = -INFINITY

        # Loop through each legal move
        for move in moves:
            # Copy the board and preform a move on copy of board
            new_board = board.copy()
            new_board.push(move)

            if self.score_function == minimax_score:
                score = self.score_function(new_board,
                                            cache=self.known_positions,
                                            config=self.config,
                                            current_depth=1)
            else:
                score = self.score_function(new_board)

            if score > best_score:
                best_move = move
                best_score = score

        board.push(best_move)
        self.store_position(board)
        board.pop()

        print("Cache hits: {}. Prunes: {}. Positions: {}.".format(cache_hits, num_pruned, positions))

        print("Found best move: {} in {} seconds on move {}".format(best_move, time.time() - start_time,
                                                                    len(board.move_stack)))

        # print("Duplicate positions were seen times {}".format(sum(known_positions.values())))

        return best_move
