# MicroPython SSD13XX Reader

A MicroPython‑based reader designed for RP2040 boards (tested on 16 MB ROM) with SSD1306 OLED displays. Includes PC‑side debugging tools for interface maintenance and easy testing.

## Features

- **MicroPython powered** – runs on RP2040 (Raspberry Pi Pico / Pico W, etc.)  
- **SSD1306 display support** – tested with 128×64 OLED over I²C  
- **PC debugging** – allows interface testing and maintenance from a computer  
- **Helper scripts** – split text chapters or topics for display  
- **Standalone HTML tool** – pixel editor for creating custom sprites or layouts  

## Hardware Requirements

- RP2040‑based board (e.g., Raspberry Pi Pico) with at least 16 MB flash  
- SSD1306 OLED display (I²C interface)  
- Connecting wires (GND, VCC, SCL, SDA)  

## Software & Dependencies

- MicroPython firmware for RP2040  
- `ssd1306.py` driver (included in most MicroPython builds, or copy from the repository)  
- Python 3 on PC for the helper scripts and debug tool  

## File Overview

| File | Description |
|------|-------------|
| `main.py` | Main firmware for the reader – initializes the display and runs the reading logic. |
| `split_chapters.py` | PC‑side script to split a text file into chapters for easier navigation on the device. |
| `split_topics.py` | Similar to `split_chapters.py`, but splits by topics or headings. |
| `SSD1306 Pixel Editor.html` | Offline HTML tool to design pixel art / UI elements for the display; saves as byte arrays for use in MicroPython. |
| `README.md` | This file. |

## Getting Started

### 1. Flash MicroPython on RP2040
Follow the official guide: [Raspberry Pi Pico Python SDK](https://datasheets.raspberrypi.com/pico/raspberry-pi-pico-python-sdk.pdf)

### 2. Upload the Code
Copy `main.py` and the SSD1306 driver (`ssd1306.py`) to the board using `mpremote`, `rshell`, or Thonny.

### 3. Connect the Display
| SSD1306 | RP2040 |
|---------|--------|
| VCC     | 3.3V   |
| GND     | GND    |
| SCL     | GP1    |
| SDA     | GP0    |

*Adjust pins in `main.py` if different.*

### 4. Run the Reader
Power the board or reset it. The display should show the reader interface.

### 5. PC Debugging
Use `split_chapters.py` or `split_topics.py` to prepare text files. The HTML pixel editor helps design icons and layouts – simply open it in any browser.

## Usage Notes

- The reader is intended for displaying pre‑formatted text files stored on the board’s filesystem.
- Use the PC scripts to split large texts into manageable chunks – each chunk becomes a separate file that the reader can load.
- The pixel editor outputs byte arrays compatible with the `framebuf` module – paste the output into your MicroPython code for custom graphics.

## Future Improvements

- Add button controls (previous/next page, menu)  
- Support for other SSD13XX displays (SSD1315, etc.)  
- Implement bookmarking and font selection  

## Contributing

Feel free to open issues or pull requests. Suggestions for enhancements are welcome.

## License

This project is currently unlicensed. If you intend to reuse or distribute it, please consider adding an open‑source license (e.g., MIT) or contact the author.

---

**Author:** [ntfs-sys](https://github.com/ntfs-sys)  
**Repository:** [github.com/ntfs-sys/micropython_ssd13XX_reader](https://github.com/ntfs-sys/micropython_ssd13XX_reader)
