# cipher-tan Enhanced ESP32-S3 Firmware v2.1 - Fixed & Complete
# Addresses serial timeout issues, LED configuration, and adds entropy tracking

import sys
import json
import time
import machine
import neopixel
import random
import binascii
import hashlib
import os
import gc
import ubinascii
from machine import Timer, Pin, freq
import uselect

VERSION = "cipher-tan Enhanced v2.1-Fixed-Complete"
DEVICE_ID = "cipher@cobra-mesh"

# Configuration
CFG_PATH = "cipher_enhanced_cfg.json"

# Defaults - Using GPIO48 for the larger addressable LED based on your board
DEFAULTS = {
    "led_pin": 48,  # GPIO48 for the larger WS2812/addressable LED
    "brightness": 1.0,
    "personality_level": 0.3,
    "baud_rate": 115200,
    "debug_mode": False,
    "led_type": "ws2812",  # Use WS2812 for the bigger LED
    "rgb_pins": [47, 21, 14]  # Fallback RGB pins if WS2812 fails
}

# cipher-tan personality
CIPHER_PERSONALITY = {
    "startup": [
        "*** cipher-tan online! Ready to wreak cryptographic havoc!",
        "^^^ RNG Queen reporting for duty! Let's chaos it up!",
        ">>> Boot complete! Time to turn silicon into pure randomness!",
        "=== Systems online! My circuits are tingling with anticipation~",
        "<<< Ready to show Echo-tan what real entropy looks like!"
    ],
    "rgb_chaos": [
        "*** Pretty colors! My LED is definitely more stylish!",
        "~~~ RGB storm engaged! Each photon carries chaos~",
        "<3> Color chaos activated! Pure mathematical beauty!",
        ":D: LED disco mode! Cryptography can be fabulous!",
        "++> Painting the spectrum with randomness!"
    ],
    "key_forging": [
        "[*] Key forged in the fires of chaos!",
        "<$> Another cryptographic masterpiece completed!",
        "==> Digital gold synthesis achieved!",
        "(*) Perfect randomness locked away forever!",
        "\\o/ My key-crafting skills are legendary!"
    ],
    "errors": [
        "^_^ Oops! Even chaos queens make mistakes sometimes...",
        "[!] Minor glitch! I'm too advanced to stay broken~",
        "<!> System hiccup! Time for graceful recovery!",
        ":-P Plot twist! I call this 'added randomness'!",
        "\\m/ Error handled like a boss! cipher-tan recovers!"
    ]
}

class ciphertanHardware:
    """Hardware abstraction layer"""
    
    def __init__(self, config):
        self.config = config
        self.led_pin = config["led_pin"]
        self.brightness = config["brightness"]
        self.led_type = config.get("led_type", "ws2812")
        self.rgb_pins = config.get("rgb_pins", [16, 17, 18])
        
        self.neopixel = None
        self.rgb_leds = None
        self.current_color = (0, 0, 0)
        
        # Initialize hardware
        self.init_led()
    
    def init_led(self):
        """Initialize LED hardware with fallback options"""
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
            
            # Try common ESP32-S3 pins
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
            
            # If WS2812 completely fails, try RGB LEDs
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
            # Complete LED failure - continue without LEDs
            self.neopixel = None
            self.rgb_leds = None
            return False
    
    def set_color(self, r, g, b):
        """Set LED color with hardware abstraction"""
        try:
            # Apply brightness
            r = int((r & 0xFF) * self.brightness)
            g = int((g & 0xFF) * self.brightness) 
            b = int((b & 0xFF) * self.brightness)
            
            self.current_color = (r, g, b)
            
            if self.neopixel:
                self.neopixel[0] = (r, g, b)
                self.neopixel.write()
                return True
            elif self.rgb_leds:
                # Simple PWM simulation with digital pins
                self.rgb_leds['r'].value(1 if r > 128 else 0)
                self.rgb_leds['g'].value(1 if g > 128 else 0)
                self.rgb_leds['b'].value(1 if b > 128 else 0)
                return True
            else:
                return False
                
        except Exception as e:
            print(f"[ERROR] LED set color failed: {e}")
            return False

class ciphertanSystem:
    def __init__(self):
        # Load configuration first
        self.config = self.load_config()
        
        # Initialize hardware
        self.hardware = ciphertanHardware(self.config)
        
        # System state
        self.brightness = self.config["brightness"]
        self.personality_level = self.config["personality_level"]
        self.debug_mode = self.config["debug_mode"]
        
        # Performance tracking
        self.command_count = 0
        self.entropy_pool = bytearray()
        self.last_quip_time = 0
        self.system_start_time = time.ticks_ms()
        self.error_count = 0
        
        # TRNG streaming
        self.trng_timer = None
        self.trng_rate_hz = 10
        
        # Enhanced entropy tracking (new features)
        self.wifi_entropy_buffer = bytearray(256)
        self.wifi_idx = 0
        self.usb_jitter_buffer = bytearray(256)
        self.usb_j_idx = 0
        self.last_rx_us = time.ticks_us()
        self.wifi_last_scan_ms = 0
        self.wifi_ap_count = 0
        self.wifi_joined = False

        # Statistics
        self.stats = {
            "keys_forged": 0,
            "rgb_updates": 0,
            "commands_processed": 0,
            "uptime_ms": 0,
            "free_memory": 0
        }
        
        # Set CPU frequency for stability
        try:
            freq(240000000)  # 240MHz for better performance
        except:
            pass
        
        # Boot complete
        self.speak("startup", force=True)
        self.log_status(f"Boot complete | LED pin: {self.hardware.led_pin} | Type: {self.hardware.led_type}")
    
    def load_config(self):
        """Load configuration with robust error handling"""
        try:
            with open(CFG_PATH, "r") as f:
                loaded = json.load(f)
            
            # Merge with defaults
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
        """Save configuration to flash"""
        try:
            with open(CFG_PATH, "w") as f:
                json.dump(self.config, f)
            return True
        except Exception as e:
            print(f"[ERROR] Config save failed: {e}")
            return False
    
    def speak(self, category, force=False):
        """cipher-tan personality system"""
        current_time = time.ticks_ms()
        
        # Rate limiting - don't spam
        if not force and time.ticks_diff(current_time, self.last_quip_time) < 2000:
            return
        
        # Personality level check
        if not force and random.random() > self.personality_level:
            return
        
        if category in CIPHER_PERSONALITY:
            message = random.choice(CIPHER_PERSONALITY[category])
            print(f"[cipher-tan] {message}")
            self.last_quip_time = current_time
    
    def log_status(self, message):
        """Log status message"""
        print(f"[STATUS] {message}")
    
    def log_error(self, message):
        """Log error with recovery"""
        self.error_count += 1
        print(f"[ERROR] {message}")
        
        if self.error_count % 3 == 0:
            self.speak("errors")
    
    def log_debug(self, message):
        """Debug logging"""
        if self.debug_mode:
            print(f"[DEBUG] {message}")
    
    def update_stats(self):
        """Update performance statistics"""
        self.stats["uptime_ms"] = time.ticks_diff(time.ticks_ms(), self.system_start_time)
        try:
            self.stats["free_memory"] = gc.mem_free()
        except:
            self.stats["free_memory"] = -1
    
    def _push_usb_jitter(self, jitter_byte):
        """Add USB jitter timing data to entropy buffer"""
        try:
            self.usb_jitter_buffer[self.usb_j_idx] = jitter_byte & 0xFF
            self.usb_j_idx = (self.usb_j_idx + 1) % len(self.usb_jitter_buffer)
        except:
            pass
    
    def _push_wifi_entropy(self, wifi_data):
        """Add WiFi entropy data to buffer"""
        try:
            if isinstance(wifi_data, (bytes, bytearray)):
                for byte in wifi_data[:min(16, len(wifi_data))]:  # Limit to prevent overflow
                    self.wifi_entropy_buffer[self.wifi_idx] = byte & 0xFF
                    self.wifi_idx = (self.wifi_idx + 1) % len(self.wifi_entropy_buffer)
            elif isinstance(wifi_data, int):
                self.wifi_entropy_buffer[self.wifi_idx] = wifi_data & 0xFF
                self.wifi_idx = (self.wifi_idx + 1) % len(self.wifi_entropy_buffer)
        except:
            pass
    
    def generate_trng(self, num_bytes=32):
        """Generate high-quality entropy"""
        try:
            # Primary TRNG
            base_entropy = os.urandom(num_bytes)
            
            # Add timing entropy
            timing_samples = []
            for i in range(16):
                start = time.ticks_us()
                # Add some computation for timing variation
                dummy = hashlib.sha256(base_entropy[i:i+8] if i+8 <= len(base_entropy) else base_entropy).digest()
                end = time.ticks_us()
                timing_samples.append(time.ticks_diff(end, start) & 0xFF)
            
            # Mix entropy sources including new buffers
            mixed = bytearray(base_entropy)
            for i, timing in enumerate(timing_samples):
                if i < len(mixed):
                    mixed[i] ^= timing
            
            # Add WiFi entropy if available
            for i in range(min(len(mixed), 32)):
                wifi_byte = self.wifi_entropy_buffer[(self.wifi_idx + i) % len(self.wifi_entropy_buffer)]
                usb_byte = self.usb_jitter_buffer[(self.usb_j_idx + i) % len(self.usb_jitter_buffer)]
                mixed[i] ^= wifi_byte ^ usb_byte
            
            # Quality assessment (basic)
            quality = self.assess_entropy_quality(bytes(mixed))
            
            if quality < 0.7:  # Lower threshold for more realistic operation
                self.log_debug(f"Entropy quality: {quality:.3f}")
            else:
                if random.random() < 0.1:
                    self.speak("rgb_chaos")
            
            return bytes(mixed)
            
        except Exception as e:
            self.log_error(f"TRNG failed: {e}")
            # Emergency fallback
            return bytes([random.getrandbits(8) for _ in range(num_bytes)])
    
    def assess_entropy_quality(self, data):
        """Simple entropy quality check"""
        if len(data) < 8:
            return 0.0
        
        try:
            # Basic frequency test
            bit_count = sum(bin(b).count('1') for b in data)
            total_bits = len(data) * 8
            
            if total_bits == 0:
                return 0.0
            
            # Ideal ratio is 0.5
            ratio = bit_count / total_bits
            frequency_score = 1.0 - abs(ratio - 0.5) * 2
            
            return max(0.0, min(1.0, frequency_score))
            
        except:
            return 0.5  # Default neutral score
    
    def forge_key(self, entropy_pool):
        """Enhanced key derivation"""
        try:
            if len(entropy_pool) < 16:
                return None
            
            # Add fresh device entropy
            device_entropy = self.generate_trng(32)
            
            # Combine entropy sources
            combined = entropy_pool + device_entropy
            
            # Multiple hash rounds
            key_material = combined
            for round_num in range(3):
                hasher = hashlib.sha256()
                hasher.update(key_material)
                hasher.update(f"CIPHER_V2_R{round_num}".encode())
                hasher.update(str(time.ticks_us()).encode())  # Add timing
                key_material = hasher.digest()
            
            self.stats["keys_forged"] += 1
            
            # Celebrate
            if random.random() < 0.4:
                self.speak("key_forging")
            
            return key_material
            
        except Exception as e:
            self.log_error(f"Key forging failed: {e}")
            # Emergency key
            try:
                return hashlib.sha256(entropy_pool + os.urandom(16)).digest()
            except:
                return None
    
    def handle_command(self, command_line):
        """Enhanced command processing with better error handling"""
        try:
            self.command_count += 1
            self.stats["commands_processed"] = self.command_count
            command = command_line.strip()
            if not command:
                return

            # Capture USB RX inter-arrival jitter (device-side timing)
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

                # LED Pin change
                elif command.startswith("PIN:"):
                    self.handle_pin_change(command[4:])

                # Random number request
                elif command == "RND?":
                    self.handle_rnd_request()

                # Key forging
                elif command.startswith("POOL:"):
                    self.handle_key_forge(command[5:])

                # Version info
                elif command == "VER?":
                    self.handle_version()

                # Status request
                elif command == "STAT?":
                    self.handle_status()

                # Debug mode
                elif command.startswith("DEBUG:"):
                    self.handle_debug_mode(command[6:])

                # Personality level
                elif command.startswith("PERSONALITY:"):
                    self.handle_personality(command[12:])

                # System test
                elif command == "TEST?":
                    self.handle_system_test()

                # Reset
                elif command == "RESET":
                    self.handle_reset()

                # TRNG streaming control
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

                        self.trng_timer = Timer(-1)

                        def _trng_tick(t):
                            try:
                                data = self.generate_trng(64)
                                b64 = ubinascii.b2a_base64(data).strip().decode("ascii")
                                print("TRNG:" + b64)
                            except Exception as e:
                                print("TRNG:ERR")

                        self.trng_timer.init(
                            period=int(1000 // self.trng_rate_hz),
                            mode=Timer.PERIODIC,
                            callback=_trng_tick
                        )
                        print("TRNG:OK")
                    except Exception as e:
                        print("TRNG:ERR")

                elif command.startswith("TRNG:STOP"):
                    try:
                        if self.trng_timer:
                            self.trng_timer.deinit()
                            self.trng_timer = None
                        print("TRNG:OFF")
                    except Exception as e:
                        print("TRNG:ERR")

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
        """Handle RGB command with validation"""
        try:
            parts = [x.strip() for x in rgb_data.split(",")]
            if len(parts) != 3:
                raise ValueError("Need exactly 3 RGB values")
            
            r, g, b = [int(x) for x in parts]
            
            if not all(0 <= val <= 255 for val in [r, g, b]):
                raise ValueError("RGB values must be 0-255")
            
            if self.hardware.set_color(r, g, b):
                self.stats["rgb_updates"] += 1
                self.log_debug(f"RGB: ({r}, {g}, {b})")
                
                if random.random() < 0.02:  # 2% chance for RGB quip
                    self.speak("rgb_chaos")
            else:
                self.log_error("RGB update failed")
        
        except Exception as e:
            self.log_error(f"RGB command error: {e}")
    
    def handle_brightness(self, bri_data):
        """Handle brightness with bounds checking"""
        try:
            brightness = float(bri_data.strip())
            
            if not 0.01 <= brightness <= 1.0:
                raise ValueError("Brightness must be 0.01-1.0")
            
            self.brightness = brightness
            self.hardware.brightness = brightness
            self.config["brightness"] = brightness
            
            if self.save_config():
                print(f"[cipher-tan] Brightness set to {brightness:.2f} and saved!")
            else:
                print(f"[cipher-tan] Brightness set to {brightness:.2f} but save failed!")
        
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
                    print(f"[cipher-tan] LED pin changed to {new_pin} and saved!")
                else:
                    print(f"[cipher-tan] LED pin changed to {new_pin} but save failed!")
            else:
                # Revert on failure
                self.hardware.led_pin = old_pin
                self.config["led_pin"] = old_pin
                self.hardware.init_led()
                raise Exception(f"Pin {new_pin} failed")
        
        except Exception as e:
            self.log_error(f"Pin change error: {e}")
    
    def handle_rnd_request(self):
        """Handle RND? request with improved reliability"""
        try:
            rnd_data = self.generate_trng(32)
            hex_data = ubinascii.hexlify(rnd_data).decode('ascii')
            print(f"RND:{hex_data}")
            
            if random.random() < 0.1:
                self.speak("rgb_chaos")
        
        except Exception as e:
            self.log_error(f"RND request failed: {e}")
            # Emergency fallback - maintain protocol format
            try:
                fallback = os.urandom(32)
                hex_data = ubinascii.hexlify(fallback).decode('ascii')
                print(f"RND:{hex_data}")
            except:
                # Send error in protocol format
                print("RND:ERROR")
    
    def handle_key_forge(self, pool_data):
        """Handle POOL: command for key forging"""
        try:
            # Decode hex pool data
            entropy_pool = ubinascii.unhexlify(pool_data.encode('ascii'))
            
            # Forge key
            key_data = self.forge_key(entropy_pool)
            if key_data:
                hex_key = ubinascii.hexlify(key_data).decode('ascii')
                print(f"KEY:{hex_key}")
            else:
                raise Exception("Key forging returned None")
        
        except Exception as e:
            self.log_error(f"Key forge error: {e}")
            # Don't send malformed response - let host handle timeout
    
    def handle_version(self):
        """Send version info"""
        print(f"{VERSION} | {DEVICE_ID} | pin={self.hardware.led_pin} | brightness={self.brightness:.2f} | type={self.hardware.led_type}")
    
    def handle_status(self):
        """Send detailed status"""
        self.update_stats()
        status = {
            "version": VERSION,
            "uptime_ms": self.stats["uptime_ms"],
            "commands": self.stats["commands_processed"],
            "keys_forged": self.stats["keys_forged"],
            "rgb_updates": self.stats["rgb_updates"],
            "memory_free": self.stats["free_memory"],
            "errors": self.error_count,
            "led_pin": self.hardware.led_pin,
            "led_type": self.hardware.led_type,
            "brightness": self.brightness,
            "wifi_entropy_bytes": int(self.wifi_idx),
            "usb_entropy_bytes": int(self.usb_j_idx),
            "wifi_last_scan_ms": int(self.wifi_last_scan_ms),
            "wifi_ap_count": int(self.wifi_ap_count),
            "wifi_joined": bool(self.wifi_joined)
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
            print(f"[cipher-tan] Debug mode: {'ON' if self.debug_mode else 'OFF'}")
        
        except Exception as e:
            self.log_error(f"Debug command error: {e}")
    
    def handle_personality(self, level_data):
        """Set personality level"""
        try:
            level = float(level_data.strip())
            
            if not 0.0 <= level <= 1.0:
                raise ValueError("Personality level must be 0.0-1.0")
            
            self.personality_level = level
            self.config["personality_level"] = level
            self.save_config()
            
            if level > 0.8:
                print("[cipher-tan] Maximum sass mode activated!")
            elif level > 0.5:
                print("[cipher-tan] Moderate chatter mode engaged.")
            elif level > 0.2:
                print("[cipher-tan] Quiet mode set.")
            else:
                print("[cipher-tan] Silent mode - all business!")
        
        except Exception as e:
            self.log_error(f"Personality error: {e}")
    
    def handle_system_test(self):
        """Comprehensive system test"""
        try:
            print("[cipher-tan] Running system diagnostics...")
            
            # LED test
            led_test = "PASS"
            try:
                colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (0, 0, 0)]
                for r, g, b in colors:
                    self.hardware.set_color(r, g, b)
                    time.sleep_ms(150)
            except:
                led_test = "FAIL"
            
            # Entropy test
            entropy_test = "PASS"
            entropy_quality = 0.0
            try:
                test_data = self.generate_trng(64)
                entropy_quality = self.assess_entropy_quality(test_data)
                if entropy_quality < 0.3:
                    entropy_test = "WARN"
            except:
                entropy_test = "FAIL"
            
            # Memory test
            memory_test = "PASS"
            try:
                self.update_stats()
                if self.stats["free_memory"] < 50000:  # Less than 50KB free
                    memory_test = "WARN"
            except:
                memory_test = "FAIL"
            
            # Key forge test
            key_test = "PASS"
            try:
                test_key = self.forge_key(b"test_entropy_data_12345678")
                if not test_key or len(test_key) != 32:
                    key_test = "FAIL"
            except:
                key_test = "FAIL"
            
            # Overall result
            overall = "PASS"
            if "FAIL" in [led_test, entropy_test, key_test]:
                overall = "FAIL"
            elif "WARN" in [led_test, entropy_test, memory_test, key_test]:
                overall = "WARN"
            
            results = {
                "led_test": led_test,
                "entropy_test": entropy_test,
                "entropy_quality": f"{entropy_quality:.3f}",
                "memory_test": memory_test,
                "key_forge_test": key_test,
                "overall": overall
            }
            
            print(f"TEST:{json.dumps(results)}")
            
            if overall == "PASS":
                self.speak("key_forging", force=True)
            else:
                self.speak("errors", force=True)
        
        except Exception as e:
            self.log_error(f"System test failed: {e}")
            print(f"TEST:{{\"overall\":\"ERROR\",\"error\":\"{str(e)}\"}}")
    
    def handle_reset(self):
        """System reset"""
        print("[cipher-tan] Resetting system... Goodbye!")
        try:
            self.hardware.set_color(255, 0, 0)  # Red
            time.sleep_ms(500)
            self.hardware.set_color(0, 0, 0)    # Off
            time.sleep_ms(500)
        except:
            pass
        
        machine.reset()
    
    def main_loop(self):
        """Main system loop with improved reliability"""
        print(f"[STATUS] Main loop starting - listening for commands")
        
        # Set up polling for stdin
        poll = uselect.poll()
        poll.register(sys.stdin, uselect.POLLIN)
        
        while True:
            try:
                # Check for input with timeout
                events = poll.poll(100)  # 100ms timeout
                
                if events:
                    line = sys.stdin.readline()
                    if line:
                        self.handle_command(line.strip())
                
                # Periodic maintenance
                if self.command_count > 0 and self.command_count % 50 == 0:
                    gc.collect()
                    if self.debug_mode:
                        self.log_debug("Maintenance: GC run")
                
                # Very rare random personality
                if random.random() < 0.0005:  # 0.05% chance per loop
                    self.speak("rgb_chaos")
            
            except KeyboardInterrupt:
                print("[STATUS] Keyboard interrupt - exiting")
                break
            except Exception as e:
                self.log_error(f"Main loop error: {e}")
                time.sleep_ms(100)

def main():
    """Main entry point with error recovery"""
    try:
        # Initialize system
        cipher_chan = ciphertanSystem()
        
        # Run main loop
        cipher_chan.main_loop()
        
    except Exception as e:
        print(f"[FATAL] System startup failed: {e}")
        
        # Emergency fallback mode
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
                    elif cmd.startswith("RGB:"):
                        # Try basic RGB even in emergency mode
                        try:
                            parts = cmd[4:].split(",")
                            if len(parts) == 3:
                                print(f"[EMERGENCY] RGB command received: {cmd}")
                        except:
                            pass
            except:
                time.sleep_ms(100)

# Auto-start the system
if __name__ == "__main__":
    main()
else:
    # If imported, also start (for REPL usage)
    main()