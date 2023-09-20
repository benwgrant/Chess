import pygame
import math
import random
import engine
import polyglot

from init import *

from logic import *
from piece_movement import promote, en_passant
from engine import find_valid_board_states
import copy

colorTurn = 'w'
turnMove = 1

# board colors
color = None
white = (234, 233, 210)
black = (0, 0, 0)
blue = (75, 115, 153)

# effect colors
selectedBlueOnWhite = (117, 199, 232)
selectedBlueOnBlack = (38, 140, 204)
inCheckRed = (237, 62, 54)
captureRed = (247, 100, 99)

# board variables
current_position = fen_to_array("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
previous_position = []
colorTurn = "w"
selectedPiece = []  # first position is the square being selected, second position is the square it is being moved to
castling = False

# map coordinates to rank and file
coord_to_rank = {0: '8', 1: '7', 2: '6', 3: '5', 4: '4', 5:'3', 6: '2', 7: '1'}
coord_to_file = {0: 'a', 1: 'b', 2: 'c', 3: 'd', 4: 'e', 5:'f', 6: 'g', 7: 'h'}

pygame.mixer.init()


# load game sounds
pygame.mixer.music.load("./sfx/gamestart.wav")
gameStartSound = pygame.mixer.Sound("./sfx/gamestart.wav")
pygame.mixer.Sound.play(gameStartSound)

pygame.mixer.music.load("./sfx/regmove.wav")
moveSound = pygame.mixer.Sound("./sfx/regmove.wav")

pygame.mixer.music.load("./sfx/capture.wav")
captureSound = pygame.mixer.Sound("./sfx/capture.wav")

pygame.mixer.music.load("./sfx/castling.wav")
castlingSound = pygame.mixer.Sound("./sfx/castling.wav")

pygame.mixer.music.load("./sfx/check.wav")
checkSound = pygame.mixer.Sound("./sfx/check.wav")

pygame.mixer.music.load("./sfx/checkmate.wav")
checkmateSound = pygame.mixer.Sound("./sfx/checkmate.wav")

pygame.mixer.music.load("./sfx/stalemate.wav")
stalemateSound = pygame.mixer.Sound("./sfx/stalemate.wav")

isCheckmate = False
isStalemate = False


def CREATE_CHESSBOARD():
    WINDOW.blit(preferredBoard, (0,0))


# TODO: Move this function into Logic file
def COLOR_SQUARE(rank, file):
    if rank % 2 == 0:
        if file % 2 == 0:
            return "White"
        else:
            return "Black"
    else:
        if file % 2 == 0:
            return "Black"
        else:
            return "White"


# TODO: cover cases where the king is in check and the opponent castled

def PLAY_MOVE_SOUND():
    global current_position, previous_position, colorTurn

    if has_captured(previous_position, current_position):
        pygame.mixer.Sound.play(captureSound)
    if castling:
        pygame.mixer.Sound.play(castlingSound)
    elif is_in_check(current_position, colorTurn) != "Neither":
        pygame.mixer.Sound.play(checkSound)
    # elif hasCastled():
        # pygame.mixer.Sound.play(castleSound)
    else:
        pygame.mixer.Sound.play(moveSound)


def CHANGE_COLOR():
    global colorTurn

    if colorTurn == 'w':
        colorTurn = 'b'
    elif colorTurn == 'b':  
        colorTurn = 'w'

def update_game_position_table(current_position, colorTurn, valid_move, new_piece_position):
    global turnMove

    # update the move in the text file
    with open("game_position_table.txt", "a") as f:
        turnMove += 1

    f.close()

def CHANGE_CURRENT_POSITION(new_position):
    global current_position

    # check if board exists
    if not new_position:
        return

    current_position = new_position


def ENGINE_MOVE_PIECE(opening_book):

    move = polyglot.get_best_move(array_to_fen(current_position), opening_book)
    if move is not None:
        engine_choice = fen_to_array(move)

        # introduce a slight delay between 0 seconds and 1.5 seconds to give the appearance of the computer thinking
        delay = random.uniform(0, 1.5)
        time.sleep(delay)
    else:
        _, engine_choice = engine.minimax(current_position, engine.MAX_DEPTH, -math.inf, math.inf, True, 'b')
    valid_move = is_valid_move(current_position, engine_choice, colorTurn, True, True)[0]
    if valid_move == "White Checkmated":
        board.isCheckmate = True
        print("White Checkmated")
    if valid_move == "Black Checkmated":
        board.isCheckmate = True
        print("Black Checkmated")
    if check_stalemate(colorTurn) and valid_move not in ["White Checkmated", "Black Checkmated"]:
        board.isStalemate = True
        print("Stalemate")
    CHANGE_COLOR()
    CHANGE_CURRENT_POSITION(engine_choice)


# change board position based on player input
def MOVE_PIECES(mousePos):
    # return the modified array after an attempted move
    global previous_position, current_position, colorTurn, isCheckmate, isStalemate
    castling = False
    sp_copy = []

    # modified array after move
    new_current_position = copy.deepcopy(current_position)

    rank = math.floor(mousePos[1] / (HEIGHT / 8))
    file = math.floor(mousePos[0] / (WIDTH / 8))

    selectedPiece.append([rank, file])

    if len(selectedPiece) == 2: # two squares have been selected
        sp_copy = copy.deepcopy(selectedPiece)
        new_current_position[selectedPiece[1][0]][selectedPiece[1][1]] = new_current_position[selectedPiece[0][0]][selectedPiece[0][1]]
        new_current_position[selectedPiece[0][0]][selectedPiece[0][1]] = '0'
        selectedPiece.clear()

    # Update a pawn to queen if on the last rank
    promote_coord = promote(new_current_position)
    if promote_coord != []:
        if promote_coord[0] == 7:
            new_current_position[promote_coord[0]][promote_coord[1]] = 'q'
        if promote_coord[0] == 0:
            new_current_position[promote_coord[0]][promote_coord[1]] = 'Q'

    valid_move, new_piece_position = is_valid_move(current_position, new_current_position, colorTurn, True, False)

    if valid_move:
        previous_position.append(copy.deepcopy(current_position))
        current_position = new_current_position

        # update the move in the text file
        update_game_position_table(current_position, colorTurn, valid_move, new_piece_position)

        castling = is_castling(previous_position[-1], current_position, previous_position[-1][sp_copy[0][0]][sp_copy[0][1]], [sp_copy[1][0], sp_copy[1][1]])
        castle_update(previous_position[-1][sp_copy[0][0]][sp_copy[0][1]], [sp_copy[0][0], sp_copy[0][1]])

        if castling:
            current_position = castling

        en_passant(previous_position[-1], sp_copy[0], sp_copy[1])

        # play correct move sound
        PLAY_MOVE_SOUND()

        # change the color turn, white to black/black to white
        CHANGE_COLOR()

    if valid_move == "White Checkmated":
        isCheckmate = True
        print("White Checkmated")
    if valid_move == "Black Checkmated":
        isCheckmate = True
        print("Black Checkmated")
    if check_stalemate(colorTurn) and valid_move not in ["White Checkmated", "Black Checkmated"]:
        isStalemate = True
        print("Stalemate")


def DISPLAY_PIECE_EFFECTS():
    # blue highlight selection when a piece is selected
    global colorTurn, current_position

    if len(selectedPiece) == 1:
        # don't display effects if not the proper color turn
        if colorTurn == "w" and current_position[selectedPiece[0][0]][selectedPiece[0][1]].islower():
            selectedPiece.clear()
            return
        elif colorTurn == "b" and current_position[selectedPiece[0][0]][selectedPiece[0][1]].isupper():
            selectedPiece.clear()
            return

        # blue square around selected piece, changes shade based on color square
        if COLOR_SQUARE(selectedPiece[0][1], selectedPiece[0][0]) == "White":
            pygame.draw.rect(WINDOW, selectedBlueOnWhite, pygame.Rect(selectedPiece[0][1] * WIDTH // 8, selectedPiece[0][0] * HEIGHT // 8, WIDTH // 8, HEIGHT // 8))
        else:
            pygame.draw.rect(WINDOW, selectedBlueOnBlack, pygame.Rect(selectedPiece[0][1] * WIDTH // 8, selectedPiece[0][0] * HEIGHT // 8, WIDTH // 8, HEIGHT // 8))

        for square in find_valid_moves(current_position, selectedPiece[0]):
            # if the piece can be captured, draw a red frame around it
            if is_opposite_color(current_position[selectedPiece[0][0]][selectedPiece[0][1]], current_position[square[0]][square[1]]):
                pygame.draw.rect(WINDOW, captureRed, pygame.Rect(square[1] * WIDTH // 8, square[0] * HEIGHT // 8, WIDTH // 8, HEIGHT // 8))
            # otherwise, draw circles to empty squares the piece can move to
            else:
                pygame.draw.circle(WINDOW, black, (square[1] * WIDTH // 8 + (WIDTH // 16), square[0] * HEIGHT // 8 + (HEIGHT // 16)), WIDTH // 48)

    # a king is in check
    isCheck = is_in_check(current_position, colorTurn)
    if isCheck != "Neither":
        if isCheck == "White":
            for i, pieces in enumerate(current_position):
                for j, piece in enumerate(pieces):
                    if piece == "K":
                        pygame.draw.rect(WINDOW, inCheckRed, pygame.Rect(j * WIDTH // 8, i * HEIGHT // 8, WIDTH // 8, HEIGHT // 8))
        elif isCheck == "Black":
            for i, pieces in enumerate(current_position):
                for j, piece in enumerate(pieces):
                    if piece == "k":
                        pygame.draw.rect(WINDOW, inCheckRed, pygame.Rect(j * WIDTH // 8, i * HEIGHT // 8, WIDTH // 8, HEIGHT // 8))


def DISPLAY_BOARD_EFFECTS():
    global colorTurn, current_position, previous_position
    if len(previous_position) > 0:
        if isCheckmate and colorTurn == "b":
            for i, pieces in enumerate(current_position):
                for j, piece in enumerate(pieces):
                    if piece == "K":
                        WINDOW.blit(won, (j * WIDTH // 8, i * HEIGHT // 8))
                    elif piece == "k":
                        WINDOW.blit(bMate, (j * WIDTH // 8, i * HEIGHT // 8))
        elif isCheckmate and colorTurn == "w":
            for i, pieces in enumerate(current_position):
                for j, piece in enumerate(pieces):
                    if piece == "K":
                        WINDOW.blit(wMate, (j * WIDTH // 8, i * HEIGHT // 8))
                    elif piece == "k":
                        WINDOW.blit(won, (j * WIDTH // 8, i * HEIGHT // 8))
        elif isStalemate:
            for i, pieces in enumerate(current_position):
                for j, piece in enumerate(pieces):
                    if piece == "K" and colorTurn == "w":
                        WINDOW.blit(stalemate, (j * WIDTH // 8, i * HEIGHT // 8))
                    elif piece == "k" and colorTurn == "b":
                        WINDOW.blit(stalemate, (j * WIDTH // 8, i * HEIGHT // 8))


# displays pieces based on current board position
def DISPLAY_PIECES():
    # display all the piece pieces
    for i in range(8):
        for j in range(8):
            # black pieces
            if current_position[i][j] == "k":
                WINDOW.blit(blackKing, (j * WIDTH / 8, i * HEIGHT / 8))
            if current_position[i][j] == "q":
                WINDOW.blit(blackQueen, (j * WIDTH / 8, i * HEIGHT / 8))
            if current_position[i][j] == "r":
                WINDOW.blit(blackRook, (j * WIDTH / 8, i * HEIGHT / 8))
            if current_position[i][j] == "b":
                WINDOW.blit(blackBishop, (j * WIDTH / 8, i * HEIGHT / 8))
            if current_position[i][j] == "n":
                WINDOW.blit(blackKnight, (j * WIDTH / 8, i * HEIGHT / 8))
            if current_position[i][j] == "p":
                WINDOW.blit(blackPawn, (j * WIDTH / 8, i * HEIGHT / 8))
            # white pieces
            if current_position[i][j] == "K":
                WINDOW.blit(whiteKing, (j * WIDTH / 8, i * HEIGHT / 8))
            if current_position[i][j] == "Q":
                WINDOW.blit(whiteQueen, (j * WIDTH / 8, i * HEIGHT / 8))
            if current_position[i][j] == "R":
                WINDOW.blit(whiteRook, (j * WIDTH / 8, i * HEIGHT / 8))
            if current_position[i][j] == "B":
                WINDOW.blit(whiteBishop, (j * WIDTH / 8, i * HEIGHT / 8))
            if current_position[i][j] == "N":
                WINDOW.blit(whiteKnight, (j * WIDTH / 8, i * HEIGHT / 8))
            if current_position[i][j] == "P":
                WINDOW.blit(whitePawn, (j * WIDTH / 8, i * HEIGHT / 8))


# change board position to the last saved board position
def MAKE_PREVIOUS_TURN():
    global previous_position, current_position, colorTurn

    if len(previous_position) == 0:
        return

    current_position = previous_position[-1]
    previous_position.remove(current_position)
    selectedPiece.clear()

    if colorTurn == "w":
        colorTurn = "b"
    else:
        colorTurn = "w"

    PLAY_MOVE_SOUND()


# reset board to starting position
def RESET_PIECES():
    global current_position, colorTurn, isCheckmate, isStalemate
    current_position = fen_to_array("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
    selectedPiece.clear()
    colorTurn = "w"
    isCheckmate = False
    isStalemate = False

    pygame.mixer.Sound.play(gameStartSound)


# helper function
def DISPLAY_PIECE_MOVEMENT(rank, file):
    print(current_position[rank][file])


def print_boards(boards, delay):
    global current_position
    for board in boards:
        current_position = board
        time.sleep(delay)


def update_board(board_array):
    current_position = board_array
