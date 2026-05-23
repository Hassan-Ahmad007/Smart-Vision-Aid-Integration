import asyncio
import serial
from winsdk.windows.devices.geolocation import Geolocator
from navigation.config import GPS_MODE


class GPSInput:
    def __init__(self):
        if GPS_MODE == "laptop":
            self.locator = Geolocator()
            self.locator.desired_accuracy_in_meters = 50

        elif GPS_MODE == "arduino":
            self.ser = serial.Serial('COM5', 9600, timeout=1)

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

            print(f"GPS (Laptop): {lat}, {lon}")
            return lat, lon, 0, 999

        except Exception as e:
            print("GPS ERROR (Laptop):", e)
            return None

    # ---------------- ARDUINO GPS ----------------
    def arduino_gps(self):
        try:
            line = self.ser.readline().decode().strip()

            # expected format:
            # LAT:xx,LON:yy,OBS:0,DIST:999
            data = {}
            for item in line.split(","):
                k, v = item.split(":")
                data[k] = float(v)

            lat = data["LAT"]
            lon = data["LON"]
            obs = data.get("OBS", 0)
            dist = data.get("DIST", 999)

            print(f"GPS (Arduino): {lat}, {lon}")
            return lat, lon, obs, dist

        except Exception as e:
            print("GPS ERROR (Arduino):", e)
            return None

    # ---------------- MAIN ENTRY ----------------
    def get_location(self):
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            future = asyncio.wait_for(self._get_coords(), timeout=5)
            lat, lon = loop.run_until_complete(future)

            # save last good value
            self.last_location = (lat, lon)

            print(f"GPS (Laptop): {lat}, {lon}")
            return lat, lon, 0, 999

        except Exception as e:
            print("GPS ERROR (Laptop):", e)

            # 🔴 USE LAST KNOWN LOCATION
            if hasattr(self, "last_location"):
                lat, lon = self.last_location
                print(f"USING LAST GPS: {lat}, {lon}")
                return lat, lon, 0, 999

            return None