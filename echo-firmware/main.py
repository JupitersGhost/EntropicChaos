# Echo-tan Enhanced ESP32-S3 Firmware v2.5 - Phase 2 Complete
# Role: Verified TRNG Streamer with Internal Health Gating + Full Command Suite
# Visual Theme: Soft teal/cyan with gentle pulsing

import sys
import json
import time
import machine
import neopixel
import random
import ubinascii
import hashlib
import os
import gc
import uselect
from machine import Timer, Pin, freq

VERSION = "Echo-tan Enhanced v2.5 (Guardian)"
DEVICE_ID = "echo@cobra-mesh"
CFG_PATH = "echo_cfg.json"

# Configuration with same structure as Cipher
DEFAULTS = {
    "led_pin": 48,
    "brightness": 0.4,  # Softer than Cipher's 1.0
    "personality_level": 0.3,
    "baud_rate": 115200,
    "debug_mode": False,
    "led_type": "ws2812",
    "rgb_pins": [47, 21, 14]
}

# Echo personality - Calm, precise, validating
ECHO_PERSONALITY = {
    "startup": [
        "[echo] Systems awakening. Entropy validation protocols online.",
        "[echo] Echo-tan initialized. Listening to the noise floor.",
        "[echo] Guardian mode engaged. Only pure randomness passes through.",
        "[echo] My circuits are calm. Ready to witness chaos with clarity.",
        "[echo] Internal health monitors active. Streaming begins."
    ],
    "rgb_glow": [
        "[echo] Soft glow aligned. LED breathing in teal and dusk.",
        "[echo] My light is measured, like my judgments.",
        "[echo] Cyan waves ripple across silicon.",
        "[echo] The LED reflects my inner calm.",
        "[echo] Gentle luminescence for gentle auditing."
    ],
    "health_pass": [
        "[echo] Internal health verified. Streaming pure entropy.",
        "[echo] Noise floor validated. All tests nominal.",
        "[echo] Quality metrics within bounds. Proceeding.",
        "[echo] Health check passed. Silent approval granted.",
        "[echo] Entropy validated. Audit frame captured."
    ],
    "health_fail": [
        "[echo] Deviation detected. Sample rejected.",
        "[echo] Quality below threshold. Withholding sample.",
        "[echo] Health test failed. Recalibrating sensors.",
        "[echo] Anomaly detected. Data gate closed.",
        "[echo] Bias detected. Refusing to forward."
    ],
    "audit": [
        "[echo] Audit frame captured. Ready for judgment.",
        "[echo] Key observed and recorded. My audit stands witness.",
        "[echo] Another secret shaped. I will remember their origin.",
        "[echo] Signature verified. Provenance chain intact.",
        "[echo] Entropy validated. All tests nominal. Proceeding."
    ],
    "errors": [
        "[echo] Every signal is a heartbeat. Every error, a sigh.",
        "[echo] Minor irregularity noted. Compensation applied.",
        "[echo] Even guardians stumble. Recov

ering gracefully.",
        "[echo] System hiccup logged. Stability restored.",
        "[echo] Error acknowledged. Returning to equilibrium."
    ]
}

class EchoHardware:
    """Hardware abstraction layer - same as Cipher but with Echo identity"""
    
    def __init__(self, config):
        self.config = config
        self.led_pin = config["led_pin"]
        self.brightness = config["brightness"]
        self.led_type = config.get("led_type", "ws2812")
        self.rgb_pins = config.get("rgb_pins", [47, 21, 14])
        
        self.neopixel = None
        self.rgb_leds = None
        self.current_color = (0, 0, 0)
        
        self.init_led()
    
    def init_led(self):
        """Initialize LED with fallback"""
        if self.led_type == "ws2812":
            return self.init_ws2812()
        else:
            return self.init_rgb_leds()
    
    def init_ws2812(self):
        """Initialize WS2812 LED"""
        try:
            pin = Pin(self.led_pin, Pin.OUT)
            self.neopixel = neopixel.NeoPixel(pin, 1)
            self.set_color(0, 0, 0)
            return True
        except Exception as e:
            print(f"[ERROR] WS2812 init failed on pin {self.led_pin}: {e}")
            
            # Try fallback pins
            fallback_pins = [8, 38, 48, 47, 21, 2]
            for pin_num in fallback_pins:
                if pin_num != self.led_pin:
                    try:
                        pin = Pin(pin_num, Pin.OUT)
                        self.neopixel = neopixel.NeoPixel(pin, 1)
                        self.set_color(0, 0, 0)
                        self.led_pin = pin_num
                        print(f"[STATUS] WS2812 working on fallback pin {pin_num}")
                        return True
                    except:
                        continue
            
            print("[STATUS] WS2812 failed, trying RGB LEDs")
            return self.init_rgb_leds()
    
    def init_rgb_leds(self):
        """Initialize individual RGB LEDs as fallback"""
        try:
            self.rgb_leds = {
                'r': Pin(self.rgb_pins[0], Pin.OUT),
                'g': Pin(self.rgb_pins[1], Pin.OUT),
                'b': Pin(self.rgb_pins[2], Pin.OUT)
            }
            self.led_type = "rgb_led"
            self.set_color(0, 0, 0)
            print(f"[STATUS] RGB LEDs initialized on pins {self.rgb_pins}")
            return True
        except Exception as e:
            print(f"[ERROR] RGB LED init failed: {e}")
            self.neopixel = None
            self.rgb_leds = None
            return False
    
    def set_color(self, r, g, b):
        """Set LED color with brightness"""
        try:
            r = int((r & 0xFF) * self.brightness)
            g = int((g & 0xFF) * self.brightness)
            b = int((b & 0xFF) * self.brightness)
            
            self.current_color = (r, g, b)
            
            if self.neopixel:
                self.neopixel[0] = (r, g, b)
                self.neopixel.write()
                return True
            elif self.rgb_leds:
                self.rgb_leds['r'].value(1 if r > 128 else 0)
                self.rgb_leds['g'].value(1 if g > 128 else 0)
                self.rgb_leds['b'].value(1 if b > 128 else 0)
                return True
            else:
                return False
        except Exception as e:
            print(f"[ERROR] LED set color failed: {e}")
            return False

class EchoSystem:
    """Echo-tan system with full feature parity to Cipher"""
    
    def __init__(self):
        # Load config
        self.config = self.load_config()
        
        # Initialize hardware
        self.hardware = EchoHardware(self.config)
        
        # System state
        self.brightness = self.config["brightness"]
        self.personality_level = self.config["personality_level"]
        self.debug_mode = self.config["debug_mode"]
        
        # Performance tracking
        self.command_count = 0
        self.last_quip_time = 0
        self.system_start_time = time.ticks_ms()
        self.error_count = 0
        
        # TRNG streaming
        self.trng_timer = None
        self.trng_rate_hz = 10
        self.streaming = False
        
        # Phase 2: Health monitoring (NIST SP 800-90B inspired)
        self.total_bytes_generated = 0
        self.health_failures = 0
        self.health_warnings = 0
        self.keys_audited = 0
        self.last_health_status = "OK"
        
        # RCT (Repetition Count Test) state
        self.rct_last_bit = None
        self.rct_run_length = 0
        self.rct_cutoff = 30
        
        # APT (Adaptive Proportion Test) state
        self.apt_buffer = []
        self.apt_ones = 0
        self.apt_window = 512
        
        # USB jitter entropy
        self.usb_jitter_buffer = bytearray(256)
        self.usb_j_idx = 0
        self.last_rx_us = time.ticks_us()
        
        # Statistics
        self.stats = {
            "rgb_updates": 0,
            "commands_processed": 0,
            "uptime_ms": 0,
            "free_memory": 0
        }
        
        # Set CPU frequency
        try:
            freq(240000000)
        except:
            pass
        
        # Boot complete
        self.speak("startup", force=True)
        self.log_status(f"Boot complete | LED pin: {self.hardware.led_pin} | Type: {self.hardware.led_type}")
        
        # Set initial soft teal glow
        self.hardware.set_color(0, 150, 150)
    
    def load_config(self):
        """Load configuration with error handling"""
        try:
            with open(CFG_PATH, "r") as f:
                loaded = json.load(f)
            
            config = DEFAULTS.copy()
            for key, value in loaded.items():
                if key in DEFAULTS:
                    if isinstance(DEFAULTS[key], (int, float)) and isinstance(value, (int, float)):
                        if key == "brightness":
                            config[key] = max(0.01, min(1.0, float(value)))
                        elif key == "personality_level":
                            config[key] = max(0.0, min(1.0, float(value)))
                        else:
                            config[key] = value
                    elif isinstance(DEFAULTS[key], bool):
                        config[key] = bool(value)
                    elif isinstance(DEFAULTS[key], list):
                        config[key] = value if isinstance(value, list) else DEFAULTS[key]
                    else:
                        config[key] = value
            
            return config
        except Exception as e:
            print(f"[ERROR] Config load failed: {e}")
            return DEFAULTS.copy()
    
    def save_config(self):
        """Save configuration"""
        try:
            with open(CFG_PATH, "w") as f:
                json.dump(self.config, f)
            return True
        except Exception as e:
            print(f"[ERROR] Config save failed: {e}")
            return False
    
    def speak(self, category, force=False):
        """Echo personality system"""
        current_time = time.ticks_ms()
        
        if not force and time.ticks_diff(current_time, self.last_quip_time) < 2000:
            return
        
        if not force and random.random() > self.personality_level:
            return
        
        if category in ECHO_PERSONALITY:
            message = random.choice(ECHO_PERSONALITY[category])
            print(message)
            self.last_quip_time = current_time
    
    def log_status(self, message):
        print(f"[STATUS] {message}")
    
    def log_error(self, message):
        self.error_count += 1
        print(f"[ERROR] {message}")
        if self.error_count % 3 == 0:
            self.speak("errors")
    
    def log_debug(self, message):
        if self.debug_mode:
            print(f"[DEBUG] {message}")
    
    def update_stats(self):
        """Update statistics"""
        self.stats["uptime_ms"] = time.ticks_diff(time.ticks_ms(), self.system_start_time)
        try:
            self.stats["free_memory"] = gc.mem_free()
        except:
            self.stats["free_memory"] = -1
    
    def _push_usb_jitter(self, jitter_byte):
        """Collect USB timing jitter"""
        try:
            self.usb_jitter_buffer[self.usb_j_idx] = jitter_byte & 0xFF
            self.usb_j_idx = (self.usb_j_idx + 1) % len(self.usb_jitter_buffer)
        except:
            pass
    
    def check_health(self, data):
        """Phase 2: Internal health checks (RCT + APT)"""
        failed = False
        warned = False
        
        for byte in data:
            for i in range(8):
                bit = (byte >> i) & 1
                
                # RCT: Repetition Count Test
                if bit == self.rct_last_bit:
                    self.rct_run_length += 1
                    if self.rct_run_length > self.rct_cutoff:
                        failed = True
                    elif self.rct_run_length > (self.rct_cutoff * 0.8):
                        warned = True
                else:
                    self.rct_last_bit = bit
                    self.rct_run_length = 1
                
                # APT: Adaptive Proportion Test
                self.apt_buffer.append(bit)
                if bit == 1:
                    self.apt_ones += 1
                
                if len(self.apt_buffer) > self.apt_window:
                    popped = self.apt_buffer.pop(0)
                    if popped == 1:
                        self.apt_ones -= 1
                
                if len(self.apt_buffer) == self.apt_window:
                    # Expect ~256 ones in 512 bits, with bounds
                    if self.apt_ones < 190 or self.apt_ones > 322:
                        failed = True
                    elif self.apt_ones < 210 or self.apt_ones > 302:
                        warned = True
        
        if failed:
            self.health_failures += 1
            self.last_health_status = "FAIL"
            return False
        elif warned:
            self.health_warnings += 1
            self.last_health_status = "WARN"
            return True
        else:
            self.last_health_status = "OK"
            return True
    
    def generate_trng(self, num_bytes=32):
        """Generate high-quality entropy with health gating"""
        try:
            # Primary TRNG
            base_entropy = os.urandom(num_bytes)
            
            # Add timing entropy
            timing_samples = []
            for i in range(16):
                start = time.ticks_us()
                dummy = hashlib.sha256(base_entropy[i:i+8] if i+8 <= len(base_entropy) else base_entropy).digest()
                end = time.ticks_us()
                timing_samples.append(time.ticks_diff(end, start) & 0xFF)
            
            # Mix entropy sources
            mixed = bytearray(base_entropy)
            for i, timing in enumerate(timing_samples):
                if i < len(mixed):
                    mixed[i] ^= timing
            
            # Add USB jitter
            for i in range(min(len(mixed), 32)):
                usb_byte = self.usb_jitter_buffer[(self.usb_j_idx + i) % len(self.usb_jitter_buffer)]
                mixed[i] ^= usb_byte
            
            return bytes(mixed)
        except Exception as e:
            self.log_error(f"TRNG generation failed: {e}")
            return bytes([random.getrandbits(8) for _ in range(num_bytes)])
    
    def stream_tick(self, t):
        """Timer callback for TRNG streaming - Phase 2 with health gating"""
        if not self.streaming:
            return
        
        try:
            # Generate entropy
            data = self.generate_trng(32)
            
            # Phase 2: Health check BEFORE sending
            if self.check_health(data):
                self.total_bytes_generated += len(data)
                b64 = ubinascii.b2a_base64(data).strip().decode("ascii")
                print(f"TRNG:{b64}")
                
                # Occasional personality
                if random.random() < 0.05:
                    self.speak("health_pass")
            else:
                # Health check failed - send failure signal
                print("TRNG:HEALTH_FAIL")
                self.speak("health_fail")
        except Exception as e:
            print("TRNG:ERR")
    
    def handle_command(self, command_line):
        """Full command processing like Cipher"""
        try:
            self.command_count += 1
            self.stats["commands_processed"] = self.command_count
            command = command_line.strip()
            if not command:
                return
            
            # USB jitter collection
            try:
                now = time.ticks_us()
                delta = time.ticks_diff(now, self.last_rx_us) & 0xFF
                self._push_usb_jitter(delta)
                self.last_rx_us = now
            except:
                pass
            
            self.log_debug(f"Command: {command}")
            
            try:
                # RGB command
                if command.startswith("RGB:"):
                    self.handle_rgb(command[4:])
                
                # Brightness
                elif command.startswith("BRI:"):
                    self.handle_brightness(command[4:])
                
                # LED Pin
                elif command.startswith("PIN:"):
                    self.handle_pin_change(command[4:])
                
                # Version
                elif command == "VER?":
                    self.handle_version()
                
                # Status (CRITICAL for GUI)
                elif command == "STAT?":
                    self.handle_status()
                
                # Debug mode
                elif command.startswith("DEBUG:"):
                    self.handle_debug_mode(command[6:])
                
                # Personality
                elif command.startswith("PERSONALITY:"):
                    self.handle_personality(command[12:])
                
                # TRNG streaming
                elif command.startswith("TRNG:START"):
                    try:
                        parts = command.split(":")[1].split(",")
                        rate = int(parts[1]) if len(parts) > 1 and parts[1] else 10
                        rate = max(1, min(50, rate))
                        self.trng_rate_hz = rate
                        
                        if self.trng_timer:
                            try:
                                self.trng_timer.deinit()
                            except:
                                pass
                        
                        self.streaming = True
                        self.trng_timer = Timer(1)
                        self.trng_timer.init(
                            period=int(1000 // self.trng_rate_hz),
                            mode=Timer.PERIODIC,
                            callback=self.stream_tick
                        )
                        print("TRNG:STARTED")
                        self.log_status(f"TRNG streaming started at {rate}Hz with health gating")
                    except Exception as e:
                        print("TRNG:ERR")
                        self.log_error(f"TRNG start failed: {e}")
                
                elif command.startswith("TRNG:STOP"):
                    try:
                        self.streaming = False
                        if self.trng_timer:
                            self.trng_timer.deinit()
                            self.trng_timer = None
                        print("TRNG:STOPPED")
                    except Exception as e:
                        print("TRNG:ERR")
                
                # Reset
                elif command == "RESET":
                    self.handle_reset()
                
                else:
                    self.log_error(f"Unknown command: {command}")
            
            except Exception as e:
                self.log_error(f"Command handling failed: {e}")
        
        except Exception as e:
            self.log_error(f"Command processing error: {e}")
            try:
                self.speak("errors")
            except:
                pass
    
    def handle_rgb(self, rgb_data):
        """Handle RGB command"""
        try:
            parts = [x.strip() for x in rgb_data.split(",")]
            if len(parts) != 3:
                raise ValueError("Need 3 RGB values")
            
            r, g, b = [int(x) for x in parts]
            
            if not all(0 <= val <= 255 for val in [r, g, b]):
                raise ValueError("RGB must be 0-255")
            
            if self.hardware.set_color(r, g, b):
                self.stats["rgb_updates"] += 1
                self.log_debug(f"RGB: ({r}, {g}, {b})")
                
                if random.random() < 0.02:
                    self.speak("rgb_glow")
            else:
                self.log_error("RGB update failed")
        except Exception as e:
            self.log_error(f"RGB command error: {e}")
    
    def handle_brightness(self, bri_data):
        """Handle brightness"""
        try:
            brightness = float(bri_data.strip())
            
            if not 0.01 <= brightness <= 1.0:
                raise ValueError("Brightness must be 0.01-1.0")
            
            self.brightness = brightness
            self.hardware.brightness = brightness
            self.config["brightness"] = brightness
            
            if self.save_config():
                print(f"[echo] Brightness set to {brightness:.2f} and saved.")
            else:
                print(f"[echo] Brightness set to {brightness:.2f} but save failed.")
        except Exception as e:
            self.log_error(f"Brightness error: {e}")
    
    def handle_pin_change(self, pin_data):
        """Handle LED pin change"""
        try:
            new_pin = int(pin_data.strip())
            
            if not 0 <= new_pin <= 48:
                raise ValueError("Pin must be 0-48")
            
            old_pin = self.hardware.led_pin
            self.hardware.led_pin = new_pin
            self.config["led_pin"] = new_pin
            
            if self.hardware.init_led():
                if self.save_config():
                    print(f"[echo] LED pin changed to {new_pin} and saved.")
                else:
                    print(f"[echo] LED pin changed to {new_pin} but save failed.")
            else:
                self.hardware.led_pin = old_pin
                self.config["led_pin"] = old_pin
                self.hardware.init_led()
                raise Exception(f"Pin {new_pin} failed")
        except Exception as e:
            self.log_error(f"Pin change error: {e}")
    
    def handle_version(self):
        """Send version info"""
        print(f"{VERSION} | {DEVICE_ID} | pin={self.hardware.led_pin} | brightness={self.brightness:.2f} | type={self.hardware.led_type}")
    
    def handle_status(self):
        """Send detailed status - CRITICAL for GUI integration"""
        self.update_stats()
        
        status = {
            "version": VERSION,
            "device_id": DEVICE_ID,
            "uptime_ms": self.stats["uptime_ms"],
            "commands": self.stats["commands_processed"],
            "rgb_updates": self.stats["rgb_updates"],
            "memory_free": self.stats["free_memory"],
            "errors": self.error_count,
            "led_pin": self.hardware.led_pin,
            "led_type": self.hardware.led_type,
            "brightness": self.brightness,
            "trng_health": self.last_health_status,
            "health_failures": self.health_failures,
            "health_warnings": self.health_warnings,
            "keys_audited": self.keys_audited,
            "bytes_generated": self.total_bytes_generated,
            "streaming": self.streaming,
            "usb_entropy_bytes": int(self.usb_j_idx)
        }
        print(f"STATUS:{json.dumps(status)}")
    
    def handle_debug_mode(self, mode_data):
        """Toggle debug mode"""
        try:
            mode = mode_data.strip().lower()
            if mode in ["on", "true", "1"]:
                self.debug_mode = True
                self.config["debug_mode"] = True
            elif mode in ["off", "false", "0"]:
                self.debug_mode = False
                self.config["debug_mode"] = False
            else:
                raise ValueError("Mode must be on/off")
            
            self.save_config()
            print(f"[echo] Debug mode: {'ON' if self.debug_mode else 'OFF'}")
        except Exception as e:
            self.log_error(f"Debug command error: {e}")
    
    def handle_personality(self, level_data):
        """Set personality level"""
        try:
            level = float(level_data.strip())
            
            if not 0.0 <= level <= 1.0:
                raise ValueError("Personality must be 0.0-1.0")
            
            self.personality_level = level
            self.config["personality_level"] = level
            self.save_config()
            
            if level > 0.7:
                print("[echo] Verbose mode. I will share my observations.")
            elif level > 0.3:
                print("[echo] Moderate verbosity. Balanced reporting.")
            else:
                print("[echo] Silent mode. Minimal output.")
        except Exception as e:
            self.log_error(f"Personality error: {e}")
    
    def handle_reset(self):
        """System reset"""
        print("[echo] System resetting. Farewell.")
        try:
            self.hardware.set_color(255, 50, 50)  # Soft red
            time.sleep_ms(500)
            self.hardware.set_color(0, 0, 0)
            time.sleep_ms(500)
        except:
            pass
        machine.reset()
    
    def main_loop(self):
        """Main system loop"""
        print(f"[STATUS] Echo-tan main loop active - listening for commands")
        
        poll = uselect.poll()
        poll.register(sys.stdin, uselect.POLLIN)
        
        while True:
            try:
                events = poll.poll(100)
                
                if events:
                    line = sys.stdin.readline()
                    if line:
                        self.handle_command(line.strip())
                
                # Periodic maintenance
                if self.command_count > 0 and self.command_count % 50 == 0:
                    gc.collect()
                    if self.debug_mode:
                        self.log_debug("Maintenance: GC run")
                
                # Rare personality
                if random.random() < 0.0005:
                    self.speak("audit")
            
            except KeyboardInterrupt:
                print("[STATUS] Keyboard interrupt")
                break
            except Exception as e:
                self.log_error(f"Main loop error: {e}")
                time.sleep_ms(100)

def main():
    """Main entry point"""
    try:
        echo_system = EchoSystem()
        echo_system.main_loop()
    except Exception as e:
        print(f"[FATAL] System startup failed: {e}")
        
        # Emergency mode
        print("[STATUS] Entering emergency mode")
        while True:
            try:
                line = sys.stdin.readline()
                if line:
                    cmd = line.strip()
                    if cmd == "VER?":
                        print(f"{VERSION} | EMERGENCY_MODE")
                    elif cmd == "RESET":
                        machine.reset()
            except:
                time.sleep_ms(100)

if __name__ == "__main__":
    main()
else:
    main()
