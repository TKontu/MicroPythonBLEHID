# MicroPython Human Interface Device library
# Copyright (C) 2021 H. Groefsema
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.


# Implements a BLE HID mouse
import time
from machine import SoftSPI, Pin
from hid_services import Mouse

class Device:
    def __init__(self):
        # Define state
        self.x = 0
        self.y = 0

        self.prev_x = 0
        self.prev_y = 0

        # Define buttons
        self.pin_forward = Pin(5, Pin.IN)
        self.pin_reverse = Pin(23, Pin.IN)
        self.pin_right = Pin(19, Pin.IN)
        self.pin_left = Pin(18, Pin.IN)

        # Create our device
        self.mouse = Mouse("Mouse")
        # Set a callback function to catch changes of device state
        self.mouse.set_state_change_callback(self.mouse_state_callback)
        # Start our device
        self.mouse.start()

    # Function that catches device status events
    def mouse_state_callback(self):
        if self.mouse.get_state() is Mouse.DEVICE_IDLE:
            return
        elif self.mouse.get_state() is Mouse.DEVICE_ADVERTISING:
            return
        elif self.mouse.get_state() is Mouse.DEVICE_CONNECTED:
            return
        else:
            return

    def advertise(self):
        self.mouse.start_advertising()

    def stop_advertise(self):
        self.mouse.stop_advertising()

    # Main loop
    def start(self):
        while True:
            # Read pin values and update variables
            self.x = self.pin_right.value() * 127 - self.pin_left.value() * 127
            self.y = self.pin_forward.value() * 127 - self.pin_reverse.value() * 127

            # If the variables changed do something depending on the device state
            if (self.x != self.prev_x) or (self.y != self.prev_y):
                # Update values
                self.prev_x = self.x
                self.prev_y = self.y

                # If connected set axes and notify
                # If idle start advertising for 30s or until connected
                if self.mouse.get_state() is Mouse.DEVICE_CONNECTED:
                    self.mouse.set_axes(self.x, self.y)
                    self.mouse.notify_hid_report()
                elif self.mouse.get_state() is Mouse.DEVICE_IDLE:
                    self.mouse.start_advertising()
                    i = 10
                    while i > 0 and self.mouse.get_state() is Mouse.DEVICE_ADVERTISING:
                        time.sleep(3)
                        i -= 1
                    if self.mouse.get_state() is Mouse.DEVICE_ADVERTISING:
                        self.mouse.stop_advertising()

            if self.mouse.get_state() is Mouse.DEVICE_CONNECTED:
                time.sleep_ms(20)
            else:
                time.sleep(2)

    # Only for test
    def stop(self):
        self.mouse.stop()

    # Test routine
    def test(self):
        self.mouse.set_battery_level(50)
        self.mouse.notify_battery_level()

        for i in range(30):
            self.mouse.set_axes(100,100)
            self.mouse.set_buttons(1)
            self.mouse.notify_hid_report()
            time.sleep_ms(500)

            self.mouse.set_axes(100,-100)
            self.mouse.set_buttons()
            self.mouse.notify_hid_report()
            time.sleep_ms(500)

            self.mouse.set_axes(-100,-100)
            self.mouse.set_buttons(b2=1)
            self.mouse.notify_hid_report()
            time.sleep_ms(500)

            self.mouse.set_axes(-100,100)
            self.mouse.set_buttons()
            self.mouse.notify_hid_report()
            time.sleep_ms(500)

        self.mouse.set_axes(0,0)
        self.mouse.set_buttons()
        self.mouse.notify_hid_report()

        self.mouse.set_battery_level(100)
        self.mouse.notify_battery_level()

if __name__ == "__main__":
    d = Device()
    d.start()
