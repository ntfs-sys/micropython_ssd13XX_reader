# micropython_ssd13XX_reader

Project implements reading data from SSD13XX controller displays (SSD1306, SSD1309 and similar) using MicroPython. Suitable for embedded systems like Raspberry Pi Pico or ESP32.

## Installation
1. Install MicroPython firmware on the device (from micropython.org).
2. Copy project files to the device:
   ```
   main.py
   ssd13xx_reader.py
   ```
3. Connect display: SCL to GP1, SDA to GP0 (or per schematic), VCC 3.3V, GND.

## Usage
Import module in `main.py`:
```python
from ssd13xx_reader import SSD13XXReader
import machine

i2c = machine.I2C(0, sda=machine.Pin(0), scl=machine.Pin(1), freq=400000)
reader = SSD13XXReader(i2c, addr=0x3C)
reader.init_display()
reader.read_frame(buffer_size=1024)  # Reads frame into buffer
print(reader.get_image())  # Outputs image (optional)
```
Configure I2C address (0x3C/0x3D), display dimensions (128x64 etc.) in class.

## Structure
- `main.py` — entry point, initialization and read loop.
- `ssd13xx_reader.py` — driver: init, read_frame, dump_data.
- `requirements.txt` — dependencies (thop, framebuf).

## Configuration
Edit parameters in `ssd13xx_reader.py`:
- `HEIGHT = 64`
- `WIDTH = 128`
- `I2C_ADDR = 0x3C`

## Debugging
- Logs via `print`.
- Test I2C: `i2c.scan()`.
- For Pico use Thonny or rshell.

## Compatibility
- MicroPython 1.20+.
- Displays: SSD1306/1309/1315.
- Platforms: RP2040, ESP8266/32.

License: MIT. Contributions welcome via PR.