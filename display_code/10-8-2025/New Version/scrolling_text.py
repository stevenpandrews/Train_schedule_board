# scrolling_text.py
# A helper module for creating a scrolling text display group.

import displayio
from adafruit_display_text import scrolling_label
from adafruit_bitmap_font import bitmap_font

def create_scrolling_text_group(text, display):
    """Creates and returns a displayio.Group for scrolling text."""
    
    # --- Font and Color ---
    font = bitmap_font.load_font("/fonts/6x10.bdf")
    color = 0xFF0000  # Red for the alert

    # --- Create the Label ---
    # ** THE FIX IS HERE **
    # We tell the label it can only show about 10 characters at a time.
    # Since the full text is longer, it will be forced to scroll.
    scroll_label = scrolling_label.ScrollingLabel(
        font,
        text=text,
        color=color,
        max_characters=10, # Force the text to scroll on a 64-pixel wide display
        animate_time=0.3   # Speed of the scroll
    )
    
    # --- Set Position ---
    # Center the label vertically
    scroll_label.x = 10 
    scroll_label.y = display.height // 2

    # --- Create the Group ---
    text_group = displayio.Group()
    text_group.append(scroll_label)
    
    return text_group