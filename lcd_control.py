import time
from RPLCD.i2c import CharLCD
lcd = CharLCD('PCF8574', 0x27)

def write_to_lcd(lcd, framebuffer, num_cols):
  """Write the framebuffer out to the specified LCD."""
  lcd.home()
  for row in framebuffer:
    lcd.write_string(row.ljust(num_cols)[:num_cols])
    lcd.write_string('\r\n')

def loop_string(string, lcd, framebuffer, row, num_cols, delay=0.2):
  padding = ' ' * num_cols
  s = padding + string + padding
  for i in range(len(s) - num_cols + 1):
    framebuffer[row] = s[i:i+num_cols]
    write_to_lcd(lcd, framebuffer, num_cols)
    time.sleep(delay)

def display_message(staticLine, scrollLine, period = 0):
  if period != 0:
    start = time.time()
    while True:
      loop_string(scrollLine, lcd, staticLine, 1, 16)
      if time.time() > start + period:
        loop_string("", lcd, "", 1, 16)
        break
  else:
    loop_string(scrollLine, lcd, staticLine, 1, 16)
