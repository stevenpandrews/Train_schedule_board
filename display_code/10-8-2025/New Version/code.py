# OCTOBER 11 2025 (v9 - Button Control)
# Jorge Enrique Gamboa Fuentes
# Subway schedule board with multiple modes

import time
import microcontroller
import board
from board import NEOPIXEL
import displayio
import adafruit_display_text.label
from adafruit_bitmap_font import bitmap_font
from adafruit_matrixportal.matrix import Matrix
from adafruit_matrixportal.network import Network
import traceback
import digitalio
from adafruit_debouncer import Debouncer

# Import the new helper file
import scrolling_text

# --- Button Setup ---
# UP button is for switching to the next mode
pin_up = digitalio.DigitalInOut(board.BUTTON_UP)
pin_up.direction = digitalio.Direction.INPUT
pin_up.pull = digitalio.Pull.UP
button_up = Debouncer(pin_up)

# DOWN button is also for switching
pin_down = digitalio.DigitalInOut(board.BUTTON_DOWN)
pin_down.direction = digitalio.Direction.INPUT
pin_down.pull = digitalio.Pull.UP
button_down = Debouncer(pin_down)


# --- Mode Setup ---
# We will use numbers to represent each mode
TRAIN_SCHEDULE_MODE = 0
SECURITY_ALERT_MODE = 1
# Start in train schedule mode
current_mode = TRAIN_SCHEDULE_MODE
MODE_COUNT = 2 # Total number of modes

# --- CONFIGURABLE PARAMETERS ---
BOARD_TITLE = 'Bowdoin'
STOP_ID = 'place-wondl'
DIRECTION_ID = '0'
ROUTE = 'Blue'
BACKGROUND_IMAGE = 'Tblue-dashboard.bmp'
DATA_SOURCE = f'https://www.mbta.com/schedules/finder_api/departures?id={ROUTE}&stop={STOP_ID}&direction={DIRECTION_ID}'
UPDATE_DELAY = 15
SYNC_TIME_DELAY = 120 # Sync time less often to avoid interruptions
ERROR_RESET_THRESHOLD = 5

# --- Display setup ---
matrix = Matrix()
display = matrix.display
network = Network(status_neopixel=NEOPIXEL, debug=False)


# =======================================================================
#               MODE 0: TRAIN SCHEDULE FUNCTIONS
# =======================================================================
def setup_train_schedule_group():
    """Creates and returns the displayio.Group for the train schedule."""
    group = displayio.Group()
    bitmap = displayio.OnDiskBitmap(open(BACKGROUND_IMAGE, 'rb'))
    colors = [0x444444, 0xDD8000, 0x9966cc] # [dim white, gold, purple]
    font = bitmap_font.load_font("/fonts/6x10.bdf")

    text_lines = [
        displayio.TileGrid(bitmap, pixel_shader=bitmap.pixel_shader),
        adafruit_display_text.label.Label(font, color=colors[0], x=20, y=3, text=BOARD_TITLE),
        adafruit_display_text.label.Label(font, color=colors[1], x=26, y=11, text="---"),
        adafruit_display_text.label.Label(font, color=colors[1], x=26, y=20, text="---"),
        adafruit_display_text.label.Label(font, color=colors[1], x=26, y=28, text="---"),
    ]
    for line in text_lines:
        group.append(line)
    return group

def update_train_schedule(group):
    """Fetches train data and updates the train schedule group."""
    print("Fetching train data...")
    text_lines = [group[1], group[2], group[3], group[4]] # Text labels are at these indices
    colors = [0x444444, 0xDD8000, 0x9966cc]
    
    try:
        schedule = network.fetch_data(DATA_SOURCE, json_path=[])
        for i in range(3):
            display_text = "-----"
            if i < len(schedule):
                try:
                    time_parts = schedule[i]['realtime']['prediction']['time']
                    if time_parts[0].lower() in ('boarding', 'arriving', 'brding'):
                        display_text = "brding"
                        group[i + 2].color = colors[2]
                    else:
                        display_text = "".join(time_parts)
                        group[i + 2].color = colors[1]
                except (KeyError, IndexError): pass
            group[i + 2].text = display_text
    except Exception as e:
        print("Error fetching train data:", e)
        group[2].text = "Error"
        group[3].text = "Check"
        group[4].text = "Log"

# Create the display group for the train schedule now
train_schedule_group = setup_train_schedule_group()

# =======================================================================
#               MODE 1: SECURITY ALERT FUNCTIONS
# =======================================================================
security_alert_group = scrolling_text.create_scrolling_text_group(
    "Security alert activated", display
)

# =======================================================================
#                          MAIN LOOP
# =======================================================================
error_counter = 0
last_sync = 0
last_train_update = 0

while True:
    # --- Step 1: Check for button presses to change mode ---
    button_up.update()
    button_down.update()

    if button_up.fell or button_down.fell:
        current_mode = (current_mode + 1) % MODE_COUNT
        print(f"Mode changed to: {current_mode}")
        # When we change modes, force an immediate update
        last_train_update = 0

    # --- Step 2: Run the code for the current mode ---
    if current_mode == TRAIN_SCHEDULE_MODE:
        display.root_group = train_schedule_group
        
        # Sync time if needed
        if time.monotonic() > last_sync + SYNC_TIME_DELAY:
            try:
                network.get_local_time()
                last_sync = time.monotonic()
            except Exception as e:
                print("Time sync failed:", e)

        # Update train data if it's time
        if time.monotonic() > last_train_update + UPDATE_DELAY:
            update_train_schedule(train_schedule_group)
            last_train_update = time.monotonic()

    elif current_mode == SECURITY_ALERT_MODE:
        display.root_group = security_alert_group
        # The scrolling_label animates itself, but we need to tell it to update
        security_alert_group[0].update()

    # A tiny sleep to prevent the loop from running too fast
    time.sleep(0.01)