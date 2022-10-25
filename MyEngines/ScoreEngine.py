import chess
import time

PIECE_VALUES = {
    'K': 0,
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

    # If there is a checkmate possible increase the  score
    if new_board.is_checkmate():
        return 99999999

    return material_diff


def improved_score(new_board, turn):
    score = material_count(new_board, turn)

    # Compute space controlled by current color
    space = 0
    for square in chess.SQUARES:
        if new_board.is_attacked_by(turn, square):
            space += 1
        if new_board.is_attacked_by(not turn, square):
            space -= 1

    score += space * 1 / 32

    return score


num_pruned = 0
cache_hits = 0
positions = 0


def minimax_score(board, turn, cutoff=999999999, current_depth=0, max_depth=2, cache={}):
    global cache_hits, num_pruned, positions
    positions += 1

    if current_depth == max_depth or board.outcome():
        return material_count(board, turn)

    # recursively calculate best move
    # Make a list of all legal moves
    moves = list(board.legal_moves)

    best_move = None
    best_score = -float('inf')

    # Loop through each legal move
    for move in moves:

        # Copy the board and preform a move on copy of board
        new_board = board.copy()
        new_board.push(move)

        # if new_board.fen() not in cache:
        #     score = minimax_score(new_board, not turn, -best_score, current_depth + 1, max_depth, cache)
        #     cache[new_board.fen()] = (score, current_depth)
        # else:
        #     #     old_score, old_depth = cache[new_board.fen()]
        #     #     if old_depth > current_depth:
        #     #         score = minimax_score(new_board, turn, current_depth + 1, max_depth, cache)
        #     #         cache[new_board.fen()] = (score, current_depth)
        #     #     else:
        #     score, _ = cache[new_board.fen()]
        #     cache_hits += 1

        score = minimax_score(new_board, not turn, -best_score, current_depth + 1, max_depth, cache)

        if score > best_score:
            best_move = move
            best_score = score

        if score > cutoff:
            num_pruned += 1
            return -best_score

    # print("Opponent's best move is {}".format(best_move))
    return -best_score


class ScoreEngine:
    def __init__(self, score_function=material_count):
        self.score_function = minimax_score
        self.name = "ScoreEngine"

    def play(self, board):
        start_time = time.time()

        # Make a list of all legal moves
        moves = list(board.legal_moves)

        best_move = None
        best_score = -999999

        known_positions = {}

        # Loop through each legal move
        for move in moves:

            # Copy the board and preform a move on copy of board
            new_board = board.copy()
            new_board.push(move)

            score = self.score_function(new_board, board.turn, cache=known_positions)

            if score > best_score:
                best_move = move
                best_score = score
        print("Cache hits: {}. Prunes: {}. Positions: {}.".format(cache_hits, num_pruned, positions))
        print("Found best move: {} in {} seconds".format(best_move, time.time() - start_time))
        # print("Duplicate positions were seen times {}".format(sum(known_positions.values())))

        return best_move
