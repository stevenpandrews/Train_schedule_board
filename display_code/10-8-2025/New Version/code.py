# OCTOBER 10 2025 (v8 - Final)
# Jorge Enrique Gamboa Fuentes
# Subway schedule board - single direction
# Data from: Boston - MBTA

import time
import microcontroller
import board
from board import NEOPIXEL
import displayio
import adafruit_display_text.label
from adafruit_datetime import datetime
from adafruit_bitmap_font import bitmap_font
from adafruit_matrixportal.matrix import Matrix
from adafruit_matrixportal.network import Network
import json
import traceback

# --- CONFIGURABLE PARAMETERS ---
BOARD_TITLE = 'Bowdoin'
STOP_ID = 'place-wondl'
DIRECTION_ID = '0'
ROUTE = 'Blue'
BACKGROUND_IMAGE = 'Tblue-dashboard.bmp'
DATA_SOURCE = f'https://www.mbta.com/schedules/finder_api/departures?id={ROUTE}&stop={STOP_ID}&direction={DIRECTION_ID}'
UPDATE_DELAY = 15
SYNC_TIME_DELAY = 30
ERROR_RESET_THRESHOLD = 3

# --- Functions ---
def get_and_update_arrivals():
    """
    Fetches train data from the MBTA API and updates the display lines directly.
    """
    print("Fetching new data from: " + DATA_SOURCE)
    
    try:
        # The fetch_data function with json_path=[] now returns a parsed JSON object (a list/dict).
        # We no longer need to call json.loads() on it.
        schedule = network.fetch_data(DATA_SOURCE, json_path=[])

        for i in range(3):
            display_text = "-----"
            if i < len(schedule):
                try:
                    time_parts = schedule[i]['realtime']['prediction']['time']
                    
                    if time_parts[0].lower() in ('boarding', 'arriving', 'brding'):
                        display_text = "brding"
                        text_lines[i + 2].color = colors[2] # Purple for boarding
                    else:
                        display_text = "".join(time_parts)
                        text_lines[i + 2].color = colors[1] # Gold for times
                except (KeyError, IndexError):
                    print(f"Could not parse train {i+1}")
                    pass
            
            text_lines[i + 2].text = display_text

    except Exception as e:
        print("--- ERROR ---")
        print("An error occurred while fetching or processing data:")
        traceback.print_exception(type(e), e, e.__traceback__)
        text_lines[2].text = "Error"
        text_lines[3].text = "Check"
        text_lines[4].text = "Log"

    display.root_group = group

# --- Display setup ---
matrix = Matrix()
display = matrix.display
network = Network(status_neopixel=NEOPIXEL, debug=False)

# --- Drawing setup ---
group = displayio.Group()
bitmap = displayio.OnDiskBitmap(open(BACKGROUND_IMAGE, 'rb'))
colors = [0x444444, 0xDD8000, 0x9966cc] # [dim white, gold, purple]
font = bitmap_font.load_font("fonts/6x10.bdf")

text_lines = [
    displayio.TileGrid(bitmap, pixel_shader=bitmap.pixel_shader),
    adafruit_display_text.label.Label(font, color=colors[0], x=20, y=3, text=BOARD_TITLE),
    adafruit_display_text.label.Label(font, color=colors[1], x=26, y=11, text="|||"),
    adafruit_display_text.label.Label(font, color=colors[1], x=26, y=20, text="---"),
    adafruit_display_text.label.Label(font, color=colors[1], x=26, y=28, text="---"),
]
for line in text_lines:
    group.append(line)

display.root_group = group

# --- Main Loop ---
error_counter = 0
last_time_sync = 0
while True:
    try:
        if time.monotonic() > last_time_sync + SYNC_TIME_DELAY:
            print("Syncing time...")
            network.get_local_time()
            last_time_sync = time.monotonic()
            print("Time synced!")
        
        get_and_update_arrivals()

    except Exception as e:
        print("An error occurred in the main loop:")
        traceback.print_exception(type(e), e, e.__traceback__)
        error_counter += 1
        if error_counter > ERROR_RESET_THRESHOLD:
            print("Too many errors, resetting device.")
            microcontroller.reset()
    
    print(f"Waiting {UPDATE_DELAY} seconds...")
    time.sleep(UPDATE_DELAY)