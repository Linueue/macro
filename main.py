from pynput import mouse, keyboard
import time
import win32api, win32con
import argparse
from enum import Enum
import pickle
import os.path
import ctypes

awareness = ctypes.c_int()
ctypes.windll.shcore.SetProcessDpiAwareness(2)

mouse_controller = mouse.Controller()
keyboard_controller = keyboard.Controller()

class Listener:
    mouse_listener: mouse.Listener | None = None
    keyboard_listener: keyboard.Listener | None = None

class RecordType(Enum):
    KEYBOARD = 0
    MOUSE = 1

class MouseState(Enum):
    POS = 0
    MOVE = 1
    CLICKED = 2
    SCROLLED = 3

class RecordData:
    is_recording = False
    start_hotkey = "q"
    stop_hotkey = "q"
    start_time = 0.0
    key_time = {}
    mouse_time = {}
    data = []
    prev_mouse_pos: tuple[int, int] | None = None

    @staticmethod
    def get_time() -> float:
        return time.time() - RecordData.start_time

    @staticmethod
    def add_data(data):
        data["time"] = RecordData.get_time()
        RecordData.data.append(data)

    @staticmethod
    def save(filename):
        with open(filename, "wb") as f:
            pickle.dump(RecordData.data, f)

    @staticmethod
    def load(filename):
        if not os.path.exists(filename):
            print(f"{filename} does not exist!")
            return False

        with open(filename, "rb") as f:
            RecordData.data = pickle.load(f)
        return True

def mouse_move(x, y):
    win32api.mouse_event(win32con.MOUSEEVENTF_MOVE, x, y, 0, 0)

def mouse_press(button):
    button_constant = None
    if button == mouse.Button.left:
        button_constant = win32con.MOUSEEVENTF_LEFTDOWN
    elif button == mouse.Button.middle:
        button_constant = win32con.MOUSEEVENTF_MIDDLEDOWN
    elif button == mouse.Button.right:
        button_constant = win32con.MOUSEEVENTF_RIGHTDOWN
    win32api.mouse_event(button_constant, 0, 0)

def mouse_release(button):
    button_constant = None
    if button == mouse.Button.left:
        button_constant = win32con.MOUSEEVENTF_LEFTUP
    elif button == mouse.Button.middle:
        button_constant = win32con.MOUSEEVENTF_MIDDLEUP
    elif button == mouse.Button.right:
        button_constant = win32con.MOUSEEVENTF_RIGHTUP
    win32api.mouse_event(button_constant, 0, 0)

def on_move(x, y):
    if not RecordData.is_recording:
        return
    dx, dy = (0, 0)
    if RecordData.prev_mouse_pos:
        dx = x - RecordData.prev_mouse_pos[0]
        dy = y - RecordData.prev_mouse_pos[1]
    RecordData.prev_mouse_pos = (x, y)
    RecordData.add_data({"type": RecordType.MOUSE, "state": MouseState.MOVE, "dx": dx, "dy": dy, "x": x, "y": y})

def on_click(x, y, button, pressed):
    if not RecordData.is_recording:
        return
    RecordData.add_data({"type": RecordType.MOUSE, "state": MouseState.CLICKED, "button": button, "pressed": pressed})

def on_scroll(x, y, dx, dy):
    if not RecordData.is_recording:
        return
    RecordData.add_data({"type": RecordType.MOUSE, "state": MouseState.SCROLLED, "dx": dx, "dy": dy})

def on_press(key):
    if not RecordData.is_recording:
        return
    RecordData.add_data({"type": RecordType.KEYBOARD, "key": key, "pressed": True})

def on_release(key):
    if hasattr(key, "char") and not RecordData.is_recording and key.char == RecordData.start_hotkey:
        RecordData.is_recording = True
        RecordData.start_time = time.time()
        RecordData.add_data({"type": RecordType.MOUSE, "state": MouseState.POS, "x": mouse_controller.position[0], "y": mouse_controller.position[1]})
        print("Recording started")
        return
    if hasattr(key, "char") and RecordData.is_recording and key.char == RecordData.stop_hotkey:
        RecordData.is_recording = False
        Listener.mouse_listener.stop()
        Listener.keyboard_listener.stop()
        print("Recording stopped")
        return False

    if not RecordData.is_recording:
        return
    RecordData.add_data({"type": RecordType.KEYBOARD, "key": key, "pressed": False})

def record(filename):
    print(f"Press {RecordData.start_hotkey} to record")

    Listener.mouse_listener = mouse.Listener(
            on_move=on_move,
            on_click=on_click,
            on_scroll=on_scroll)
    Listener.keyboard_listener = keyboard.Listener(
            on_press=on_press,
            on_release=on_release)
    Listener.mouse_listener.start()
    Listener.keyboard_listener.start()
    Listener.mouse_listener.join()
    Listener.keyboard_listener.join()

    RecordData.save(filename)
    print(f"Record data saved to {filename}")

def play(filename, loop):
    if not RecordData.load(filename):
        return

    print(f"{filename} loaded. Press {RecordData.start_hotkey} to play")

    def play_on_release(key):
        if hasattr(key, "char") and key.char == RecordData.start_hotkey:
            return False

    with keyboard.Listener(on_press=lambda k: None, on_release=play_on_release) as listener:
        listener.join()

    data = RecordData.data
    prev_pos = (0, 0)

    for i in range(loop):
        print(f"Playing loop {i}")
        start_time = time.time()
        for d in data:
            time_stamp = d["time"]
            record_type = d["type"]

            current_time = time.time() - start_time
            diff = max(time_stamp - current_time, 0)
            time.sleep(diff)

            if record_type == RecordType.MOUSE:
                mouse_state = d["state"]

                if mouse_state == MouseState.POS:
                    #diff_pos = (d["x"] - prev_pos[0], d["y"] - prev_pos[1])
                    #mouse_move(diff_pos[0], diff_pos[1])
                    mouse_controller.position = (d["x"], d["y"])
                    #prev_pos = (d["x"], d["y"])
                elif mouse_state == MouseState.MOVE:
                    mouse_move(d["dx"] * 5, d["dy"] * 5)
                    mouse_controller.position = (d["x"], d["y"])
                elif mouse_state == MouseState.CLICKED:
                    if d["pressed"]:
                        mouse_press(d["button"])
                    else:
                        mouse_release(d["button"])
                elif mouse_state == MouseState.SCROLLED:
                    mouse_controller.scroll(d["dx"], d["dy"])
            else:
                pressed = d["pressed"]
                
                if pressed:
                    keyboard_controller.press(d["key"])
                else:
                    keyboard_controller.release(d["key"])
    print(f"Finished playing {filename}")

def main():
    parser = argparse.ArgumentParser(
            prog="Macro",
            description="Records mouse, and keyboard")
    parser.add_argument("action", choices=["record", "play"])
    parser.add_argument("-f", "--filename", default="records/record1.rd")
    parser.add_argument("-l", "--loop", default=1)
    args = parser.parse_args()

    if args.action == "record":
        record(args.filename)
    if args.action == "play":
        play(args.filename, int(args.loop))

if __name__ == "__main__":
    main()
