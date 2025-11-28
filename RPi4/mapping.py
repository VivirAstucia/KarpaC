import RPi.GPIO as GPIO
import time
import board, neopixel

LED = board.D18
GPIO.setmode(GPIO.BCM)
ORDER = neopixel.GRB
color = {
    ' ': (0, 0, 0),
    'R': (255, 0, 0),
    'G': (0, 255, 0),
    'B': (0, 0, 255),
    'W': (255, 255, 255),
    'Y': (255, 255, 0),
    'P': (128, 0, 128),
    'C': (0, 255, 255)
}

class ChessBoard():
    def __init__(self):
        self.H_OUT = [10, 9, 11, 5, 6, 13, 19, 26]
        self.H_IN = [25, 8, 7, 1, 12, 16, 20, 21]
        #self.H_OUT = [19, 21, 23, 29, 31, 33, 35, 37]
        #self.H_IN = [22, 24, 26, 28, 32, 36, 38, 40]
        self.initialize_hall()
        self.strip = neopixel.NeoPixel(LED, 4*len(self.H_OUT)*len(self.H_IN), brightness=0.2, auto_write=False, pixel_order=ORDER)
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

    def update_leds(self, pattern):
        for i in range(len(self.H_IN)):
            for j in range(len(self.H_OUT)):
                square_indices = self.square[i][j]
                color_value = color.get(pattern[i][j], (0, 0, 0))
                for index in square_indices:
                    self.strip[index] = color_value
        self.strip.show()

    def reset_board(self):
        self.grid = [[0 for _ in range(len(self.H_OUT))] for _ in range(len(self.H_IN))]
        self.prev = [[self.grid[i][j] for j in range(len(self.H_OUT))] for i in range(len(self.H_IN))]
        self.strip.fill((0, 0, 0))
        self.strip.show()
        
    

    def game(self):
        try:
            while True:
                self.read_hall()
                print(self.grid)
                self.update_leds([['R' if val else 'B' for val in row] for row in self.grid])
                time.sleep(0.1)
        except KeyboardInterrupt:
            self.strip.fill((0, 0, 0))
            self.strip.show()
            GPIO.cleanup()
            time.sleep(1)
            

if __name__ == "__main__":
    chessboard = ChessBoard()
    chessboard.game()

