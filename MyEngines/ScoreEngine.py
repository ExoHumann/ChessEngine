from collections import namedtuple
from math import inf as INFINITY
import random

import chess
import dis
import time

PIECE_VALUES = {
    chess.KING: 0,
    chess.QUEEN: 900,
    chess.ROOK: 500,
    chess.BISHOP: 320,
    chess.KNIGHT: 310,
    chess.PAWN: 100
}


def material_count(board):
    # count material in the new position
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


class ScoreEngine:

    def __init__(self, max_depth=15):
        self.max_depth = max_depth
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

    def get_all_moves(self, board, moves):
        """
        Return a scored list of moves to search over
        """
        children = []

        # generate children positions from legal moves
        for move in moves:
            board.push(move)  # apply the current candidate move
            sort_score = self.cached_score_difference(board)
            board.pop()  # undo the candidate move

            children.append((sort_score, move))

        return children

    def loud_moves_only(self, board, moves):
        """
        Return a scored list of moves to search over
        """
        children = []

        was_check = board.is_check()

        # generate children positions from legal moves
        for move in moves:

            is_capture = board.is_capture(move)

            # check if move is a capture or check
            board.push(move)  # apply the current candidate move

            if was_check or board.is_check() or is_capture:
                sort_score = self.cached_score_difference(board)
                children.append((sort_score, move))

            board.pop()  # undo the candidate move

        # if children:
        #     print(board.fen())
        #     print("Found {} loud moves.".format(len(children)))

        return children

    def quiescence_search(self, board):
        key = board._transposition_key()
        if key in self.known_positions:
            score, _ = self.known_positions[key]
        else:
            print("quiesence_search")
            score = self.minimax_score(board, current_depth=1, timelimit=time.time() + 1,
                                       sorted_moves=self.loud_moves_only,
                                       evaluation_function=self.cached_score_difference,
                                       caching=False, early_stop=True, max_depth=self.max_depth)

            self.known_positions[key] = (score, 0)
        return score

    def minimax_score(self, board, alpha=-INFINITY, beta=INFINITY, current_depth=0,
                      max_depth=4, timelimit=None, sorted_moves=get_all_moves,
                      evaluation_function=material_count, caching=True, early_stop=False):

        global cache_hits, num_pruned, positions
        positions += 1

        outcome = board.outcome(claim_draw=False)

        turn = board.turn

        if outcome:
            if outcome.winner is None:
                return 0
            else:
                return 100000 / current_depth  # prefer shallower checkmates

        if current_depth == max_depth:
            return evaluation_function(board)

        # Make a list of all legal moves
        moves = list(board.legal_moves)

        best_move = None
        best_score = -INFINITY

        if early_stop and not board.is_check():
            best_score = -evaluation_function(board)

        children = sorted_moves(board, moves)

        if len(children) == 0:
            return evaluation_function(board)

        for _, move in sorted(children, key=lambda x: x[0], reverse=True):
            board.push(move)

            if timelimit and time.time() > timelimit:
                score = self.cached_score_difference(board)
            else:

                key = board._transposition_key()

                score, cached_depth = self.known_positions[key] \
                    if key in self.known_positions else (0, 0)

                # Compute depth of score estimate
                new_depth = max_depth - current_depth

                # If we could get a deeper estimate than what is in the cache
                if new_depth > cached_depth or not caching:
                    score = self.minimax_score(board, -beta, -alpha, current_depth + 1,
                                               max_depth, timelimit, sorted_moves, evaluation_function)

                    self.known_positions[key] = (score, new_depth)
                else:
                    cache_hits += 1

            board.pop()

            if score > best_score:
                best_move = move
                best_score = score
                alpha = max(best_score, alpha)

            if score >= beta:
                num_pruned += 1
                return -best_score

        # print("Opponent's best move is {}".format(best_move))
        return -best_score

    def play(self, board, time_limit, ponder):
        start_time = time.time()


        # target 50 moves
        target_time = time_limit / 1000
        print("Trying to make move in {} seconds".format(target_time))
        timelimit = time.time() + target_time

        # start_time = time.time()
        self.store_position(board)

        # Make a list of all legal moves
        moves = list(board.legal_moves)

        # Loop through each legal move
        for depth in range(1, self.max_depth + 1):

            print("Trying depth {}".format(depth))

            best_moves = []
            best_score = -INFINITY

            for move in moves:
                # Copy the board and preform a move on copy of board
                new_board = board.copy()
                new_board.push(move)

                score = self.minimax_score(new_board, current_depth=1, max_depth=depth,
                                           timelimit=time_limit,
                                           sorted_moves=self.get_all_moves,
                                           evaluation_function=self.quiescence_search)

                if score > best_score:
                    best_moves = [move]
                    best_score = score
                elif score == best_score:
                    best_moves.append(move)

            # print("Found {} moves with score {}".format(len(best_moves), best_score))

            if timelimit and time.time() > timelimit:
                print("Ran out of time at depth {}".format(depth))
                break

        best_move = random.choice(best_moves)
        board.push(best_move)
        self.store_position(board)
        board.pop()

        print("Cache hits: {}. Prunes: {}. Positions: {}.".format(cache_hits, num_pruned, positions))
        # print("Found {} moves with score {}".format(len(best_moves), best_score))
        print("Chose random best move: {} with score {} in {} seconds on move {}".format(best_move, best_score,
                                                                                         time.time() - start_time,
                                                                                         len(board.move_stack)))
        return best_move
