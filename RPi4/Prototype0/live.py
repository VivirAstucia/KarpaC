import gpiozero as gpio
import time
from typing import *

class Expander:
    def __init__(self, address):
        self.address = address
        self.pins = [gpio.MCP23017(address=address).pin(i) for i in range(16)]

# Controlling 4*16 Hall sensor pins with 4 PIN Expanders for detecting chess pieces
class HallSensorArray:
    def __init__(self, expander_pins):
        """
        Expander_Pins is a list of I2C addresses for the MCP23017 expanders.
        """
        self.expanders = [gpio.MCP23017(address=addr) for addr in expander_pins]
        self.sensors = []
        for expander in self.expanders:
            for pin in range(16):
                sensor = gpio.DigitalInputDevice(expander.pin(pin), pull_up=True)
                self.sensors.append(sensor)

        self._hall_map :Dict[Tuple[int, int],int] = {}

    def read_sensors(self):
        return [sensor.value for sensor in self.sensors]
    

class LEDs: #ws2812b
    def __init__(self, pins, count=16):
        """
        pins is a list of GPIO pins where the LED strips are connected
        count is the number of LEDs per strip
        """
        self.count,self.pins = count,pins
        self._leds = [gpio.Neopixel(pin, count) for pin in pins]
        
        #64 leds
        self._led_map :Dict[Tuple[int, int],int] = {} #mapping of physical LED coordinates to logical indices
        
        self.colors = {
            'off': (0, 0, 0),
            'red': (255, 0, 0),
            'green': (0, 255, 0),
            'blue': (0, 0, 255),
            'white': (255, 255, 255),
            'yellow': (255, 255, 0),
            'purple': (128, 0, 128),
            'cyan': (0, 255, 255),
            'default': (0, 0, 0)
        }
        
    def set_led(self, index, color_name):
        color = self.colors.get(color_name, (0, 0, 0))
        physical_index = self._led_map.get(index, index)
        strip_index = physical_index // self.count
        led_index = physical_index % self.count
        self._leds[strip_index][led_index] = color
        self._leds[strip_index].show()

