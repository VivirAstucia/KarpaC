import board, neopixel, time

pixel_pin = board.D18     # GPIO18 (PWM)
num_pixels = 255
import random

ORDER = neopixel.GRB

pixels = neopixel.NeoPixel(pixel_pin, num_pixels, brightness=0.8, auto_write=False, pixel_order=ORDER)

def w(n, bias=2):
    """Return integer in [0, n-1], biased toward both ends."""
    r = random.random() ** bias
    if random.random() < 0.5:
        val = r  # near 0
    else:
        val = 1 - r  # near 1
    return int(val * n)

while True:
    # pixels.fill((255, 0, 0))  # Red
    # pixels.show()
    # time.sleep(1)
    # pixels.fill((0, 255, 0))  # Green
    for i in range(num_pixels):
        pixels[i] = (w(255), w(255), w(255))
    pixels.show()
    time.sleep(1)
