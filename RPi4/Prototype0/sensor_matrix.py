import adafruit_mcp23017
from digitalio import Direction, Pull

SENSOR_ACTIVE_LOW = True
I2C_ADDRESSES = [0x20, 0x21, 0x22, 0x23]
class SensorMatrix:
    """Manages the 4x MCP23017 I/O expanders to read 64 sensors."""
    
    def __init__(self, i2c):
        self.mcps = []
        self.pins = []
        try:
            for addr in I2C_ADDRESSES:
                mcp = adafruit_mcp23017.MCP23017(i2c, address=addr)
                self.mcps.append(mcp)
            print(f"Successfully initialized {len(self.mcps)} MCP23017 expanders.")
        except Exception as e:
            print(f"FATAL ERROR: Could not initialize MCP23017. Check I2C wiring and addresses.")
            print(f"Error: {e}")
            raise
            
        # Store all 64 pin objects for faster access
        for mcp in self.mcps:
            for i in range(16): # GPA0-7, GPB0-7
                pin = mcp.get_pin(i)
                pin.direction = Direction.INPUT
                pin.pull = Pull.UP # Use internal pull-ups
                self.pins.append(pin)

    def read_board_state(self):
        """
        Reads all 64 sensors and returns a list of booleans.
        True = Occupied (piece present)
        False = Empty
        """
        state = [False] * 64
        for i in range(64):
            pin_value = self.pins[i].value
            # If sensor is active-low, a LOW value (False) means a piece is present
            if SENSOR_ACTIVE_LOW:
                state[i] = not pin_value
            else:
                state[i] = pin_value
        return state
