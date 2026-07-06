# =========================================
# navigation/gps_input.py
# =========================================

import asyncio
import serial
from winsdk.windows.devices.geolocation import Geolocator
from navigation.config import GPS_MODE


class GPSInput:
    def __init__(self):
        self.last_lat = None
        self.last_lon = None

        if GPS_MODE == "laptop":
            self.locator = Geolocator()
            self.locator.desired_accuracy_in_meters = 50

        elif GPS_MODE == "arduino":
            # Using COM4 as per your successful Bluetooth test script
            self.ser = serial.Serial('COM4', 9600, timeout=1)
            print("Bluetooth GPS connected on COM4 (Ultrasonic Ignored).")

    # ---------------- LAPTOP GPS ----------------
    async def _get_coords(self):
        pos = await self.locator.get_geoposition_async()
        lat = pos.coordinate.latitude
        lon = pos.coordinate.longitude
        return lat, lon

    def laptop_gps(self):
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            future = asyncio.wait_for(self._get_coords(), timeout=5)
            lat, lon = loop.run_until_complete(future)

            self.last_lat = lat
            self.last_lon = lon

            # Returning 0, 0 for obs and dist so we don't break unpacking in other files
            return lat, lon, 0, 0

        except Exception as e:
            print("GPS ERROR (Laptop):", e)
            if self.last_lat and self.last_lon:
                return self.last_lat, self.last_lon, 0, 0
            return None

    # ---------------- ARDUINO GPS (BLUETOOTH) ----------------
    def arduino_gps(self):
        try:
            # Read all lines currently sitting in the Bluetooth hardware buffer
            while self.ser.in_waiting > 0:
                line = self.ser.readline().decode("utf-8", errors="ignore").strip()

                # Parse ONLY Lat and Lon. Ignore any DIST coming from Arduino.
                if line.startswith("LAT:"):
                    self.last_lat = float(line.split(":")[1].strip())
                elif line.startswith("LON:"):
                    self.last_lon = float(line.split(":")[1].strip())

            if self.last_lat is not None and self.last_lon is not None:
                return self.last_lat, self.last_lon, 0, 0
            else:
                return None

        except Exception as e:
            print("GPS ERROR (Arduino Bluetooth):", e)
            if self.last_lat and self.last_lon:
                return self.last_lat, self.last_lon, 0, 0
            return None

    # ---------------- MAIN ENTRY ----------------
    def get_location(self):
        if GPS_MODE == "laptop":
            return self.laptop_gps()
        elif GPS_MODE == "arduino":
            return self.arduino_gps()
        else:
            print("ERROR: Invalid GPS_MODE in config.py")
            return None