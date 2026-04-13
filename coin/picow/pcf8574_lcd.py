import time

LCD_BACKLIGHT = 0x08
ENABLE = 0x04
RW = 0x02
RS = 0x01

class PCF8574_LCD:
    def __init__(self, i2c, address=0x27, cols=16, rows=2):
        self.i2c = i2c
        self.address = address
        self.cols = cols
        self.rows = rows
        self.backlight = LCD_BACKLIGHT

        time.sleep(0.05)
        self._write4(0x30)
        time.sleep(0.005)
        self._write4(0x30)
        time.sleep(0.001)
        self._write4(0x30)
        time.sleep(0.001)
        self._write4(0x20)
        time.sleep(0.001)

        self.command(0x28)  # 4-bit, 2 line, 5x8
        self.command(0x0C)  # display on, cursor off
        self.command(0x06)  # entry mode
        self.command(0x01)  # clear
        time.sleep(0.002)

    def _expander_write(self, data):
        while not self.i2c.try_lock():
            pass
        try:
            self.i2c.writeto(self.address, bytes([data | self.backlight]))
        finally:
            self.i2c.unlock()

    def _pulse_enable(self, data):
        self._expander_write(data | ENABLE)
        time.sleep(0.0005)
        self._expander_write(data & ~ENABLE)
        time.sleep(0.0001)

    def _write4(self, data):
        self._expander_write(data)
        self._pulse_enable(data)

    def _send(self, value, mode=0):
        high = (value & 0xF0) | mode
        low = ((value << 4) & 0xF0) | mode
        self._write4(high)
        self._write4(low)

    def command(self, cmd):
        self._send(cmd, 0)

    def write_char(self, char):
        self._send(ord(char), RS)

    def clear(self):
        self.command(0x01)
        time.sleep(0.002)

    def home(self):
        self.command(0x02)
        time.sleep(0.002)

    def set_cursor(self, col, row):
        row_offsets = [0x00, 0x40, 0x14, 0x54]
        self.command(0x80 | (col + row_offsets[row]))

    def message(self, text):
        for char in text:
            if char == "\n":
                self.set_cursor(0, 1)
            else:
                self.write_char(char)

    def backlight_on(self):
        self.backlight = LCD_BACKLIGHT
        self._expander_write(0)

    def backlight_off(self):
        self.backlight = 0x00
        self._expander_write(0)
