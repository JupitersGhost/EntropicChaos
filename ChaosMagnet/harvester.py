# harvester.py
import threading
import time
import psutil
import random
import os
import numpy as np

# --- IMPORTS WITH SAFETY CHECKS ---
try:
    from pynput import mouse
    HAS_MOUSE = True
except ImportError:
    HAS_MOUSE = False

try:
    import cv2
    HAS_VIDEO = True
except ImportError:
    HAS_VIDEO = False

try:
    import sounddevice as sd
    HAS_AUDIO = True
except ImportError:
    HAS_AUDIO = False

class BaseHarvester(threading.Thread):
    def __init__(self, engine, name, rate):
        super().__init__(daemon=True)
        self.engine = engine
        self.name = name
        self.rate = rate
        self.active = False
        self.available = True
        self.stop_event = threading.Event()

    def run(self):
        while not self.stop_event.is_set():
            if self.active and self.available:
                try:
                    data = self.collect()
                    if data:
                        self.engine.inject_entropy(self.name, data)
                except Exception as e:
                    print(f"[!] {self.name} Error: {e}")
                    self.active = False
            time.sleep(self.rate)

    def collect(self):
        raise NotImplementedError

    def toggle(self, state):
        self.active = state

class SystemHarvester(BaseHarvester):
    def collect(self):
        cpu = psutil.cpu_times()
        mem = psutil.virtual_memory()
        disk = psutil.disk_io_counters()
        t = time.time_ns()
        raw = f"{cpu}{mem}{disk}{t}"
        return raw.encode()

class TRNGHarvester(BaseHarvester):
    """
    Harvests from Hardware/Kernel True Random Number Generators.
    Priority: /dev/hwrng (Raw Hardware) -> /dev/random (Kernel Entropy) -> os.urandom
    """
    def collect(self):
        try:
            # Try reading raw hardware RNG first (requires permissions)
            if os.path.exists("/dev/hwrng"):
                with open("/dev/hwrng", "rb") as f:
                    return f.read(32) # 256 bits
            
            # Fallback to Kernel Entropy Pool
            return os.urandom(32)
        except Exception:
            # Final fallback
            return os.urandom(32)

class AudioHarvester(BaseHarvester):
    def __init__(self, engine, name, rate):
        super().__init__(engine, name, rate)
        self.device_index = None
        if HAS_AUDIO:
            try:
                # Simply check if the audio subsystem is responsive.
                sd.query_devices()
                self.available = True
                print(f" [*] AUDIO: Using System Default (PipeWire/Pulse)")
            except:
                self.available = False
        else:
            self.available = False

    def collect(self):
        if not self.available: return None
        try:
            # STABILITY FIX: Reduced sample duration to 0.1s (was 0.2s)
            # This makes the UI feel snappier and prevents blocking.
            rec = sd.rec(int(0.1*44100), samplerate=44100, channels=1, device=None, dtype='float64')
            sd.wait()
            return rec.tobytes()
        except:
            return None

class VideoHarvester(BaseHarvester):
    def __init__(self, engine, name, rate):
        super().__init__(engine, name, rate)
        if not HAS_VIDEO:
            self.available = False
        self.cap = None

    def collect(self):
        if not self.available: return None
        if self.cap is None or not self.cap.isOpened():
            self.cap = cv2.VideoCapture(0)
            if not self.cap.isOpened():
                self.available = False
                return None
        ret, frame = self.cap.read()
        if ret:
            noise = frame.flatten()
            # STABILITY FIX: Downsample aggressively [::7] to save CPU
            return noise[::7].tobytes()
        return None

    def toggle(self, state):
        super().toggle(state)
        if not state and self.cap:
            self.cap.release()
            self.cap = None

class MouseHarvester:
    def __init__(self, engine):
        self.engine = engine
        self.available = HAS_MOUSE
        self.listener = None
        self.active = False
        # STABILITY FIX: Added counter for event throttling
        self.counter = 0

    def on_move(self, x, y):
        if self.active:
            # STABILITY FIX: Only process 1 out of every 10 events.
            # Without this, moving the mouse generates ~500 events/sec,
            # causing the "30-second crash" you saw.
            self.counter += 1
            if self.counter % 20 != 0:
                return

            t = time.time_ns()
            self.engine.inject_entropy("MOUSE_MOV", f"{x}{y}{t}".encode())

    def on_click(self, x, y, button, pressed):
        if self.active:
            t = time.time_ns()
            self.engine.inject_entropy("MOUSE_CLK", f"{x}{y}{button}{t}".encode())

    def toggle(self, state):
        self.active = state
        if state and not self.listener and self.available:
            self.listener = mouse.Listener(on_move=self.on_move, on_click=self.on_click)
            self.listener.start()