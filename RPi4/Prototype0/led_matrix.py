import neopixel
import time
import chess

BLACK = (0, 0, 0)
WHITE = (150, 150, 150)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
CYAN = (0, 255, 255)
MAGENTA = (255, 0, 255)
ORANGE = (255, 165, 0)

class LedMatrix:
    """Manages the 64 WS2812B NeoPixel LEDs."""
    
    def __init__(self, pin, count, brightness=0.5):
        try:
            self.pixels = neopixel.NeoPixel(
                pin, 
                count, 
                brightness=brightness, 
                auto_write=False, # We MUST call show() manually
                pixel_order=neopixel.RGB
            )
            self.pixels.fill(BLACK)
            self.pixels.show()
            self.count = count
            print("Successfully initialized NeoPixel LEDs.")
        except Exception as e:
            print(f"FATAL ERROR: Could not initialize NeoPixels on pin {pin}.")
            print(f"Error: {e}")
            raise

    def set_square(self, index, color):
        """Sets a single square to a color. Does not call show()."""
        if 0 <= index < self.count:
            self.pixels[index] = color

    def fill(self, color):
        """Sets all squares to a color. Does not call show()."""
        self.pixels.fill(color)

    def clear(self):
        """Turns all LEDs off. Does not call show()."""
        self.fill(BLACK)

    def show(self):
        """Pushes the current color data to the LED strip."""
        self.pixels.show()

    def highlight_last_move(self, from_index, to_index):
        """Highlights the 'from' and 'to' squares of the last move."""
        self.clear()
        self.set_square(from_index, YELLOW)
        self.set_square(to_index, YELLOW)
        self.show()
        
    def show_legal_moves(self, from_index, move_list, board_state):
        """
        Highlights all legal moves for a picked-up piece.
        - GREEN for empty square
        - RED for capture
        - BLUE for the picked-up piece
        """
        self.clear()
        self.set_square(from_index, BLUE) # Highlight the piece being held
        
        for move in move_list:
            to_index = self.chess_square_to_index(move.to_square)
            
            # Check if the destination square is occupied (a capture)
            if board_state[to_index]:
                self.set_square(to_index, RED)
            else:
                self.set_square(to_index, GREEN)
        
        self.show()

    def show_best_move_hint(self, move):
        """Highlights the best move (from Stockfish) in CYAN."""
        from_index = self.chess_square_to_index(move.from_square)
        to_index = self.chess_square_to_index(move.to_square)
        
        # We set these *on top of* any legal move highlights
        self.set_square(from_index, CYAN)
        self.set_square(to_index, CYAN)
        self.show() # Update the LEDs with the new hint

    def play_illegal_move_animation(self):
        """Flashes all LEDs red to indicate an illegal move."""
        for _ in range(3):
            self.fill(RED)
            self.show()
            time.sleep(0.1)
            self.clear()
            self.show()
            time.sleep(0.1)

    def play_game_over_animation(self):
        """Simple animation for checkmate/stalemate."""
        colors = [RED, WHITE, RED, WHITE, BLACK]
        for color in colors:
            self.fill(color)
            self.show()
            time.sleep(0.5)

    # -------------------------------------------------
    # MAPPING HELPERS (Must match your wiring!)
    # -------------------------------------------------

    @staticmethod
    def index_to_chess_square(index):
        """Converts a 0-63 board index to a 'chess.Square' (e.g., 0 -> chess.A1)."""
        rank = index // 8
        file = index % 8
        return chess.square(file, rank)

    @staticmethod
    def chess_square_to_index(square):
        """Converts a 'chess.Square' to a 0-63 board index (e.g., chess.A1 -> 0)."""
        return square
