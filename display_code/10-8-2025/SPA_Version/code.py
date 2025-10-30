# OCTOBER 30 2025 (v20 - Conditional Zero Padding)
# Jorge Enrique Gamboa Fuentes
# Subway schedule board with multiple modes
# REFRESHED: Implements conditional zero padding for minutes < 10.

import time
import microcontroller
import board
import sys # Import sys for printing exceptions
from board import NEOPIXEL
import displayio
import adafruit_display_text.label
from adafruit_bitmap_font import bitmap_font
from adafruit_matrixportal.matrix import Matrix
from adafruit_matrixportal.network import Network
import digitalio
from adafruit_debouncer import Debouncer
import json # Explicitly import json for manual parsing
import gc # Import garbage collection module

# Import the new helper file (assuming scrolling_text.py exists)
import scrolling_text

# --- Button Setup ---
pin_up = digitalio.DigitalInOut(board.BUTTON_UP)
pin_up.direction = digitalio.Direction.INPUT
pin_up.pull = digitalio.Pull.UP
button_up = Debouncer(pin_up)

pin_down = digitalio.DigitalInOut(board.BUTTON_DOWN)
pin_down.direction = digitalio.Direction.INPUT
pin_down.pull = digitalio.Pull.UP
button_down = Debouncer(pin_down)


# --- Mode Setup ---
TRAIN_SCHEDULE_MODE = 0
SECURITY_ALERT_MODE = 1
current_mode = TRAIN_SCHEDULE_MODE
MODE_COUNT = 2

# --- CONFIGURABLE PARAMETERS ---
BOARD_TITLE = 'To School'
STOP_ID = '2706'
ROUTES = '89,101' 
BACKGROUND_IMAGE = 'Tbanner.bmp'

# V3 API format
DATA_SOURCE = f'https://api-v3.mbta.com/predictions?filter[stop]={STOP_ID}&filter[route]={ROUTES}&sort=departure_time&include=route&page[limit]=3'
UPDATE_DELAY = 15
SYNC_TIME_DELAY = 120 # Sync time less often

# --- Display setup ---
matrix = Matrix()
display = matrix.display
network = Network(status_neopixel=NEOPIXEL)

# =======================================================================
#               TIME PARSING HELPER
# =======================================================================

def iso_to_local_epoch(iso_time_str):
    """
    Parses an ISO 8601 time string into local epoch time.
    """
    if not iso_time_str:
        return 0

    try:
        # Extract components: Year, Month, Day, Hour, Minute, Second
        year = int(iso_time_str[0:4])
        month = int(iso_time_str[5:7])
        day = int(iso_time_str[8:10])
        hour = int(iso_time_str[11:13])
        minute = int(iso_time_str[14:16])
        second = int(iso_time_str[17:19])
        
        # Create a time tuple: (year, month, day, hour, min, sec, weekday, yearday, dst)
        time_tuple = (year, month, day, hour, minute, second, 0, 0, -1)
        
        # Convert the time tuple to local epoch seconds
        return time.mktime(time_tuple)
    except Exception as e:
        print(f"ISO parse error: {e}")
        return 0

# =======================================================================
#               MODE 0: TRAIN SCHEDULE FUNCTIONS
# =======================================================================
def setup_train_schedule_group():
    """Creates and returns the displayio.Group for the train schedule."""
    group = displayio.Group()
    try:
        bitmap = displayio.OnDiskBitmap(open(BACKGROUND_IMAGE, 'rb'))
        group.append(displayio.TileGrid(bitmap, pixel_shader=bitmap.pixel_shader))
    except Exception as e:
        print(f"Error loading background image: {e}")
        group.append(displayio.Group())

    colors = [0x444444, 0xDD8000, 0x9966cc] # [dim white, gold, purple]
    font = bitmap_font.load_font("/fonts/6x10.bdf")

    # Indices: 0=Background/Placeholder, 1=Title, 2/3/4=Prediction Lines
    text_lines = [
        adafruit_display_text.label.Label(font, color=colors[0], x=7, y=3, text=BOARD_TITLE),
        adafruit_display_text.label.Label(font, color=colors[1], x=7, y=11, text="---"),
        adafruit_display_text.label.Label(font, color=colors[1], x=7, y=20, text="---"),
        adafruit_display_text.label.Label(font, color=colors[1], x=7, y=28, text="---"),
    ]
    for line in text_lines:
        group.append(line)
    return group

def update_train_schedule(group):
    """Fetches train data from V3 API and updates the train schedule group with relative time."""
    print("Fetching V3 train prediction data...")
    colors = [0x444444, 0xDD8000, 0x9966cc]
    
    # Get current time once for comparison
    current_epoch = time.time()
    
    # --- FIX: Validate current epoch time ---
    if current_epoch < 1577836800:
        print("System time is likely unsynced or invalid. Displaying error.")
        group[2].text = "TIME"
        group[3].text = "UNSYNCED"
        group[4].text = "Check WIFI"
        return
    # ---------------------------------------
    
    try:
        raw_json = network.fetch_data(DATA_SOURCE, json_path=[])
        json_data = json.loads(raw_json)
        
        # --- GC Optimization: Delete raw JSON string immediately ---
        del raw_json 
        gc.collect() 
        # ---------------------------------------------------------
        
        predictions = json_data.get('data', [])
        
        for i in range(3):
            display_text = "-----"
            # Prediction labels start at index 2 (group[2], group[3], group[4])
            pred_label = group[i + 2] 
            pred_label.color = colors[1] # Default color (Gold)
            
            if i < len(predictions):
                try:
                    # --- Optimization: Reference objects once to reduce lookups/temp dicts ---
                    prediction = predictions[i]
                    attributes = prediction.get('attributes', None)
                    relationships = prediction.get('relationships', None) 

                    status = ""
                    if attributes is not None:
                         status = str(attributes.get('status', '')).upper()
                    # --------------------------------------------------------------------------
                    
                    if status in ('BOARDING', 'BRDNG', 'ARRIVING'):
                        display_text = "BRDNG"
                        pred_label.color = colors[2] # Purple for boarding
                    else:
                        time_raw = None
                        if attributes is not None:
                            # Prioritize departure_time, then arrival_time
                            time_raw = attributes.get('departure_time')
                            if not time_raw:
                                time_raw = attributes.get('arrival_time')

                        if time_raw:
                            # 1. Convert the prediction time to epoch seconds
                            prediction_epoch = iso_to_local_epoch(time_raw)
                            
                            # 2. Calculate the difference in minutes
                            time_diff_sec = prediction_epoch - current_epoch
                            time_diff_min = round(time_diff_sec / 60)
                            
                            # Safely get the route ID
                            route_id_data = relationships.get('route', {}).get('data', {}) if relationships else {} 
                            route_id = f"{route_id_data.get('id', '??'):>3}"
                            
                            if time_diff_min <= 0:
                                # This is the state change identified by the user
                                display_text = f"{route_id} NOW"
                                pred_label.color = colors[2] # Purple for immediate departure
                            else:
                                # --- CONDITIONAL PADDING LOGIC ---
                                if time_diff_min < 10:
                                    # Pad: 5 -> "05"
                                    minute_str = f"{time_diff_min:02d}"
                                else:
                                    # No pad: 12 -> "12"
                                    minute_str = str(time_diff_min)
                                
                                # Display route ID and time until (e.g., "89 05 min")
                                display_text = f"{route_id} {minute_str}min"
                        else:
                            # If no time, but there is a status, use the status
                            display_text = status if status else "N/A"
                            
                except Exception as e:
                    print(f"Error parsing prediction {i} data structure:")
                    print(e) 
                    display_text = "PARSE ERR"
                    pred_label.color = 0xFF0000 # Red error

            pred_label.text = display_text
            
        # --- GC Optimization: Clean up after prediction loop ---
        del json_data 
        gc.collect() 
        # -------------------------------------------------------
            
    except Exception as e:
        # Re-raise memory error if it occurs here, so it can be caught by the main loop reset logic
        print("Error fetching V3 train data:")
        print(e) 
        
        # Display connection/API error
        group[2].text = "V3"
        group[3].text = "API"
        group[4].text = "Error"
        raise # Re-raise to trigger error_counter increment

# Initialize Mode Groups
train_schedule_group = setup_train_schedule_group()

# =======================================================================
#               MODE 1: SECURITY ALERT FUNCTIONS
# =======================================================================
security_alert_group = scrolling_text.create_scrolling_text_group(
    "Security alert activated", display
)

# Set initial display group
display.root_group = train_schedule_group 

# =======================================================================
#                          INITIAL SETUP
# =======================================================================
error_counter = 0
last_sync = 0
last_train_update = 0
MAX_FAILURES = 4 # --- ADDED: Constant for reset limit ---

# --- FIX: Force initial time sync before main loop starts ---
print("Initial time sync...")
try:
    network.get_local_time()
    last_sync = time.monotonic()
    gc.collect() 
except Exception as e:
    print("Initial time sync failed (will retry in main loop):", e)
    error_counter = 1 # Start counter if initial sync fails
# -----------------------------------------------------------


# =======================================================================
#                          MAIN LOOP
# =======================================================================
while True:
    # --- Step 1: Check for button presses to change mode ---
    button_up.update()
    button_down.update()

    if button_up.fell or button_down.fell:
        new_mode = (current_mode + 1) % MODE_COUNT
        
        if new_mode != current_mode:
            current_mode = new_mode
            print(f"Mode changed to: {current_mode}")
            last_train_update = 0 # Force immediate update on mode change
            
            # --- Centralized Display Management ---
            if current_mode == TRAIN_SCHEDULE_MODE:
                display.root_group = train_schedule_group
            elif current_mode == SECURITY_ALERT_MODE:
                display.root_group = security_alert_group
            
            gc.collect()

    # --- Step 2: Run the code for the current mode ---
    if current_mode == TRAIN_SCHEDULE_MODE:
        # Sync time if needed (Crucial for accurate time calculation!)
        if time.monotonic() > last_sync + SYNC_TIME_DELAY:
            try:
                print("Syncing time...")
                network.get_local_time() 
                last_sync = time.monotonic()
                error_counter = 0 # Reset counter on sync success
                gc.collect() 
            except Exception as e:
                print("Time sync failed:", e)
                error_counter += 1 # Increment counter on sync failure

        # Update train data if it's time
        if time.monotonic() > last_train_update + UPDATE_DELAY:
            try:
                update_train_schedule(train_schedule_group)
                last_train_update = time.monotonic()
                error_counter = 0 # Reset counter on update success
            except Exception as e:
                # Catch MemoryError or other failures re-raised from update_train_schedule
                print("Critical update failure caught in main loop:", e)
                error_counter += 1 # Increment counter on update failure
        
        # --- ADDED: RESET CHECK ---
        if error_counter >= MAX_FAILURES:
            print(f"!!! CRITICAL FAILURE: {error_counter} consecutive errors. Resetting board. !!!")
            # Wait briefly to let the message display before reboot
            time.sleep(5) 
            microcontroller.reset()
        # ---------------------------

    elif current_mode == SECURITY_ALERT_MODE:
        # The scrolling_label animates itself
        security_alert_group[0].update()

    # A tiny sleep to prevent the loop from running too fast
    time.sleep(0.1)