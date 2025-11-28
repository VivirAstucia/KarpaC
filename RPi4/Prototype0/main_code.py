import time
import board
import busio
import sensor_matrix
import led_matrix
import chess
from stockfish import Stockfish

STOCKFISH_PATH = r".\engine\stockfish.exe"
LED_COUNT = 64
LED_PIN = board.D18  # GPIO 18 (PWM-capable pin)
LED_BRIGHTNESS = 0.3 

BLACK = (0, 0, 0)
WHITE = (150, 150, 150)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
CYAN = (0, 255, 255)
MAGENTA = (255, 0, 255)
ORANGE = (255, 165, 0)

class SmartChessGame:
    def __init__(self):
        print("Initializing Smart Chessboard...")

        self.i2c = busio.I2C(board.SCL, board.SDA)
        self.sensors = sensor_matrix.SensorMatrix(self.i2c)
        self.leds = led_matrix.LedMatrix(LED_PIN, LED_COUNT, LED_BRIGHTNESS)
        self.stocky = Stockfish(path=STOCKFISH_PATH)

        self.board = chess.Board() 
            
        self.previous_board_state = self.sensors.read_board_state()
        self.current_board_state = self.previous_board_state.copy()
        
        self.picked_up_square_index = None 
        self.best_move_hint = None 

        print("Initialization complete. Starting game loop.")
        self.leds.fill(WHITE) 
        self.leds.show()
        time.sleep(1)
        self.leds.clear()
        self.leds.show()

    def run_game_loop(self):
        """The main polling loop that detects moves."""
        try:
            while not self.board.is_game_over():
                self.current_board_state = self.sensors.read_board_state()
                
                if self.current_board_state != self.previous_board_state:
                    print("State change detected!")
                    self.handle_board_change()
                
                self.previous_board_state = self.current_board_state.copy()
                
                time.sleep(0.1)

            print("Game Over.")
            print(f"Result: {self.board.result()}")
            self.leds.play_game_over_animation()

        except KeyboardInterrupt:
            print("\nGame interrupted by user.")
        finally:
            self.shutdown()

    def handle_board_change(self):
        """This is the core logic for detecting a move."""
        
        diff_indices = [i for i in range(64) if self.current_board_state[i] != self.previous_board_state[i]]
        
        if len(diff_indices) == 0:
            return # Should not happen, but good to check
        
        if len(diff_indices) == 1 and self.picked_up_square_index is None:
            index = diff_indices[0]
            if not self.current_board_state[index]: # Piece was lifted
                self.picked_up_square_index = index
                self.handle_piece_pickup(index)

        elif len(diff_indices) == 1 and self.picked_up_square_index is not None:
            to_index = diff_indices[0]
            if to_index == self.picked_up_square_index:
                print("Piece returned to original square.")
                self.picked_up_square_index = None
                self.leds.clear()
                self.leds.show()
            elif self.current_board_state[to_index]: # Piece was placed
                from_index = self.picked_up_square_index
                self.picked_up_square_index = None # No longer holding a piece
                self.handle_piece_drop(from_index, to_index)

        else:
            print(f"Ignoring ambiguous state change (diff: {len(diff_indices)}).")
            # Clear any "picked up" state to reset
            if self.picked_up_square_index is not None:
                 self.picked_up_square_index = None
                 self.leds.clear()
                 self.leds.show()


    def handle_piece_pickup(self, index):
        """Called when a piece is lifted from 'index'."""
        print(f"Piece picked up from {self.leds.index_to_chess_square(index)}")
        from_square = self.leds.index_to_chess_square(index)
        
        # Check if it's the correct player's piece
        piece = self.board.piece_at(from_square)
        if piece is None or piece.color != self.board.turn:
            print("Picked up empty square or wrong color piece.")
            self.leds.clear()
            self.leds.set_square(index, ORANGE) # Show "wrong piece"
            self.leds.show()
            self.picked_up_square_index = None
            return

        legal_moves_for_piece = [
            move for move in self.board.legal_moves 
            if move.from_square == from_square
        ]
        self.leds.show_legal_moves(index, legal_moves_for_piece, self.current_board_state)
        
        

    def handle_piece_drop(self, from_index, to_index):
        """Called when a piece is moved from 'from_index' to 'to_index'."""

        # Clear all move/hint LEDs
        self.leds.clear()
        self.leds.show()

        from_square = self.leds.index_to_chess_square(from_index)
        to_square = self.leds.index_to_chess_square(to_index)

        # Create the move object. Handle promotions (default to Queen).
        move = chess.Move(from_square, to_square)
        if self.board.piece_type_at(from_square) == chess.PAWN:
            if chess.square_rank(to_square) == 7 and self.board.turn == chess.WHITE:
                move.promotion = chess.QUEEN
            elif chess.square_rank(to_square) == 0 and self.board.turn == chess.BLACK:
                move.promotion = chess.QUEEN
        
        # Check if the move is legal
        if move in self.board.legal_moves:
            print(f"Legal move: {move.uci()}")
            self.board.push(move)
            self.leds.highlight_last_move(from_index, to_index)
        else:
            print(f"ILLEGAL move attempted: {move.uci()}")
            self.leds.play_illegal_move_animation()
        time.sleep(1.0)
        self.leds.clear()
        self.leds.show()
        self.start_stockfish_analysis()
        
    def start_stockfish_analysis(self):
        """Starts a new thread to get a hint from Stockfish."""
        self.stocky.set_fen_position(self.board.fen())
        self.best_move_hint = self.stocky.get_best_move_time(1000)
        self.leds.show_best_move_hint(self.best_move_hint)


    def shutdown(self):
        """Cleans up resources on exit."""
        print("Shutting down...")
        if hasattr(self, 'leds'):
            self.leds.clear()
            self.leds.show()
            print("LEDs cleared.")

# -----------------------------------------------------------------------------
# 5. MAIN EXECUTION
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    game = None
    try:
        game = SmartChessGame()
        game.run_game_loop()
    except Exception as main_e:
        print(f"An unexpected error occurred: {main_e}")
    finally:
        if game:
            game.shutdown()
        print("Program terminated.")
