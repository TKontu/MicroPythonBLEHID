# Implements a BLE HID keyboard with 5 buttons and 3 encoders
import uasyncio as asyncio
from machine import Pin
from hid_services import Keyboard

class Device:
    def __init__(self, name="Keyboard"):
        # Define state
        self.keys = [0x00] * 6  # 6-key rollover
        self.modifiers = 0  # 8-bit modifiers (Ctrl, Alt, Shift)
        self.encoders = [0, 0, 0]  # Encoder positions
        self.updated = False
        self.active = True

        # Define buttons
        self.buttons = [
            Pin(5, Pin.IN, Pin.PULL_UP),  # Button 1
            Pin(6, Pin.IN, Pin.PULL_UP),  # Button 2
            Pin(7, Pin.IN, Pin.PULL_UP),  # Button 3
            Pin(8, Pin.IN, Pin.PULL_UP),  # Button 4
            Pin(9, Pin.IN, Pin.PULL_UP),  # Button 5
        ]

        # Define encoders (A and B pins for 3 encoders)
        self.encoders_pins = [
            (Pin(10, Pin.IN, Pin.PULL_UP), Pin(11, Pin.IN, Pin.PULL_UP)),  # Encoder 1
            (Pin(12, Pin.IN, Pin.PULL_UP), Pin(13, Pin.IN, Pin.PULL_UP)),  # Encoder 2
            (Pin(14, Pin.IN, Pin.PULL_UP), Pin(15, Pin.IN, Pin.PULL_UP)),  # Encoder 3
        ]

        # Create our device
        self.keyboard = Keyboard(name)
        self.keyboard.set_state_change_callback(self.keyboard_state_callback)

    # Function to handle device state changes
    def keyboard_state_callback(self):
        if self.keyboard.get_state() is Keyboard.DEVICE_IDLE:
            print("Device is idle.")
        elif self.keyboard.get_state() is Keyboard.DEVICE_ADVERTISING:
            print("Device is advertising.")
        elif self.keyboard.get_state() is Keyboard.DEVICE_CONNECTED:
            print("Device is connected.")

    def advertise(self):
        self.keyboard.start_advertising()

    def stop_advertise(self):
        self.keyboard.stop_advertising()

    async def advertise_for(self, seconds=30):
        self.advertise()

        while seconds > 0 and self.keyboard.get_state() is Keyboard.DEVICE_ADVERTISING:
            await asyncio.sleep(1)
            seconds -= 1

        if self.keyboard.get_state() is Keyboard.DEVICE_ADVERTISING:
            self.stop_advertise()

    # Input loop to poll buttons and encoders
    async def gather_input(self):
        last_encoder_states = [0] * len(self.encoders_pins)
        while self.active:
            # Check buttons
            for i, button in enumerate(self.buttons):
                if not button.value():  # Button pressed
                    self.keys[i] = 0x04 + i  # Assign key codes (starting from 'a')
                else:
                    self.keys[i] = 0x00  # No key

            # Check encoders
            for i, (a_pin, b_pin) in enumerate(self.encoders_pins):
                state = (a_pin.value() << 1) | b_pin.value()
                if state != last_encoder_states[i]:
                    if state == 0b01:
                        self.encoders[i] += 1  # Increment
                    elif state == 0b10:
                        self.encoders[i] -= 1  # Decrement
                    last_encoder_states[i] = state

            self.updated = True
            await asyncio.sleep_ms(50)

    # Bluetooth device loop
    async def notify(self):
        while self.active:
            # Notify changes if updated
            if self.updated:
                if self.keyboard.get_state() is Keyboard.DEVICE_CONNECTED:
                    # Notify button states
                    self.keyboard.set_keys(*self.keys[:6])
                    self.keyboard.notify_hid_report()

                    # Notify encoder values (can send as additional reports)
                    print(f"Encoder states: {self.encoders}")

                elif self.keyboard.get_state() is Keyboard.DEVICE_IDLE:
                    await self.advertise_for(30)

                self.updated = False

            await asyncio.sleep_ms(50)

    async def co_start(self):
        # Start the device
        if self.keyboard.get_state() is Keyboard.DEVICE_STOPPED:
            self.keyboard.start()
            self.active = True
            await asyncio.gather(self.advertise_for(30), self.gather_input(), self.notify())

    async def co_stop(self):
        self.active = False
        self.keyboard.stop()

    def start(self):
        asyncio.run(self.co_start())

    def stop(self):
        asyncio.run(self.co_stop())

if __name__ == "__main__":
    device = Device(name="Pico Keyboard")
    device.start()
