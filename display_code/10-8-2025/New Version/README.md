# MBTA Blue Line Train Schedule Display

October 10 2025

This project turns an Adafruit Matrix Portal S3 and an RGB LED matrix into a real-time train schedule display. It shows the next three departure times for the MBTA Blue Line from Wonderland station heading towards Bowdoin.

!(https://cdn-learn.adafruit.com/assets/assets/000/111/988/original/adafruit_products_5398_iso_ORIG_2022_07.jpg)

---

## Requirements

For this project to work, you **must** be running the latest versions of both the CircuitPython firmware and the Adafruit CircuitPython Library Bundle. Old versions will cause security errors (SSL Handshake Errors) when trying to connect to the MBTA's modern API.

1.  **Latest CircuitPython Firmware for Matrix Portal S3:** This is the operating system for your board.
    * **Download the .uf2 file here:** [https://circuitpython.org/board/adafruit_matrixportal_s3/](https://circuitpython.org/board/adafruit_matrixportal_s3/)

2.  **Latest Adafruit CircuitPython Library Bundle:** These are the drivers needed to talk to the hardware and the internet.
    * **Download the bundle here:** [https://circuitpython.org/libraries](https://circuitpython.org/libraries)

---

## Installation

### 1. Update Firmware (Install the .uf2 file)

You must install the latest CircuitPython firmware to avoid connection errors.

* Connect your Matrix Portal S3 to your computer via a USB-C data cable.
* **Quickly double-press the Reset button** on the back of the board.
* The RGB status light will turn **green**, and a new USB drive called **`PRTLS3BOOT`** will appear on your computer.
* Drag and drop the `.uf2` file you downloaded onto the `PRTLS3BOOT` drive.
* The board will automatically restart. A new drive called `CIRCUITPY` will appear.

### 2. Copy Project Files

* Unzip the Library Bundle you downloaded. Copy the entire `lib` folder to your `CIRCUITPY` drive.
* Copy all the files from this project (`code.py`, `Tblue-dashboard.bmp`, the `fonts` folder, and your `secrets.py` file) to the main level of the `CIRCUITPY` drive.

---

## How It Works

This code connects to your local Wi-Fi and then reaches out to a public MBTA (Massachusetts Bay Transportation Authority) API to get live train data.

It specifically requests the schedule for the **Blue Line**, at the **Wonderland (`place-wondl`)** stop, for trains heading in **direction 0 (Westbound towards Bowdoin)**.

The code fetches the data, formats the upcoming departure times (e.g., "5 min", "12 min", "brding"), and displays them on the RGB matrix over a background image. The data automatically refreshes every 15 seconds.

### API Information

The code makes a `GET` request to the following API endpoint to retrieve the schedule:

`https://www.mbta.com/schedules/finder_api/departures?id=Blue&stop=place-wondl&direction=0`