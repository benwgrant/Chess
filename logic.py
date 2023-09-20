import re
import time
import copy

from piece_movement import *

white_q_castle = True
white_k_castle = True
black_q_castle = True
black_k_castle = True

en_passant_available = [0, 0, 0, 0]


def fen_to_array(fen):
    # Helper function, turns 'test' into ['t', 'e', 's', 't']
    def split(word):
        return [char for char in word]

    # Helper function, inserts a string within a string at the specified index
    def insert(source_str, insert_str, pos):
        return source_str[:pos] + insert_str + source_str[pos:]

    # Split the FEN by each rank
    board_array = fen.split("/")

    # Trim the extra information off the FEN
    first_rank = board_array[7]
    board_array[7] = first_rank[0:8]

    # Parse number for whitespaces into 0's in the right position
    for i in range(8):
        rank = board_array[i]
        for j in range(len(rank)):
            if re.match("[1-8]", rank[j]):
                board_array[i] = board_array[i].replace(rank[j], "0" * int(rank[j]), 1)

    # Use split function to turn into a 2d array
    for i in range(8):
        board_array[i] = split(board_array[i])

    return board_array


# STRICTLY FOR BLACK - THE FEN HAS A "b" TO INDICATE IT IS BLACK'S TURN
def array_to_fen(board_array):
    fen = ''
    for i in range(8):
        empty = 0
        for j in range(8):
            if board_array[i][j] == "0":
                empty += 1
            else:
                if empty != 0:
                    fen += str(empty)
                    empty = 0
                fen += board_array[i][j]
        if empty != 0:
            fen += str(empty)
        if i != 7:
            fen += '/'
    return fen


def is_valid_move(prev_board_array, cur_board_array, turnColor, update_en_passant=True, update_castling_flags=True):
    global en_passant_available
    if prev_board_array == cur_board_array or type(cur_board_array) == type(None):
        return (False, None)
    # Find which piece moves, and the starting and end position
    prev_pos = [10, 10]
    cur_pos = [10, 10]
    piece = None

    # Find the piece's start position
    for i in range(0, 8):
        for j in range(0, 8):
            # If this current spot on the board is 0 and last move it was not 0, this is where the piece moved from
            if cur_board_array[i][j] == "0" and prev_board_array[i][j] != "0":
                prev_pos = [i, j]
                piece = prev_board_array[i][j]
 

    # If it's not your turn, then the move is invalid
    if not piece or (piece.islower() and turnColor == 'w') or (piece.isupper() and turnColor == 'b'):
        return (False, None)


    # Find the piece's end position
    for i in range(0, 8):
        for j in range(0, 8):
            # If last move this spot was 0 or the opposite color, and now it is not 0 and not the opposite color,
            # this is where the piece currently lies
            if ((prev_board_array[i][j] == "0" or is_opposite_color(prev_board_array[i][j], piece)) and
                    (cur_board_array[i][j] != "0" and not is_opposite_color(cur_board_array[i][j], piece))):
                cur_pos = [i, j]
 

    # start2 = time.time_ns()
    if is_castling(prev_board_array, cur_board_array, piece, cur_pos, update_castling_flags):
        return (True, cur_pos)
    # end2 = time.time_ns()

    # start3 = time.time_ns()
    # If the piece moved to a valid position (based on what type of piece), then return true
    if cur_pos not in find_valid_moves(prev_board_array, prev_pos):
        return (False, None)
    # end3 = time.time_ns()

    # Update castling parameters
    if update_castling_flags:
        castle_update(piece, prev_pos)

    # En-passant logic
    if update_en_passant:
        if piece in ['P', 'p'] and abs(prev_pos[0] - cur_pos[0]) == 2:
            en_passant_available = [piece, [cur_pos[0], cur_pos[1] - 1], [cur_pos[0], cur_pos[1] + 1], cur_pos[1]]
        else:
            en_passant_available = []

    # start4 = time.time_ns()
    # If the player moving the piece is in check after the move, the move is invalid
    check = is_in_check(cur_board_array, turnColor)
    # end4 = time.time_ns()

    # print("Time to find prev_pos: " + str(end0 - start0))
    # print("Time to find cur_pos: " + str(end1 - start1))
    # print("Time to check castling: " + str(end2 - start2))
    # print("Time to find valid moves: " + str(end3 - start3))
    # print("Time to check check: " + str(end4 - start4))

    if check == "Both":
        return (False, None)
    if check == "White" and turnColor == 'w':
        return (False, None)
    if check == "Black" and turnColor == 'b':
        return (False, None)
    if check == "White Checkmated":
        return ("White Checkmated", None)
    if check == "Black Checkmated":
        return ("Black Checkmated", None)
    if check == "Stalemate":
        return ("Stalemate", None)

    return (True, cur_pos)



def find_valid_moves(board_array, piece_pos):
    # returns 2d list of all valid moves a piece can make i.e. [[x,y], [x,y], ..]
    piece = board_array[piece_pos[0]][piece_pos[1]]

    if piece in ['P', 'p']:
        return pawn_moves(board_array, piece_pos, en_passant_available)
    elif piece in ['R', 'r']:
        return rook_moves(board_array, piece_pos)
    elif piece in ['N', 'n']:
        return knight_moves(board_array, piece_pos)
    elif piece in ['B', 'b']:
        return bishop_moves(board_array, piece_pos)
    elif piece in ['Q', 'q']:
        return queen_moves(board_array, piece_pos)
    elif piece in ['K', 'k']:
        return king_moves(board_array, piece_pos)
    else:
        return []


def is_in_check(board_array, turnColor):
    # Returns White/Black/Both/None depending on which king(s) are in check
    # Find the kings
    white_king_pos = []
    white_valid_moves = []
    black_king_pos = []
    black_valid_moves = []
    for i in range(0, 8):
        for j in range(0, 8):
            cur_piece = board_array[i][j]
            if cur_piece == 'K':
                white_king_pos = [i, j]
            elif cur_piece == 'k':
                black_king_pos = [i, j]
            if cur_piece.isupper():
                for coord in find_valid_moves(board_array, [i, j]):
                    white_valid_moves.append(coord)
            elif cur_piece.islower():
                for coord in find_valid_moves(board_array, [i, j]):
                    black_valid_moves.append(coord)

    # print("WM", white_valid_moves)
    # print("BM", black_valid_moves)
    # print("WK:", white_king_pos)
    # print( "BK:", black_king_pos)
    # print("====================")

    white_checked = False
    black_checked = False

    if white_king_pos in black_valid_moves:
        white_checked = True
    if black_king_pos in white_valid_moves:
        black_checked = True

    if white_checked and black_checked:
        return "Both"

    if white_checked:
        if turnColor == 'b':
            checkmate = True
            for board in valid_boards(board_array, 'w'):
                if is_in_check(board, 'w') in ["Black", "Neither"]:
                    # Debugging purposes
                    # print('\n'.join(' '.join(str(x) for x in row) for row in board))
                    # print(is_in_check(board, 'w'))
                    # print("=================")
                    checkmate = False
                    break
            if checkmate:
                return "White Checkmated"
        return "White"

    if black_checked:
        if black_checked:
            if turnColor == 'w':
                checkmate = True
                for board in valid_boards(board_array, 'b'):
                    if is_in_check(board, 'b') in ["White", "Neither"]:
                        # Debugging purposes
                        # print('\n'.join(' '.join(str(x) for x in row) for row in board))
                        # print(is_in_check(board, 'b'))
                        # print("=================")
                        checkmate = False
                        break
                if checkmate:
                    return "Black Checkmated"
        return "Black"
    else:
        return "Neither"


# def is_in_check(board_array, turnColor):
#     king_pos = {'K': None, 'k': None}
#     opponent_valid_moves = set()
#     opponent_pieces = 'abcdefghijklmnopqrstuvwxyz' if turnColor == 'w' else 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'

#     # Find the kings and calculate valid moves for opponent's pieces
#     for i in range(8):
#         for j in range(8):
#             cur_piece = board_array[i][j]
#             if cur_piece == 'K' or cur_piece == 'k':
#                 king_pos[cur_piece] = [i, j]
#             if cur_piece in opponent_pieces:
#                 for coord in find_valid_moves(board_array, [i, j]):
#                     opponent_valid_moves.add(tuple(coord))

#     # Check if kings are under attack
#     king_checked = { 'K': tuple(king_pos['K']) in opponent_valid_moves if king_pos['K'] else False,
#                  'k': tuple(king_pos['k']) in opponent_valid_moves if king_pos['k'] else False }


#     # Additional logic for checkmate/stalemate would go here...

#     if king_checked['K'] and king_checked['k']:
#         return "Both"
#     elif king_checked['K']:
#         return "White"
#     elif king_checked['k']:
#         return "Black"
#     else:
#         return "Neither"



def check_stalemate(colorTurn):
    white_moves = valid_boards(board.current_position, 'w')
    black_moves = valid_boards(board.current_position, 'b')
    stalemate_white = True
    stalemate_black = True

    for move in white_moves:
        if is_valid_move(board.current_position, move, 'w', False, False)[0]:
            stalemate_white = False

    for move in black_moves:
        if is_valid_move(board.current_position, move, 'b', False, False)[0]:
            stalemate_black = False

    if (stalemate_white and colorTurn == 'w') or (stalemate_black and colorTurn == 'b'):
        return "Stalemate"

    return None


def valid_boards(board_array, turnColor):
    valid_board_list = []
    for i in range(0, 8):
        for j in range(0, 8):
            piece = board_array[i][j]
            if piece.isupper() and turnColor == 'w':
                valid_moves = find_valid_moves(board_array, [i, j])
                for move in valid_moves:
                    board_copy = copy.deepcopy(board_array)
                    board_copy[i][j] = '0'
                    board_copy[move[0]][move[1]] = piece
                    valid_board_list.append(board_copy)
            elif piece.islower() and turnColor == 'b':
                valid_moves = find_valid_moves(board_array, [i, j])
                for move in valid_moves:
                    board_copy = copy.deepcopy(board_array)
                    board_copy[i][j] = '0'
                    board_copy[move[0]][move[1]] = piece
                    valid_board_list.append(board_copy)

    return valid_board_list


def is_castling(prev_board_array, cur_board_array, piece, cur_pos, update_flags=True):
    # Returns board for the type of castling being attempted
    global white_q_castle
    global white_k_castle
    global black_q_castle
    global black_k_castle

    cur_board_copy = copy.deepcopy(cur_board_array)

    for i in range(0, 8):
        for j in range(0, 8):
            if cur_board_copy[i][j] == piece:
                cur_pos = [i, j]

    if piece == 'K':
        if cur_pos == [7, 0] and white_q_castle:
            if prev_board_array[7][1] == '0' and prev_board_array[7][2] == '0' and prev_board_array[7][3] == '0':
                for board in valid_boards(prev_board_array, 'b'):
                    if board[7][1] != '0' or board[7][2] != '0' or board[7][3] != '0' or is_in_check(prev_board_array, 'b') in ['White', 'White Checkmated']:
                        return False
                cur_board_copy[7][0] = '0'
                cur_board_copy[7][1] = 'K'
                cur_board_copy[7][2] = 'R'
                cur_board_copy[7][4] = '0'
                if update_flags:
                    white_q_castle = False
                return cur_board_copy
        elif cur_pos == [7, 7] and white_k_castle:
            if prev_board_array[7][5] == '0' and prev_board_array[7][6] == '0':
                for board in valid_boards(prev_board_array, 'b'):
                    if board[7][5] != '0' or board[7][6] != '0' or is_in_check(prev_board_array, 'b') in ['White', 'White Checkmated']:
                        return False
                cur_board_copy[7][4] = '0'
                cur_board_copy[7][5] = 'R'
                cur_board_copy[7][6] = 'K'
                cur_board_copy[7][7] = '0'
                if update_flags:
                    white_k_castle = False
                return cur_board_copy
    elif piece == 'k':
        if cur_pos == [0, 0] and black_q_castle:
            if prev_board_array[0][1] == '0' and prev_board_array[0][2] == '0' and prev_board_array[0][3] == '0':
                for board in valid_boards(prev_board_array, 'w'):
                    if board[0][1] != '0' or board[0][2] != '0' or board[0][3] != '0' or is_in_check(prev_board_array, 'w') in ['Black', 'Black Checkmated']:
                        return False
                cur_board_copy[0][0] = '0'
                cur_board_copy[0][1] = 'k'
                cur_board_copy[0][2] = 'r'
                cur_board_copy[0][4] = '0'
                if update_flags:
                    black_q_castle = False
                return cur_board_copy
        elif cur_pos == [0, 7] and black_k_castle:
            if prev_board_array[0][5] == '0' and prev_board_array[0][6] == '0':
                for board in valid_boards(prev_board_array, 'w'):
                    if board[0][5] != '0' or board[0][6] != '0' or is_in_check(prev_board_array, 'w') in ['Black', 'Black Checkmated']:
                        return False
                cur_board_copy[0][4] = '0'
                cur_board_copy[0][5] = 'k'
                cur_board_copy[0][6] = 'r'
                cur_board_copy[0][7] = '0'
                if update_flags:
                    black_k_castle = False
                return cur_board_copy

    return False


def castle_update(piece, prev_pos):
    global white_q_castle
    global white_k_castle
    global black_q_castle
    global black_k_castle
    if piece == 'K':
        white_q_castle = False
        white_k_castle = False
    elif piece == 'k':
        black_q_castle = False
        black_k_castle = False
    elif piece == 'R' and prev_pos == [7, 7]:
        white_k_castle = False
    elif piece == 'R' and prev_pos == [7, 0]:
        white_q_castle = False
    elif piece == 'r' and prev_pos == [0, 7]:
        black_k_castle = False
    elif piece == 'r' and prev_pos == [0, 0]:
        black_q_castle = False


def has_captured(previous_position, current_position):
    if len(previous_position) == 0:
        return False

    for i in range(8):
        for j in range(8):
            if current_position[i][j] != previous_position[-1][i][j] and current_position[i][j] != '0' and previous_position[-1][i][j] != '0':
                return True
    return False


def main():
    default = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"


if __name__ == '__main__':
    main()