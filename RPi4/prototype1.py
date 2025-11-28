import RPi.GPIO as GPIO
import time, random, math
import board, neopixel
import chess, stockfish
from chess import engine
import chess.pgn
import requests
from io import StringIO


# ERROR:
# Hall[6][4] always HIGH
LED = board.D18
GPIO.setmode(GPIO.BCM)
ORDER = neopixel.GRB
color = {
    ' ': (0, 0, 0),
    'R': (255, 0, 0),
    'G': (0, 255, 0),
    'B': (0, 0, 255),
    'W': (170, 170, 170),
    'Y': (255, 255, 0),
    'P': (128, 0, 128),
    'C': (0, 255, 255)
}

def getPuzzle():
    url = "https://lichess.org/api/puzzle/next"
    r = requests.get(url)
    r.raise_for_status()
    
    data = r.json()
    puzzle = data["puzzle"]
    game = data["game"]
    pgn_text = game['pgn']
    fake_pgn = f"[Event \"?\"]\n\n1. {pgn_text}"
    pgn = chess.pgn.read_game(StringIO(fake_pgn))
    sol = list(map(chess.Move.from_uci, puzzle["solution"]))
    tmpBoard = pgn.end().board()
    return tmpBoard, sol[::-1]

class ChessBoard():
    def __init__(self, chessgame=1):
        self.H_OUT = [10, 9, 11, 5, 6, 13, 19, 26]
        self.H_IN = [25, 8, 7, 1, 12, 16, 20, 21]
        #self.H_OUT = [19, 21, 23, 29, 31, 33, 35, 37]
        #self.H_IN = [22, 24, 26, 28, 32, 36, 38, 40]
        self.initialize_hall()
        bright = float(input('Enter brightness- '))
        self.strip = neopixel.NeoPixel(LED, 4*len(self.H_OUT)*len(self.H_IN), brightness=bright, auto_write=False, pixel_order=ORDER)
        self.strip.fill((0, 0, 0))
        self.strip.show()
        self.grid = [[0 for _ in range(len(self.H_OUT))] for _ in range(len(self.H_IN))]
        self.prev = [[self.grid[i][j] for j in range(len(self.H_OUT))] for i in range(len(self.H_IN))]

        self.square = [
            [[223, 224, 253, 254], [225, 226, 251, 252], [227, 228, 249, 250], [229, 230, 247, 248], [231, 232, 245, 246], [233, 234, 243, 244], [235, 236, 241, 242], [237, 238, 239, 240]],
            [[191, 192, 221, 222], [193, 194, 219, 220], [195, 196, 217, 218], [197, 198, 215, 216], [199, 200, 213, 214], [201, 202, 211, 212], [203, 204, 209, 210], [205, 206, 207, 208]],
            [[159, 160, 189, 190], [161, 162, 187, 188], [163, 164, 185, 186], [165, 166, 183, 184], [167, 168, 181, 182], [169, 170, 179, 180], [171, 172, 177, 178], [173, 174, 175, 176]],
            [[127, 128, 157, 158], [129, 130, 155, 156], [131, 132, 153, 154], [133, 134, 151, 152], [135, 136, 149, 150], [137, 138, 147, 148], [139, 140, 145, 146], [141, 142, 143, 144]],
            [[95, 96, 125, 126], [97, 98, 123, 124], [99, 100, 121, 122], [101, 102, 119, 120], [103, 104, 117, 118], [105, 106, 115, 116], [107, 108, 113, 114], [109, 110, 111, 112]],
            [[64, 65, 93, 94], [66, 67, 91, 92], [68, 69, 89, 90], [70, 71, 87, 88], [72, 73, 85, 86], [74, 75, 83, 84], [76, 77, 81, 82], [78, 79, 80, 80]],
            [[32, 33, 62, 63], [34, 35, 60, 61], [36, 37, 58, 59], [38, 39, 56, 57], [40, 41, 54, 55], [42, 43, 52, 53], [44, 45, 50, 51], [46, 47, 48, 49]],
            [[0, 1, 30, 31], [2, 3, 28, 29], [4, 5, 26, 27], [6, 7, 24, 25], [8, 9, 22, 23], [10, 11, 20, 21], [12, 13, 18, 19], [14, 15, 16, 17]]
        ]
        
        game_modes = {
            1 : 'No Suggestions',
            2 : 'All Suggestions',
            3 : 'White Suggestions Only',
            4 : 'Black Suggestions Only'
        }
        print("Select Game Mode:")
        for key, value in game_modes.items():
            print(f"{key}: {value}")
        self.game_mode = int(input("Enter game mode (1-4): "))
        
        self.suggestion_W = 1 if self.game_mode in [2,3] else 0
        self.suggestion_B = 1 if self.game_mode in [2,4] else 0
        
        self.parse_board = lambda board:[row.split() for row in str(board).split('\n')]
        self.parse_grid = lambda board: [[(1 if cell == '.' else 0) for cell in row] for row in self.parse_board(board)]
        if chessgame==1:
            self.engine = engine.SimpleEngine.popen_uci("/usr/games/stockfish")
            self.engine.configure({"Threads": 2, "Hash": 512})
        
            self.reset_board()
        if chessgame == 2:
            self.engine = engine.SimpleEngine.popen_uci("/usr/games/stockfish")
            self.engine.configure({"Threads": 2, "Hash": 512})
            self.board = chess.Board()
            self.board.reset()

    def initialize_hall(self):
        for pin in self.H_OUT:
            GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        for pin in self.H_IN:
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, GPIO.LOW)

    def read_hall(self):
        for i in range(len(self.H_IN)):
            GPIO.output(self.H_IN[i], GPIO.HIGH)
            time.sleep(0.001)
            for j in range(len(self.H_OUT)):
                self.grid[i][j] = GPIO.input(self.H_OUT[j])
            GPIO.output(self.H_IN[i], GPIO.LOW)
        self.grid[6][4] = 0  # TEMP FIX
        return self.grid

    def update_leds(self, pattern):
        for i in range(len(self.H_IN)):
            for j in range(len(self.H_OUT)):
                square_indices = self.square[i][j]
                color_value = color.get(pattern[i][j], (0, 0, 0))
                for index in square_indices:
                    self.strip[index] = color_value
        self.strip.show()

    def reset_board(self):
        try:
            self.board = chess.Board()
            md = input('Enter custom FEN- ')
            if md: 
                self.board = chess.Board(md)
            else:
                self.board.reset()
            
            self.prev = self.parse_grid(self.board)
            print(self.prev)
            while self.read_hall() != self.prev:
                print('Awaiting board reset...')
                print(self.read_hall())
                self.update_leds([['G' if val==0 else 'Y' for val in row] for row in self.grid])
                time.sleep(1)
            
            print("\n\n==============================================\n")
            print("Board reset detected. Starting new game...")
            
            disp = DisplayGrid()
            disp.set_animation1()
        except KeyboardInterrupt:
            self.strip.fill((0, 0, 0))
            self.strip.show()
            GPIO.cleanup()
            time.sleep(1)
        
    def compare(self):
        for i in range(8):
            for j in range(8):
                if self.prev[i][j] != self.grid[i][j]: 
                    return i,j
                

    def move(self, i,j):
        print(self.board)
        
        self.prev = [row[:] for row in self.grid]
        
        square = chess.parse_square(f"{chr(j+97)}{8-i}")
        moves = [move for move in self.board.legal_moves if move.from_square == square]
        
                
        pattern = [[['W', 'G'][(i+j)%2] for j in range(8)] for i in range(8)]
        
        if not moves:
            while self.read_hall() != (temp:=self.parse_grid(self.board)):
                pattern = [[['W', 'G'][(i+j)%2] for j in range(8)] for i in range(8)]
                for a in range(8):
                    for b in range(8):
                        if temp[a][b] != self.grid[a][b]: 
                            pattern[a][b] = 'R'
                self.update_leds(pattern)
                print("Piece can't be moved, place it back.")
                time.sleep(0.01)
            return
                
        for move in moves:
            # if move is capture, set color to Y else B
            to_square = move.to_square
            ti, tj = 7 - (to_square // 8), to_square % 8
            if self.board.is_capture(move):
                pattern[ti][tj] = 'Y'
            else:
                pattern[ti][tj] = 'B'

        self.update_leds(pattern)
        move_made = False
        print(self.board)
        print(i,j,moves)
        while not move_made:
            print("Awaiting piece placement...")
            self.read_hall()
            if self.grid[i][j] == 1:
                for move in moves:
                    to_square = move.to_square
                    ti, tj = 7 - (to_square // 8), to_square % 8
                    
                    if self.grid[ti][tj] == 0 and self.board.is_en_passant(move):
                        
                        ci, cj = ti - (-1 if self.board.turn == chess.WHITE else 1), tj 
                        pattern[ti][tj] = 'B'
                        pattern[ci][cj] = 'R'
                        self.update_leds(pattern)
                        while self.read_hall()[ci][cj] != 1:
                            print("Capture detected, awaiting piece removal...")
                            time.sleep(0.005)
                            self.board.push(move)
                            move_made = True
                            break
                        
                    if self.grid[ti][tj] == 0 and not self.board.is_capture(move):
                        self.board.push(move)
                        # print(f"Move made: {self.board.san(move)}")
                        move_made = True
                        break
                    
                    # if self.grid[ti][tj] == 0 and self.board.is_en_passant(move):
                        
                    if self.grid[ti][tj] == 1 and self.board.is_capture(move) and not self.board.is_en_passant(move):
                        
                        
                        while self.read_hall()[ti][tj] != 1:
                            print("Capture detected, awaiting piece placement...")
                            time.sleep(0.005)
                        if self.grid[i][j] == 0:
                            move_made = True
                            break
                        self.board.push(move)
                        # print(f"Capture made: {self.board.san(move)}")
                        move_made = True
                        break
            time.sleep(0.005)

        self.prev = [row[:] for row in self.grid]
        self.update_leds([[['W', 'G'][(i+j)%2] for j in range(8)] for i in range(8)])
        print(f'Move completed:\n {self.board}')
        
    def best_move(self, limit):
        result = self.engine.play(self.board, engine.Limit(time=0.01))
        sq1, sq2 = result.move.from_square, result.move.to_square
        return 7 - (sq1 // 8), sq1 % 8, 7 - (sq2 // 8), sq2 % 8, result
        
        
    def game(self):
        suggestion = []
        first = True
        try:
            while True:
                self.read_hall()
                if first:
                    first = False
                    pattern = [[['W', 'G'][(i+j)%2] for j in range(8)] for i in range(8)]
                # print(self.grid)
                
                #validate
                if any(self.grid[i][j]==0!=self.parse_grid(self.board)[i][j] for i in range(8) for j in range(8)):
                    while self.grid != (temp:=self.parse_grid(self.board)):
                        print("Invalid board state detected, please correct the board.")
                        print(self.grid)
                        print(temp)
                        pattern = [[['W', 'G'][(i+j)%2] for j in range(8)] for i in range(8)]
                        for a in range(8):
                            for b in range(8):
                                if temp[a][b] != self.grid[a][b]: 
                                    pattern[a][b] = 'R'
                        self.update_leds(pattern)
                        self.read_hall()
                        time.sleep(0.01)
                
                if self.board.is_checkmate():
                    print("Checkmate detected!")
                    if self.board.turn == chess.WHITE:
                        self.update_leds([['G' for _ in range(8)] for _ in range(8)])
                        print("Black wins!")
                    else:
                        self.update_leds([['W' for _ in range(8)] for _ in range(8)])
                        print("White wins!")
                    disp = DisplayGrid()
                    # disp.win_animation(1 if self.board.turn == chess.WHITE else 0)
                    disp.win_drawing(1 if self.board.turn == chess.WHITE else 0)
                    break
                if self.board.is_stalemate() or self.board.is_insufficient_material() or self.board.can_claim_fifty_moves() or self.board.is_fivefold_repetition():
                    print("Draw detected!")
                    self.update_leds([['Y' for _ in range(8)] for _ in range(8)])
                    break   
                
                if self.grid != self.prev:
                    suggestion.clear()
                    i,j = self.compare()
                    print(f"Change detected at: {i},{j}")
                    self.move(i,j)
                    pattern = [[['W', 'G'][(i+j)%2] for j in range(8)] for i in range(8)]
                    
                    if self.board.is_game_over(): continue
                    if self.game_mode == 1: continue
                    if self.game_mode == 4 and self.board.turn == chess.WHITE: continue
                    if self.game_mode == 3 and self.board.turn == chess.BLACK: continue
                    
                    si, sj, di, dj, _ = self.best_move(limit=0.1)
                    pattern[si][sj], pattern[di][dj] = 'P', 'P'
                    
                    
                    
                time.sleep(0.03)
                self.update_leds(pattern)
        except KeyboardInterrupt:
            self.strip.fill((0, 0, 0))
            self.strip.show()
            GPIO.cleanup()
            time.sleep(1)
            
        print("Game ended.")


class PuzzleBoard():
    def __init__(self, chessgame=2):
        self.H_OUT = [10, 9, 11, 5, 6, 13, 19, 26]
        self.H_IN = [25, 8, 7, 1, 12, 16, 20, 21]
        #self.H_OUT = [19, 21, 23, 29, 31, 33, 35, 37]
        #self.H_IN = [22, 24, 26, 28, 32, 36, 38, 40]
        self.initialize_hall()
        bright = float(input('Enter brightness- '))
        self.strip = neopixel.NeoPixel(LED, 4*len(self.H_OUT)*len(self.H_IN), brightness=bright, auto_write=False, pixel_order=ORDER)
        self.strip.fill((0, 0, 0))
        self.strip.show()
        self.grid = [[0 for _ in range(len(self.H_OUT))] for _ in range(len(self.H_IN))]
        self.prev = [[self.grid[i][j] for j in range(len(self.H_OUT))] for i in range(len(self.H_IN))]

        self.square = [
            [[223, 224, 253, 254], [225, 226, 251, 252], [227, 228, 249, 250], [229, 230, 247, 248], [231, 232, 245, 246], [233, 234, 243, 244], [235, 236, 241, 242], [237, 238, 239, 240]],
            [[191, 192, 221, 222], [193, 194, 219, 220], [195, 196, 217, 218], [197, 198, 215, 216], [199, 200, 213, 214], [201, 202, 211, 212], [203, 204, 209, 210], [205, 206, 207, 208]],
            [[159, 160, 189, 190], [161, 162, 187, 188], [163, 164, 185, 186], [165, 166, 183, 184], [167, 168, 181, 182], [169, 170, 179, 180], [171, 172, 177, 178], [173, 174, 175, 176]],
            [[127, 128, 157, 158], [129, 130, 155, 156], [131, 132, 153, 154], [133, 134, 151, 152], [135, 136, 149, 150], [137, 138, 147, 148], [139, 140, 145, 146], [141, 142, 143, 144]],
            [[95, 96, 125, 126], [97, 98, 123, 124], [99, 100, 121, 122], [101, 102, 119, 120], [103, 104, 117, 118], [105, 106, 115, 116], [107, 108, 113, 114], [109, 110, 111, 112]],
            [[64, 65, 93, 94], [66, 67, 91, 92], [68, 69, 89, 90], [70, 71, 87, 88], [72, 73, 85, 86], [74, 75, 83, 84], [76, 77, 81, 82], [78, 79, 80, 80]],
            [[32, 33, 62, 63], [34, 35, 60, 61], [36, 37, 58, 59], [38, 39, 56, 57], [40, 41, 54, 55], [42, 43, 52, 53], [44, 45, 50, 51], [46, 47, 48, 49]],
            [[0, 1, 30, 31], [2, 3, 28, 29], [4, 5, 26, 27], [6, 7, 24, 25], [8, 9, 22, 23], [10, 11, 20, 21], [12, 13, 18, 19], [14, 15, 16, 17]]
        ]
        
        # self.suggestion_W = 1 if self.game_mode in [2,3] else 0
        # self.suggestion_B = 1 if self.game_mode in [2,4] else 0
        
        self.parse_board = lambda board:[row.split() for row in str(board).split('\n')]
        self.parse_grid = lambda board: [[(1 if cell == '.' else 0) for cell in row] for row in self.parse_board(board)]
        
        if chessgame==1:
            self.engine = engine.SimpleEngine.popen_uci("/usr/games/stockfish")
            self.engine.configure({"Threads": 2, "Hash": 512})
        
            
            self.reset_board()
                
            
        if chessgame == 2:
            self.engine = engine.SimpleEngine.popen_uci("/usr/games/stockfish")
            self.engine.configure({"Threads": 2, "Hash": 512})
            self.board, self.solution = getPuzzle()
            print(self.board)
            
    
    def initialize_hall(self):
        for pin in self.H_OUT:
            GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        for pin in self.H_IN:
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, GPIO.LOW)

    def read_hall(self):
        for i in range(len(self.H_IN)):
            GPIO.output(self.H_IN[i], GPIO.HIGH)
            time.sleep(0.001)
            for j in range(len(self.H_OUT)):
                self.grid[i][j] = GPIO.input(self.H_OUT[j])
            GPIO.output(self.H_IN[i], GPIO.LOW)
        self.grid[6][4] = 0  # TEMP FIX
        return self.grid

    def update_leds(self, pattern):
        for i in range(len(self.H_IN)):
            for j in range(len(self.H_OUT)):
                square_indices = self.square[i][j]
                color_value = color.get(pattern[i][j], (0, 0, 0))
                for index in square_indices:
                    self.strip[index] = color_value
        self.strip.show()    
    
    def reset_board(self):
        try:
            
            if self.board.turn == "WHITE":
                self.suggestion_W = 0
                self.suggestion_B = 1
            else:
                self.suggestion_W = 1
                self.suggestion_B = 0

            self.prev = self.parse_grid(self.board)
            print(self.prev)
            while self.read_hall() != self.prev:
                print('Awaiting board reset...')
                print(self.read_hall())
                self.update_leds([['G' if val==0 else 'Y' for val in row] for row in self.grid])
                time.sleep(1)
            
            print("\n\n==============================================\n")
            print("Board reset detected. Starting new game...")
            
            disp = DisplayGrid()
            disp.set_animation1()
        except KeyboardInterrupt:
            self.strip.fill((0, 0, 0))
            self.strip.show()
            GPIO.cleanup()
            time.sleep(1)
    
    def compare(self):
        for i in range(8):
            for j in range(8):
                if self.prev[i][j] != self.grid[i][j]: 
                    return i,j
    
    def validatePuzzle(self, move):
        if move == self.solution[::-1]:
            self.solution.pop()
            return True
        return False
            
    def move(self, i,j):
        print(self.board)
        
        self.prev = [row[:] for row in self.grid]
        
        square = chess.parse_square(f"{chr(j+97)}{8-i}")
        moves = [move for move in self.board.legal_moves if move.from_square == square]
        
                
        pattern = [[['W', 'G'][(i+j)%2] for j in range(8)] for i in range(8)]
        
        if not moves:
            while self.read_hall() != (temp:=self.parse_grid(self.board)):
                pattern = [[['W', 'G'][(i+j)%2] for j in range(8)] for i in range(8)]
                for a in range(8):
                    for b in range(8):
                        if temp[a][b] != self.grid[a][b]: 
                            pattern[a][b] = 'R'
                self.update_leds(pattern)
                print("Piece can't be moved, place it back.")
                time.sleep(0.01)
            return
                
        for move in moves:
            # if move is capture, set color to Y else B
            to_square = move.to_square
            ti, tj = 7 - (to_square // 8), to_square % 8
            if self.board.is_capture(move):
                pattern[ti][tj] = 'Y'
            else:
                pattern[ti][tj] = 'B'

        self.update_leds(pattern)
        move_made = False
        print(self.board)
        print(i,j,moves)
        while not move_made:
            print("Awaiting piece placement...")
            self.read_hall()
            if self.grid[i][j] == 1:
                for move in moves:
                    to_square = move.to_square
                    ti, tj = 7 - (to_square // 8), to_square % 8
                    
                    if self.grid[ti][tj] == 0 and self.board.is_en_passant(move):
                        
                        ci, cj = ti - (-1 if self.board.turn == chess.WHITE else 1), tj 
                        pattern[ti][tj] = 'B'
                        pattern[ci][cj] = 'R'
                        self.update_leds(pattern)
                        while self.read_hall()[ci][cj] != 1:
                            print("Capture detected, awaiting piece removal...")
                            time.sleep(0.005)
                            if not self.validatePuzzle(move):
                                break
                            self.board.push(move)
                            move_made = True
                            break
                        
                    if self.grid[ti][tj] == 0 and not self.board.is_capture(move):
                        if not self.validatePuzzle(move):
                            break
                        self.board.push(move)
                        # print(f"Move made: {self.board.san(move)}")
                        move_made = True
                        break
                    
                    # if self.grid[ti][tj] == 0 and self.board.is_en_passant(move):
                        
                    if self.grid[ti][tj] == 1 and self.board.is_capture(move) and not self.board.is_en_passant(move):
                        
                        
                        while self.read_hall()[ti][tj] != 1:
                            print("Capture detected, awaiting piece placement...")
                            time.sleep(0.005)
                        if self.grid[i][j] == 0:
                            if not self.validatePuzzle(move):
                                break
                            move_made = True
                            break
                        if not self.validatePuzzle(move):
                            break
                        self.board.push(move)
                        # print(f"Capture made: {self.board.san(move)}")
                        move_made = True
                        break
            time.sleep(0.005)

        self.prev = [row[:] for row in self.grid]
        self.update_leds([[['W', 'G'][(i+j)%2] for j in range(8)] for i in range(8)])
        print(f'Move completed:\n {self.board}')
        
    def best_move(self, limit):
        result = self.engine.play(self.board, engine.Limit(time=0.01))
        sq1, sq2 = result.move.from_square, result.move.to_square
        return 7 - (sq1 // 8), sq1 % 8, 7 - (sq2 // 8), sq2 % 8, result
        
    def game(self):
        suggestion = []
        first = True
        try:
            while True:
                self.read_hall()
                if first:
                    first = False
                    pattern = [[['W', 'G'][(i+j)%2] for j in range(8)] for i in range(8)]
                # print(self.grid)
                
                #validate
                if any(self.grid[i][j]==0!=self.parse_grid(self.board)[i][j] for i in range(8) for j in range(8)):
                    while self.grid != (temp:=self.parse_grid(self.board)):
                        print("Invalid board state detected, please correct the board.")
                        print(self.grid)
                        print(temp)
                        pattern = [[['W', 'G'][(i+j)%2] for j in range(8)] for i in range(8)]
                        for a in range(8):
                            for b in range(8):
                                if temp[a][b] != self.grid[a][b]: 
                                    pattern[a][b] = 'R'
                        self.update_leds(pattern)
                        self.read_hall()
                        time.sleep(0.01)
                
                # if self.board.is_checkmate():
                #     print("Checkmate detected!")
                #     if self.board.turn == chess.WHITE:
                #         self.update_leds([['G' for _ in range(8)] for _ in range(8)])
                #         print("Black wins!")
                #     else:
                #         self.update_leds([['W' for _ in range(8)] for _ in range(8)])
                #         print("White wins!")
                #     disp = DisplayGrid()
                #     # disp.win_animation(1 if self.board.turn == chess.WHITE else 0)
                #     disp.win_drawing(1 if self.board.turn == chess.WHITE else 0)
                #     break
                # if self.board.is_stalemate() or self.board.is_insufficient_material() or self.board.can_claim_fifty_moves() or self.board.is_fivefold_repetition():
                #     print("Draw detected!")
                #     self.update_leds([['Y' for _ in range(8)] for _ in range(8)])
                #     break
                
                if self.solution == []:
                    if self.board.turn == chess.BLACK:
                        self.update_leds([['G' for _ in range(8)] for _ in range(8)])
                        print("Puzzle solved!")
                    else:
                        self.update_leds([['W' for _ in range(8)] for _ in range(8)])
                        print("Puzzle solved!")
                    disp = DisplayGrid()
                    # disp.win_animation(1 if self.board.turn == chess.WHITE else 0)
                    disp.win_drawing(1 if self.board.turn == chess.BLACK else 0)
                    break

                
                if self.grid != self.prev:
                    suggestion.clear()
                    i,j = self.compare()
                    print(f"Change detected at: {i},{j}")
                    self.move(i,j)
                    pattern = [[['W', 'G'][(i+j)%2] for j in range(8)] for i in range(8)]
                    
                    if self.board.is_game_over(): continue
                    if self.game_mode == 1: continue
                    if self.game_mode == 4 and self.board.turn == chess.WHITE: continue
                    if self.game_mode == 3 and self.board.turn == chess.BLACK: continue
                    
                    si, sj, di, dj, _ = self.best_move(limit=0.1)
                    pattern[si][sj], pattern[di][dj] = 'P', 'P'
                    
                    
                    
                time.sleep(0.03)
                self.update_leds(pattern)
        except KeyboardInterrupt:
            self.strip.fill((0, 0, 0))
            self.strip.show()
            GPIO.cleanup()
            time.sleep(1)
            
        print("Game ended.")    

class DisplayGrid():
    # Provide function to display grid on LEDs
    def __init__(self):
        self.strip = neopixel.NeoPixel(LED, 4*8*8, brightness=0.8, auto_write=False, pixel_order=ORDER)
        self.led_indexes = [
            [254, 253, 252, 251, 250, 249, 248, 247, 246, 245, 244, 243, 242, 241, 240, 239],
            [223, 224, 225, 226, 227, 228, 229, 230, 231, 232, 233, 234, 235, 236, 237, 238],
            [222, 221, 220, 219, 218, 217, 216, 215, 214, 213, 212, 211, 210, 209, 208, 207],
            [191, 192, 193, 194, 195, 196, 197, 198, 199, 200, 201, 202, 203, 204, 205, 206],
            [190, 189, 188, 187, 186, 185, 184, 183, 182, 181, 180, 179, 178, 177, 176, 175],
            [159, 160, 161, 162, 163, 164, 165, 166, 167, 168, 169, 170, 171, 172, 173, 174],
            [158, 157, 156, 155, 154, 153, 152, 151, 150, 149, 148, 147, 146, 145, 144, 143],
            [127, 128, 129, 130, 131, 132, 133, 134, 135, 136, 137, 138, 139, 140, 141, 142],
            [126, 125, 124, 123, 122, 121, 120, 119, 118, 117, 116, 115, 114, 113, 112, 111],
            [95, 96, 97, 98, 99, 100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110],
            [94, 93, 92, 91, 90, 89, 88, 87, 86, 85, 84, 83, 82, 81, 80, 80],
            [64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79],
            [63, 62, 61, 60, 59, 58, 57, 56, 55, 54, 53, 52, 51, 50, 49, 48],
            [32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47],
            [31, 30, 29, 28, 27, 26, 25, 24, 23, 22, 21, 20, 19, 18, 17, 16],
            [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]
        ]
        
        self.rick_roll = [
        [(62, 64, 78), (57, 60, 72), (65, 67, 79), (67, 67, 79), (56, 55, 65), (55, 55, 63), (55, 56, 66), (61, 55, 58), (62, 45, 37), (61, 54, 57), (59, 59, 67), (51, 50, 57), (54, 53, 61), (64, 64, 73), (64, 64, 74), (61, 61, 71)],
        [(166, 174, 214), (179, 189, 226), (180, 186, 221), (179, 181, 215), (174, 173, 201), (159, 160, 187), (172, 166, 184), (156, 111, 87), (116, 65, 34), (132, 93, 79), (161, 154, 170), (151, 149, 173), (153, 151, 175), (169, 168, 196), (193, 192, 223), (179, 178, 209)],    
        [(158, 167, 205), (165, 172, 208), (168, 172, 207), (173, 175, 205), (165, 164, 191), (165, 169, 196), (178, 159, 159), (138, 86, 59), (146, 106, 96), (138, 97, 85), (151, 141, 150), (150, 150, 174), (149, 148, 171), (148, 149, 174), (160, 161, 188), (176, 175, 203)],    
        [(162, 172, 208), (164, 172, 206), (171, 176, 208), (180, 182, 211), (168, 166, 193), (168, 171, 196), (179, 153, 160), (144, 94, 79), (153, 109, 102), (159, 117, 116), (167, 161, 175), (151, 150, 174), (148, 147, 171), (156, 158, 182), (151, 152, 177), (155, 156, 181)], 
        [(160, 169, 203), (162, 170, 203), (176, 180, 210), (194, 192, 222), (176, 173, 199), (155, 155, 179), (167, 144, 159), (155, 102, 92), (153, 104, 95), (169, 128, 131), (159, 151, 170), (143, 141, 162), (158, 157, 178), (170, 170, 192), (157, 157, 180), (156, 157, 181)], 
        [(170, 178, 211), (161, 168, 199), (169, 172, 201), (180, 178, 207), (166, 162, 186), (171, 169, 191), (166, 162, 177), (149, 105, 100), (156, 104, 95), (169, 141, 147), (166, 160, 178), (152, 147, 164), (147, 144, 164), (170, 167, 189), (167, 166, 188), (156, 158, 181)],
        [(165, 173, 201), (155, 160, 187), (148, 151, 175), (172, 169, 191), (169, 159, 176), (142, 128, 136), (142, 123, 120), (146, 107, 101), (156, 104, 97), (143, 119, 126), (149, 139, 151), (163, 153, 168), (152, 148, 166), (155, 151, 170), (155, 154, 174), (153, 156, 176)],
        [(152, 157, 181), (166, 171, 191), (160, 162, 181), (143, 134, 145), (90, 74, 64), (58, 42, 27), (99, 84, 72), (128, 105, 100), (161, 129, 132), (93, 82, 84), (58, 46, 42), (93, 82, 82), (143, 136, 146), (154, 150, 168), (154, 153, 172), (158, 160, 180)],
        [(151, 156, 177), (163, 166, 184), (172, 171, 189), (105, 92, 94), (48, 38, 20), (53, 46, 32), (66, 58, 45), (122, 107, 103), (121, 109, 110), (62, 56, 54), (51, 46, 41), (56, 45, 38), (81, 71, 71), (152, 147, 161), (160, 157, 177), (171, 172, 193)],
        [(151, 158, 173), (151, 153, 168), (156, 150, 164), (76, 62, 54), (52, 44, 26), (48, 43, 27), (56, 52, 39), (122, 110, 104), (85, 75, 70), (50, 44, 36), (45, 41, 32), (116, 86, 80), (132, 101, 100), (148, 142, 155), (153, 147, 164), (163, 160, 182)],
        [(159, 166, 181), (159, 161, 175), (156, 145, 157), (59, 47, 35), (45, 40, 22), (45, 40, 23), (54, 49, 34), (100, 89, 79), (75, 67, 62), (49, 44, 36), (38, 35, 23), (109, 77, 66), (131, 98, 96), (157, 152, 164), (159, 153, 169), (169, 165, 186)],
        [(160, 169, 183), (158, 157, 171), (98, 82, 82), (56, 45, 31), (47, 41, 25), (95, 68, 57), (129, 90, 80), (95, 83, 70), (63, 59, 47), (45, 42, 32), (39, 36, 21), (74, 54, 38), (86, 65, 57), (146, 141, 152), (157, 151, 169), (172, 169, 190)],
        [(154, 162, 176), (154, 152, 166), (72, 57, 49), (55, 42, 27), (57, 45, 31), (100, 71, 58), (101, 67, 54), (80, 70, 55), (55, 51, 38), (40, 38, 24), (41, 37, 19), (37, 31, 11), (40, 34, 17), (84, 78, 80), (154, 147, 163), (163, 160, 179)],
        [(158, 166, 180), (163, 165, 179), (124, 113, 117), (79, 65, 59), (69, 56, 45), (42, 36, 16), (38, 35, 12), (79, 71, 57), (49, 46, 31), (36, 35, 17), (39, 36, 16), (36, 31, 11), (28, 24, 4), (63, 59, 56), (145, 140, 154), (154, 153, 167)],
        [(150, 158, 173), (159, 161, 177), (174, 169, 188), (177, 165, 175), (104, 92, 86), (41, 34, 10), (49, 45, 23), (71, 65, 49), (48, 46, 31), (41, 40, 25), (41, 40, 24), (45, 40, 23), (59, 53, 38), (132, 126, 132), (166, 163, 176), (155, 155, 168)],
        [(47, 50, 54), (52, 52, 57), (54, 52, 58), (56, 53, 58), (34, 30, 28), (14, 12, 4), (17, 15, 8), (19, 17, 12), (15, 14, 11), (14, 14, 10), (13, 13, 9), (19, 18, 14), (51, 48, 48), (58, 56, 60), (53, 52, 56), (53, 52, 57)],
        ]
                            

    def display(self, grid):
        for i in range(16):
            for j in range(16):
                index = self.led_indexes[i][j]
                value = grid[i][j]
                if not isinstance(value, tuple):
                    value = color.get(value, (self.w(), self.w(), self.w()))
                self.strip[index] = value
        self.strip.show()
    
    def w(self):
        n=255
        bias=2
        """Return integer in [0, n-1], biased toward both ends."""
        r = random.random() ** bias
        if random.random() < 0.5:
            val = r  # near 0
        else:
            val = 1 - r  # near 1
        return int(val * n)
    
    def animation(self, frames, duration):
        for frame in frames:
            self.display(frame)
            time.sleep(duration/len(frames))

    def clear(self):
        for i in range(16):
            for j in range(16):
                index = self.led_indexes[i][j]
                self.strip[index] = (0, 0, 0)
        self.strip.show()

    def set_animation1(self):
        # 1 sec animation of a big circle expanding and contracting
        frames = []
        for r in range(1, 9):
            frame = [[(0, 255, 0) for _ in range(16)] for _ in range(16)]
            for i in range(16):
                for j in range(16):
                    if (i - 7.5) ** 2 + (j - 7.5) ** 2 <= r ** 2:
                        frame[i][j] = (255, 0, 100)
            frames.append(frame)
        for r in range(8, 0, -1):
            frame = [[(0, 0, 0) for _ in range(16)] for _ in range(16)]
            for i in range(16):
                for j in range(16):
                    if (i - 7.5) ** 2 + (j - 7.5) ** 2 <= r ** 2:
                        frame[i][j] = (255, 0, 100)
            frames.append(frame)

        self.animation(frames, 1)
        
    def set_animation2(self):
        # 1 sec animation of a diagonal line
        frames = []
        for i in range(16):
            frame = [[(0, 255, 0) for _ in range(16)] for _ in range(16)]
            for j in range(16):
                if i == j:
                    frame[i][j] = (255, 0, 100)
            frames.append(frame)
        self.animation(frames, 1)
        
    def win_animation(self, side=1):
        # side: 1 for white win, 0 for black win
        frames = []
        color_win = (255, 255, 255) if side == 1 else (0, 0, 255)
        for i in range(16):
            frame = [[(0, 0, 0) for _ in range(16)] for _ in range(16)]
            for j in range(16):
                frame[i][j] = color_win
            frames.append(frame)
        self.animation(frames, 2)
    
    def win_drawing(self, side=0):
        color_win = 'W' if side == 0 else 'G'
        win_grid = [    
            ['2', '2', '2', '2', '2', '2', '2', '2', '2', '2', '2', '2', '2', '2', '2', '2'],
            ['2', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', '2'],
            ['2', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', '2'],
            ['2', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', '2'],
            ['2', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', '2'],
            ['2', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', '2'],
            ['2', ' ', '1', ' ', ' ', ' ', '1', ' ', '1', ' ', '1', ' ', ' ', '1', ' ', '2'],
            ['2', ' ', '1', ' ', ' ', ' ', '1', ' ', '1', ' ', '1', '1', ' ', '1', ' ', '2'],
            ['2', ' ', '1', ' ', '1', ' ', '1', ' ', '1', ' ', '1', ' ', '1', '1', ' ', '2'],
            ['2', ' ', ' ', '1', ' ', '1', ' ', ' ', '1', ' ', '1', ' ', ' ', '1', ' ', '2'],
            ['2', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', '2'],
            ['2', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', '2'],
            ['2', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', '2'],
            ['2', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', '2'],
            ['2', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', '2'],
            ['2', '2', '2', '2', '2', '2', '2', '2', '2', '2', '2', '2', '2', '2', '2', '2']
        ]
        if side==1: win_grid = [row[::-1] for row in win_grid[::-1]]
        for i in range(80):
            self.display([[color_win if cell == '1' else 'Z' if cell == '2' else ' ' for cell in row] for row in win_grid])
            time.sleep(0.05)
        
    def display_rick_roll(self):
        self.display(self.rick_roll)
        
class PongGame:
    """Simplified Pong for 16x16 DisplayGrid.

    - Minimal error handling
    - No cumulative score display; only track the last winner
    - Basic paddle input from hall sensors if a `chessboard` with `H_IN`/`H_OUT`
      is provided, otherwise human paddle stays centered.
    """

    def __init__(self, disp=None, chessboard=None, paddle_height=4, fps=25, ball_speed=0.35):
        self.disp = DisplayGrid() if disp is None else disp
        self.chessboard = chessboard
        self.paddle_height = paddle_height
        self.fps = fps
        self.frame_dt = 1.0 / fps
        self.ball_speed = ball_speed

        self.width = 16
        self.height = 16

        self.left_y = float(self.height // 2)
        self.right_y = float(self.height // 2)

        self.ball_x = self.width / 2.0
        self.ball_y = self.height / 2.0
        angle = random.uniform(-0.5, 0.5)
        self.ball_vx = self.ball_speed * (1.0 if random.choice([True, False]) else -1.0)
        self.ball_vy = self.ball_speed * angle

        # only keep last winner (either 'left' or 'right')
        self.last_winner = None

        # colors
        self.COL_BALL = (255, 255, 255)
        self.COL_PADDLE = (0, 255, 0)
        self.COL_PADDLE_HIT = (255, 200, 0)
        self.COL_BG = (0, 0, 0)

    def reset_ball(self, direction=None):
        self.ball_x = self.width / 2.0
        self.ball_y = self.height / 2.0
        if direction is None:
            direction = 1 if random.choice([True, False]) else -1
        angle = random.uniform(-0.6, 0.6)
        self.ball_vx = direction * self.ball_speed
        self.ball_vy = self.ball_speed * angle

    def get_human_paddle_y(self):
        H_IN = getattr(self.chessboard, "H_IN", None)
        H_OUT = getattr(self.chessboard, "H_OUT", None)
        if H_IN is None or H_OUT is None:
            return int(round(self.left_y))

        # pulse H_IN lines, sample H_OUT, then clear
        for pin in H_IN:
            GPIO.output(pin, GPIO.HIGH)
        time.sleep(0.001)
        readings = [GPIO.input(pin) for pin in H_OUT]
        for pin in H_IN:
            GPIO.output(pin, GPIO.LOW)

        active = [i for i, v in enumerate(readings) if v == 0]
        if not active:
            return int(round(self.left_y))
        centroid = sum(active) / len(active)
        pos = int(round(centroid))
        return max(0, min(self.height - 1, pos))

    def ai_update(self):
        target = self.ball_y
        delta = target - self.right_y
        self.right_y += delta * 0.2
        self.right_y = max(0, min(self.height - 1, self.right_y))

    def update_ball(self):
        self.ball_x += self.ball_vx
        self.ball_y += self.ball_vy

        # bounce
        if self.ball_y < 0:
            self.ball_y = -self.ball_y
            self.ball_vy = -self.ball_vy
        elif self.ball_y > self.height - 1:
            self.ball_y = 2 * (self.height - 1) - self.ball_y
            self.ball_vy = -self.ball_vy

        # left paddle
        if self.ball_x <= 1.0:
            paddle_top = self.get_paddle_top(self.left_y)
            paddle_bottom = paddle_top + self.paddle_height - 1
            if paddle_top - 0.5 <= self.ball_y <= paddle_bottom + 0.5:
                self.ball_x = 1.0
                self.ball_vx = abs(self.ball_vx)
                rel = (self.ball_y - self.left_y) / max(1.0, (self.paddle_height / 2))
                self.ball_vy += rel * 0.4
            else:
                self.last_winner = 'right'
                self.reset_ball(direction=-1)
                return

        # right paddle
        if self.ball_x >= self.width - 2:
            paddle_top = self.get_paddle_top(self.right_y)
            paddle_bottom = paddle_top + self.paddle_height - 1
            if paddle_top - 0.5 <= self.ball_y <= paddle_bottom + 0.5:
                self.ball_x = self.width - 2
                self.ball_vx = -abs(self.ball_vx)
                rel = (self.ball_y - self.right_y) / max(1.0, (self.paddle_height / 2))
                self.ball_vy += rel * 0.4
            else:
                self.last_winner = 'left'
                self.reset_ball(direction=1)
                return

        # clamp velocities
        max_v = 1.5
        self.ball_vx = max(-max_v, min(max_v, self.ball_vx))
        self.ball_vy = max(-max_v, min(max_v, self.ball_vy))

    def get_paddle_top(self, center_y):
        half = self.paddle_height / 2.0
        top = int(round(center_y - half + 0.0))
        return max(0, min(self.height - self.paddle_height, top))

    def build_frame(self, highlight_paddle_hit=False):
        frame = [[self.COL_BG for _ in range(self.width)] for _ in range(self.height)]
        top = self.get_paddle_top(self.left_y)
        for r in range(self.paddle_height):
            y = top + r
            frame[y][1] = self.COL_PADDLE_HIT if highlight_paddle_hit else self.COL_PADDLE
        top_r = self.get_paddle_top(self.right_y)
        for r in range(self.paddle_height):
            y = top_r + r
            frame[y][self.width - 2] = self.COL_PADDLE
        bx = int(round(self.ball_x))
        by = int(round(self.ball_y))
        if 0 <= by < self.height and 0 <= bx < self.width:
            frame[by][bx] = self.COL_BALL
        # do not draw cumulative scores
        return frame

    def draw(self, frame):
        if self.disp is None:
            ball = (int(round(self.ball_x)), int(round(self.ball_y)))
            print(f"Ball:{ball}")
            return
        self.disp.display(frame)

    def start(self):
        print("Starting Pong. Press Ctrl-C to stop.")
        try:
            while True:
                t0 = time.time()
                py = self.get_human_paddle_y()
                self.left_y += (py - self.left_y) * 0.5
                self.ai_update()
                self.update_ball()
                frame = self.build_frame()
                self.draw(frame)
                elapsed = time.time() - t0
                time.sleep(max(0, self.frame_dt - elapsed))
        except KeyboardInterrupt:
            try:
                if self.disp is not None:
                    if self.last_winner == 'left':
                        self.disp.win_drawing(side=0)
                    elif self.last_winner == 'right':
                        self.disp.win_drawing(side=1)
                    else:
                        self.disp.clear()
            except Exception:
                pass
            try:
                GPIO.cleanup()
            except Exception:
                pass
            print(f"Pong stopped. Last winner: {self.last_winner}")
            return
    
class MusicVisualizer():
    def __init__(self):
        self.disp = DisplayGrid()
        
    def playMusic(self, file):
        ...
        
if __name__ == "__main__":
    print('1. Chess\n2. Pong\n3. Puzzle')
    inp = input('Select game: ')
    if inp == '1':
        chessboard = ChessBoard(chessgame=1)
        chessboard.game()
    elif inp == '3':
        chessboard = PuzzleBoard(chessgame=2)
        chessboard.game()
    else:
        print("Starting Pong game on 16x16 LED grid...")
        ponggame = PongGame(disp=DisplayGrid(), chessboard=None)
        ponggame.start()
    # disp = DisplayGrid()
    # print("Displaying Rick Roll...")
    # disp = DisplayGrid()
    # disp.display_rick_roll()
    # while True:
        # print("Displaying animation...")
    #     disp.set_animation1()
    #     time.sleep(1)