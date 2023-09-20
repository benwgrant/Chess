import chess
import chess.polyglot

def get_best_move(fen_string, opening_book):
    # Searches the tree of games to find if a position has been played, then plays it
    castling_options = [' b KQkq - 0 1', ' b KQk - 0 1', ' b KQq - 0 1', ' b KQ - 0 1', ' b K - 0 1', ' b Qkq - 0 1', ' b Qk - 0 1', ' b Qq - 0 1', ' b Q - 0 1', ' b kq - 0 1', ' b k - 0 1', ' b q - 0 1', ' b - - 0 1']
    best_move = None
    best_weight = 0
    best_new_fen = None
    engine_file = "openingbooks/" + opening_book + ".bin"
    with chess.polyglot.open_reader(engine_file) as reader:
        for castle_option in castling_options:
            fen = fen_string + castle_option
            board = chess.Board(fen)
            try:
                entries = list(reader.find_all(board))
                print(f"For castling option '{castle_option}', number of entries found in book: {len(entries)}")
                main_entry = reader.weighted_choice(board)
                move = main_entry.move
                if main_entry.weight > best_weight:
                    best_move = move
                    best_weight = main_entry.weight
                    board.push(move)  # Apply the move to the board
                    best_new_fen = board.fen()  # Get the FEN string of the new board
            except IndexError:
                print(f"No opening move found in book for castling option '{castle_option}'.")
                
    return best_new_fen
