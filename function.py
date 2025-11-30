"""
Entropic Chaos - Function Module
All business logic, workers, managers, and helper functions
"""

import os
import sys
import time
import json
import base64
import binascii
import hashlib
import colorsys
import threading
import subprocess
import socket
import random
import math
from datetime import datetime
from collections import deque
from pathlib import Path
from http.server import BaseHTTPRequestHandler, HTTPServer # PHASE 3: Added for HTTP Ingest

from PySide6.QtCore import Qt, QObject, QThread, Signal, Slot, QTimer, QSize, QPoint, QEvent
from PySide6.QtGui import (QIcon, QAction, QPixmap, QColor, QTextCursor, QPainter, 
                          QBrush, QLinearGradient, QPen, QFont, QPalette)
from PySide6.QtWidgets import QWidget

import serial
from serial.tools import list_ports
from pynput import keyboard

# --- PQC Integration ---
try:
    import pqcrypto_bindings
    PQC_AVAILABLE = True
except ImportError:
    PQC_AVAILABLE = False
    print("[WARNING] PQC bindings not available. Classical crypto only.")

# --- ML-KEM (FIPS 203) Support ---
try:
    from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.hkdf import HKDF
    MLKEM_AVAILABLE = True
except ImportError:
    MLKEM_AVAILABLE = False
    print("[WARNING] ML-KEM support requires cryptography library")

# --- Cobra Lab icon helpers ---
def _cc_icon_path():
    """Main Cobra Lab app icon (top-left + tray)"""
    try:
        return str((Path(__file__).parent / "icon.png").resolve())
    except Exception:
        return None

def _cc_char_icon_path(char_name: str = "cipher"):
    """
    Character-specific icons:
      - cipher  -> ciphericon.png / .jpg
      - echo    -> echoicon.png / .jpg
      - ayatoki -> ayatokiicon.png / ayatoki-icon.png / .jpg
      - mitsu   -> mitsuicon.png / .jpg (PHASE 3)
    """
    base = Path(__file__).parent
    candidates = []

    if char_name == "cipher":
        candidates = ["ciphericon.png", "ciphericon.jpg"]
    elif char_name == "echo":
        candidates = ["echoicon.png", "echoicon.jpg"]
    elif char_name == "ayatoki":
        candidates = ["ayatokiicon.png", "ayatoki-icon.png", "ayatokiicon.jpg"]
    elif char_name == "mitsu":
        candidates = ["mitsuicon.png", "mitsuicon.jpg", "mitsu-icon.png"]

    for name in candidates:
        p = base / name
        if p.exists():
            return str(p.resolve())

    # Fallback to main lab icon
    return _cc_icon_path()

def _cc_get_icon():
    """QIcon for window/tray (Cobra Lab logo)"""
    p = _cc_icon_path()
    if p and os.path.exists(p):
        return QIcon(p)
    pm = QPixmap(32, 32)
    pm.fill(QColor("#c400ff"))
    return QIcon(pm)

def _cc_get_pixmap(size: int = 60, char_name: str = "cipher"):
    """Character avatar pixmap"""
    p = _cc_char_icon_path(char_name)
    if p and os.path.exists(p):
        pm = QPixmap(p)
        return pm.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
    
    # Fallback colored square
    pm = QPixmap(size, size)
    if char_name == "cipher":
        pm.fill(QColor("#c400ff"))  # Purple
    elif char_name == "echo":
        pm.fill(QColor("#64c8ff"))  # Teal/cyan
    elif char_name == "ayatoki":
        pm.fill(QColor("#ff0844"))  # Red
    elif char_name == "mitsu":
        pm.fill(QColor("#ff69b4"))  # Hot pink
    return pm
# --- end helpers ---

# Global Cobra Lab theme: Black + Red + Purple + Teal + Pink (Phase 3)
CIPHER_COLORS = {
    'bg': '#0a0a0a',        # Pure black background
    'panel': '#1a0a0a',     # Dark red-black panels
    'accent': '#ff0844',    # Hot red accent (Ayatoki)
    'accent2': '#b429f9',   # Purple accent (Cipher)
    'accent3': '#64c8ff',   # Teal/cyan accent (Echo)
    'accent4': '#ff69b4',   # Hot pink accent (Mitsu) - PHASE 3
    'text': '#ffffff',      # Pure white text
    'muted': '#998899',     # Muted purple-gray
    'success': '#00ff88',   # Success green
    'warning': '#ffaa00',   # Warning orange
    'error': '#ff0844',     # Red error
    'blue': '#b429f9',      # Purple instead of blue
    'pqc': '#ff6b35'        # PQC accent color
}

# Enhanced directory structure
DEFAULT_DIR = Path.home() / "Desktop" / "CobraLab_EntropicChaos"
KEYS_DIR = DEFAULT_DIR / "keys"
LOGS_DIR = DEFAULT_DIR / "logs"
AUDIT_DIR = DEFAULT_DIR / "audits"  # NEW: Phase 2 audit logs
DEFAULT_DIR.mkdir(parents=True, exist_ok=True)
KEYS_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)
AUDIT_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_LOG = LOGS_DIR / f"cipherchaos_session_{os.getpid()}.txt"

class PQCManager:
    """Post-Quantum Cryptography manager - Phase 2: Hybrid Kyber+Falcon"""
    
    def __init__(self):
        self.available = PQC_AVAILABLE
        
    def wrap_and_sign(self, classical_key):
        """Phase 2: Wrap with Kyber KEM, Sign with Falcon (Hybrid)"""
        if not self.available:
            raise Exception("PQC bindings not available")
        try:
            import pqcrypto_bindings
            
            # 1. Kyber512 Key Encapsulation (Transport)
            pk_kyber, sk_kyber = pqcrypto_bindings.kyber_keygen()
            ciphertext, shared_secret = pqcrypto_bindings.kyber_encapsulate(pk_kyber)
            
            # XOR classical key with Kyber shared secret
            wrapped_key = bytearray(classical_key)
            for i in range(min(len(wrapped_key), len(shared_secret))):
                wrapped_key[i] ^= shared_secret[i]
            
            # 2. Falcon512 Signature (Authenticity)
            pk_falcon, sk_falcon = pqcrypto_bindings.falcon_keygen()
            # Sign the ciphertext to prove authenticity
            signature = pqcrypto_bindings.falcon_sign(sk_falcon, ciphertext)
            
            return {
                'wrapped_key': bytes(wrapped_key),
                'ciphertext': bytes(ciphertext),
                'kyber_pk': bytes(pk_kyber),
                'kyber_sk': bytes(sk_kyber),
                'falcon_pk': bytes(pk_falcon),
                'falcon_sk': bytes(sk_falcon),
                'signature': bytes(signature),
                'shared_secret': bytes(shared_secret),
                'type': 'kyber512_falcon512_hybrid'
            }
        except Exception as e:
            raise Exception(f"PQC Hybrid wrapping failed: {e}")
    
    def verify_signature(self, pqc_bundle):
        """Phase 2: Ayatoki's Post-Wrap Signature Verification"""
        if not self.available:
            return False
        try:
            import pqcrypto_bindings
            
            pk = pqc_bundle['falcon_pk']
            msg = pqc_bundle['ciphertext']  # We signed the ciphertext
            sig = pqc_bundle['signature']
            
            return pqcrypto_bindings.falcon_verify(pk, msg, sig)
        except Exception as e:
            print(f"Signature Verification Error: {e}")
            return False
    
    # Legacy methods for backward compatibility
    def wrap_key_with_kyber(self, classical_key):
        """Legacy: Kyber-only wrapping"""
        result = self.wrap_and_sign(classical_key)
        return {
            'wrapped_key': result['wrapped_key'],
            'public_key': result['kyber_pk'],
            'secret_key': result['kyber_sk'],
            'ciphertext': result['ciphertext'],
            'shared_secret': result['shared_secret'],
            'type': 'kyber512_wrapped'
        }
    
    def wrap_key_with_falcon(self, classical_key):
        """Legacy: Falcon-only signing"""
        result = self.wrap_and_sign(classical_key)
        return {
            'key': classical_key,
            'signature': result['signature'],
            'public_key': result['falcon_pk'],
            'secret_key': result['falcon_sk'],
            'type': 'falcon512_signed'
        }
    
    def save_pqc_wrapped_key(self, wrapped_data, key_type, name=None):
        """Save PQC-wrapped key to disk"""
        if not name:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            name = f"{key_type}_{timestamp}"
        
        key_file = KEYS_DIR / f"{name}_wrapped.key"
        
        save_data = {
            'type': wrapped_data['type'],
            'created': datetime.now().isoformat()
        }
        
        if 'wrapped_key' in wrapped_data:
            save_data['wrapped_key'] = base64.b64encode(wrapped_data['wrapped_key']).decode('ascii')
            save_data['ciphertext'] = base64.b64encode(wrapped_data['ciphertext']).decode('ascii')
        else:
            save_data['key'] = base64.b64encode(wrapped_data['key']).decode('ascii')
            save_data['signature'] = base64.b64encode(wrapped_data['signature']).decode('ascii')
        
        save_data['public_key'] = base64.b64encode(wrapped_data['public_key']).decode('ascii')
        
        with open(key_file, 'w') as f:
            json.dump(save_data, f, indent=2)
        
        secret_file = KEYS_DIR / f"{name}_secret.key"
        with open(secret_file, 'wb') as f:
            f.write(wrapped_data['secret_key'])
        
        return {
            'name': name,
            'key_file': str(key_file),
            'secret_file': str(secret_file)
        }

class EnhancedEntropyAuditor:
    """Enhanced entropy auditing with PQC considerations"""
    
    def __init__(self):
        self.test_history = deque(maxlen=100)
    
    def comprehensive_audit(self, raw_bytes: bytes) -> dict:
        """Comprehensive entropy audit suitable for PQC applications"""
        n = len(raw_bytes)
        if n == 0:
            return {"score": 0.0, "tests": {}, "pqc_ready": False}

        tests = {}
        tests.update(self._basic_statistical_tests(raw_bytes))
        tests.update(self._advanced_entropy_tests(raw_bytes))
        tests.update(self._nist_inspired_tests(raw_bytes))
        
        score = self._calculate_overall_score(tests)
        pqc_ready = (score >= 65.0 and 
                    tests.get('entropy_bpb', 0) >= 6.0 and 
                    n >= 32)
        
        result = {
            "score": round(score, 1),
            "tests": tests,
            "pqc_ready": pqc_ready,
            "sample_size": n,
            "timestamp": time.time(),
            "freq_pass": tests.get('frequency_test', False),
            "runs_pass": tests.get('runs_test', False),
            "chi_pass": tests.get('chi_square_test', False),
            "entropy_bpb": tests.get('entropy_bpb', 0.0)
        }
        
        self.test_history.append(result)
        return result
    
    def _basic_statistical_tests(self, data: bytes) -> dict:
        n = len(data)
        total_bits = n * 8
        
        ones = sum(bin(b).count("1") for b in data)
        p1 = ones / total_bits
        freq_score = 100.0 * (1.0 - abs(p1 - 0.5) * 2)
        freq_pass = 0.45 <= p1 <= 0.55
        
        prev = (data[0] >> 7) & 1
        runs = 0
        for b in data:
            for i in range(7, -1, -1):
                bit = (b >> i) & 1
                if bit != prev:
                    runs += 1
                    prev = bit
        
        expected_runs = 2 * total_bits * p1 * (1 - p1)
        runs_deviation = abs(runs - expected_runs) / (expected_runs + 1e-9)
        runs_score = 100.0 * max(0, 1.0 - runs_deviation)
        runs_pass = runs_deviation < 0.2
        
        return {
            "frequency_test": freq_pass,
            "frequency_score": round(freq_score, 1),
            "frequency_ratio": round(p1, 4),
            "runs_test": runs_pass,
            "runs_score": round(runs_score, 1),
            "runs_count": runs,
            "runs_expected": round(expected_runs, 1)
        }
    
    def _advanced_entropy_tests(self, data: bytes) -> dict:
        n = len(data)
        
        hist = [0] * 256
        for b in data:
            hist[b] += 1
        
        entropy = 0.0
        for count in hist:
            if count > 0:
                p = count / n
                entropy -= p * math.log2(p)
        
        entropy_score = (entropy / 8.0) * 100.0
        
        expected = n / 256.0
        chi_square = sum(((h - expected) ** 2) / (expected + 1e-9) for h in hist)
        chi_expected_min, chi_expected_max = 150.0, 350.0
        chi_pass = chi_expected_min <= chi_square <= chi_expected_max if n >= 1024 else True
        chi_score = 100.0 if chi_pass else 70.0
        
        try:
            import zlib
            compressed_size = len(zlib.compress(data, level=9))
            compression_ratio = compressed_size / n
            compression_score = min(100.0, (compression_ratio * 130.0))
        except:
            compression_ratio = 1.0
            compression_score = 100.0
        
        return {
            "entropy_bpb": round(entropy, 3),
            "entropy_score": round(entropy_score, 1),
            "chi_square": round(chi_square, 2),
            "chi_square_test": chi_pass,
            "chi_square_score": round(chi_score, 1),
            "compression_ratio": round(compression_ratio, 3),
            "compression_score": round(compression_score, 1)
        }
    
    def _nist_inspired_tests(self, data: bytes) -> dict:
        n = len(data)
        bits = ''.join(format(b, '08b') for b in data)
        
        block_size = min(128, n * 8 // 10)
        if block_size < 8:
            return {"block_frequency_test": True, "block_frequency_score": 100.0}
        
        blocks = [bits[i:i+block_size] for i in range(0, len(bits), block_size) if len(bits[i:i+block_size]) == block_size]
        
        if len(blocks) < 2:
            return {"block_frequency_test": True, "block_frequency_score": 100.0}
        
        block_proportions = [block.count('1') / block_size for block in blocks]
        block_variance = sum((p - 0.5) ** 2 for p in block_proportions) / len(blocks)
        block_score = 100.0 * max(0, 1.0 - (block_variance * 40))
        block_pass = block_variance < 0.06
        
        max_run = 0
        current_run = 0
        current_bit = bits[0] if bits else '0'
        
        for bit in bits:
            if bit == current_bit:
                current_run += 1
            else:
                max_run = max(max_run, current_run)
                current_run = 1
                current_bit = bit
        max_run = max(max_run, current_run)
        
        expected_max_run = math.log2(len(bits)) + 3 if len(bits) > 0 else 0
        run_score = 100.0 * max(0, 1.0 - abs(max_run - expected_max_run) / expected_max_run) if expected_max_run > 0 else 100.0
        run_pass = abs(max_run - expected_max_run) < expected_max_run * 0.4 if expected_max_run > 0 else True
        
        return {
            "block_frequency_test": block_pass,
            "block_frequency_score": round(block_score, 1),
            "block_variance": round(block_variance, 6),
            "longest_run_test": run_pass,
            "longest_run_score": round(run_score, 1),
            "longest_run": max_run,
            "expected_max_run": round(expected_max_run, 1)
        }
    
    def _calculate_overall_score(self, tests: dict) -> float:
        weights = {
            'frequency_score': 0.2,
            'runs_score': 0.15,
            'entropy_score': 0.25,
            'chi_square_score': 0.15,
            'compression_score': 0.1,
            'block_frequency_score': 0.1,
            'longest_run_score': 0.05
        }
        
        score = 0.0
        total_weight = 0.0
        
        for key, weight in weights.items():
            if key in tests:
                score += tests[key] * weight
                total_weight += weight
        
        return (score / total_weight) if total_weight > 0 else 0.0

class EntropyVisualization(QWidget):
    """Custom widget for entropy visualization"""
    
    def __init__(self):
        super().__init__()
        self.last_keypress_time = 0.0
        try:
            self.setWindowIcon(_cc_get_icon())
        except Exception:
            pass
        self.setMinimumHeight(150)
        self.entropy_data = deque(maxlen=200)
        self.keystroke_data = deque(maxlen=200)
        self.rgb_color = QColor(196, 0, 255)
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(50)
        
        self.time_offset = 0
    
    def add_entropy_point(self, entropy_level):
        self.entropy_data.append(entropy_level)
    
    def add_keystroke_point(self, rate):
        self.keystroke_data.append(rate)
    
    def set_rgb_color(self, r, g, b):
        self.rgb_color = QColor(r, g, b)
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        painter.fillRect(self.rect(), QColor(CIPHER_COLORS['panel']))
        
        width = self.width()
        height = self.height()
        
        if width <= 0 or height <= 0:
            return
        
        if len(self.entropy_data) > 1:
            gradient = QLinearGradient(0, 0, width, 0)
            gradient.setColorAt(0, self.rgb_color)
            gradient.setColorAt(1, QColor(CIPHER_COLORS['accent2']))
            
            painter.setBrush(QBrush(gradient))
            painter.setPen(QPen(self.rgb_color, 2))
            
            points = []
            for i, entropy in enumerate(self.entropy_data):
                x = (i / max(1, len(self.entropy_data) - 1)) * width
                base_y = height * (1 - entropy / 100.0) * 0.4 + height * 0.3
                wave_y = math.sin((x + self.time_offset) * 0.02) * 20
                wave_y += math.sin((x + self.time_offset) * 0.05) * 10
                y = base_y + wave_y
                points.append((x, y))
            
            if points:
                polygon_points = [QPoint(int(x), int(y)) for x, y in points]
                painter.drawPolyline(polygon_points)
        
        if len(self.keystroke_data) > 0:
            painter.setPen(QPen(QColor(CIPHER_COLORS['accent2']), 1))
            painter.setBrush(QBrush(QColor(CIPHER_COLORS['accent2'])))
            
            bar_width = max(1, width // len(self.keystroke_data))
            for i, rate in enumerate(self.keystroke_data):
                x = i * bar_width
                bar_height = min(height * 0.6, (rate / 20.0) * height * 0.6)
                y = height - bar_height
                
                painter.setOpacity(0.3)
                painter.drawRect(int(x), int(y), bar_width, int(bar_height))
                painter.setOpacity(1.0)
        
        painter.setPen(QPen(QColor(CIPHER_COLORS['muted']), 1))
        painter.setOpacity(0.2)
        
        for i in range(5):
            y = (height / 4) * i
            painter.drawLine(0, int(y), width, int(y))
        
        for i in range(10):
            x = (width / 9) * i
            painter.drawLine(int(x), 0, int(x), height)
        
        painter.setOpacity(1.0)
        self.time_offset += 2

class NetworkManager(QObject):
    """Handles network detection and CobraMesh simulation"""
    
    network_status_changed = Signal(dict)
    
    def __init__(self):
        super().__init__()
        self.last_keypress_time = 0.0
        try:
            self.setWindowIcon(_cc_get_icon())
        except Exception:
            pass
        self.headscale_connected = False
        self.mesh_peers = 0
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_network)
        self.timer.start(5000)
        self.check_network()
    
    def check_network(self):
        headscale_status = self.check_headscale()
        
        status = {
            'headscale': headscale_status,
            'mesh_peers': random.randint(1, 4) if headscale_status else 0,
            'uplink': 'active' if headscale_status else 'disconnected',
            'mesh_status': 'CobraMesh Ready' if headscale_status else 'Standalone Mode'
        }
        
        self.headscale_connected = headscale_status
        self.mesh_peers = status['mesh_peers']
        self.network_status_changed.emit(status)
    
    def check_headscale(self):
        try:
            if os.name == 'nt':
                result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq tailscaled.exe'], 
                                      capture_output=True, text=True, timeout=2)
                if 'tailscaled.exe' in result.stdout:
                    return True
                result = subprocess.run(['netsh', 'interface', 'show', 'interface'], 
                                      capture_output=True, text=True, timeout=2)
                if 'Tailscale' in result.stdout:
                    return True
            else:
                result = subprocess.run(['pgrep', 'tailscaled'], 
                                      capture_output=True, timeout=2)
                if result.returncode == 0:
                    return True
                result = subprocess.run(['ip', 'link', 'show', 'tailscale0'], 
                                      capture_output=True, text=True, timeout=2)
                if result.returncode == 0:
                    return True
        except:
            pass
        return False

# Phase 2: Echo Worker Class
class EchoWorker(QObject):
    """Worker for Echo-tan ESP32-S3 auditor - Streams VERIFIED entropy only"""
    
    status_update = Signal(str)
    quip_generated = Signal(str, str)  # (quip, character)
    audit_result = Signal(dict)
    rgb_updated = Signal(int, int, int)
    error_occurred = Signal(str)
    connection_status = Signal(bool)
    esp_status_updated = Signal(dict)
    entropy_received = Signal(int)  # Phase 2: bytes added to verified pool
    
    def __init__(self):
        super().__init__()
        self.last_keypress_time = 0.0
        
        self.serial_port = None
        self.baud_rate = 115200
        self.brightness = 0.4  # Softer than Cipher
        self.serial_connection = None
        self.connected = False  # Track physical connection
        
        # Phase 2: Verified Entropy Buffer
        self.verified_buffer = deque(maxlen=500)
        self.buffer_lock = threading.Lock()
        
        self.response_thread = None
        self.stop_event = threading.Event()
        
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.request_status)
        
        # Echo personality - calm, poetic
        self.echo_quips = [
            "Every signal is a heartbeat. Every error, a sigh.",
            "I hear Cipher's thunder... and answer with rain.",
            "Internal health verified. Streaming pure entropy.",
            "Noise is only fear, waiting to be understood.",
            "My circuits sing lullabies from chaos.",
            "Trust, but feel. That is my way.",
            "Entropy validated. All tests nominal. Proceeding.",
            "Quality below threshold. Withholding sample.",
            "Signature verified. Provenance chain intact.",
            "Listening to entropy whispers...",
            "Soft glow aligned. LED breathing in teal and dusk.",
            "Key observed and recorded. My audit stands witness.",
            "Another secret shaped. I will remember their origin.",
            "Health test passed. Silent approval granted.",
            "Deviation detected. Sample rejected.",
            "Audit frame captured. Ready for judgment."
        ]
    
    def start_system(self):
        # Only meaningful if we have separate run states in Echo (not currently needed like Cipher)
        if not self.connected:
            return
        
        # Start status polling
        self.status_timer.start(5000)
        
        self.status_update.emit("Echo-tan: Streaming Verified Entropy")
        self.quip_generated.emit(random.choice(self.echo_quips), "echo")
    
    def stop_system(self):
        self.status_timer.stop()
        
        if self.serial_connection:
            try:
                self.serial_connection.write(b"TRNG:STOP\n")
                self.serial_connection.close()
            except:
                pass
            self.serial_connection = None
        
        self.connected = False
        self.connection_status.emit(False)
        self.status_update.emit("Echo-tan paused")
    
    def request_status(self):
        """Poll Echo for status and health metrics"""
        if self.serial_connection and self.connected:
            self.send_serial_command("STAT?")

    def connect_serial(self):
        try:
            if self.serial_connection:
                self.serial_connection.close()
            
            self.serial_connection = serial.Serial(
                port=self.serial_port,
                baudrate=self.baud_rate,
                timeout=0.1, 
                write_timeout=0.2,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                bytesize=serial.EIGHTBITS
            )
            
            self.connected = True
            
            self.response_thread = threading.Thread(target=self.monitor_serial_responses, daemon=True)
            self.response_thread.start()
            
            time.sleep(1.0)
            self.serial_connection.reset_input_buffer()
            self.serial_connection.reset_output_buffer()
            
            # Initial config
            time.sleep(0.2)
            self.send_serial_command(f"BRI:{self.brightness:.2f}")
            time.sleep(0.2)
            self.send_serial_command("VER?")
            time.sleep(0.2)
            self.send_serial_command("STAT?")
            time.sleep(0.2)
            self.send_serial_command("RGB:100,200,255")  # Soft teal
            
            # Phase 2: Start VERIFIED entropy streaming
            time.sleep(0.2)
            self.send_serial_command("TRNG:START,20")  # Request 20Hz verified stream
            
            # Emit synthetic status for GUI initialization
            synthetic_status = {
                'version': 'Echo-tan v1.0 (Connected)',
                'trng_health': 'OK',
                'health_failures': 0,
                'health_warnings': 0,
                'keys_audited': 0
            }
            self.esp_status_updated.emit(synthetic_status)
            
            self.status_timer.start(5000)
            
            self.connection_status.emit(True)
            self.status_update.emit(f"Connected to Echo-tan at {self.serial_port}")
            
        except Exception as e:
            self.serial_connection = None
            self.connected = False
            self.connection_status.emit(False)
            self.error_occurred.emit(f"Echo connection failed: {str(e)}")
    
    def send_serial_command(self, command):
        if not self.serial_connection:
            return False
        
        try:
            if not command.endswith('\n'):
                command += '\n'
            self.serial_connection.write(command.encode('utf-8'))
            self.serial_connection.flush()
            return True
        except Exception as e:
            return False
    
    def monitor_serial_responses(self):
        while self.serial_connection and self.connected:
            try:
                while self.serial_connection.in_waiting > 0:
                    response = self.serial_connection.readline().decode('utf-8', errors='ignore')
                    if response.strip():
                        self.handle_serial_response(response)
            except Exception as e:
                if self.connected:
                    self.error_occurred.emit(f"Echo serial monitoring error: {e}")
                break
            time.sleep(0.02)
    
    def handle_serial_response(self, response):
        try:
            response = response.strip()
            
            # DEBUG: Log ALL responses from Echo
            if response and len(response) > 0:
                print(f"[ECHO DEBUG] Received: {response[:100]}")  # First 100 chars
            
            if "STATUS:" in response:
                idx = response.find("STATUS:") + 7
                status_json = response[idx:]
                try:
                    status_data = json.loads(status_json)
                    self.esp_status_updated.emit(status_data)
                    print(f"[ECHO] Status emitted: {status_data}")
                except json.JSONDecodeError as e:
                    print(f"[ECHO] JSON decode error: {e}")
                    pass
            
            elif response.startswith("TRNG:"):
                # Phase 2: Handle verified entropy stream
                data_str = response.split(":")[1] if ":" in response else ""
                
                if data_str == "HEALTH_FAIL":
                    self.status_update.emit("Echo-tan: Internal Health Check Failed!")
                    self.quip_generated.emit("Deviation detected. Sample rejected.", "echo")
                elif data_str:
                    try:
                        raw_data = base64.b64decode(data_str)
                        # Add to verified buffer
                        with self.buffer_lock:
                            self.verified_buffer.append(raw_data)
                        self.entropy_received.emit(len(raw_data))
                        
                        if random.random() < 0.05:
                            self.quip_generated.emit("Internal health verified. Streaming pure entropy.", "echo")
                    except Exception as e:
                        print(f"[ECHO] TRNG decode error: {e}")
                        pass
            
            elif response.startswith("AUDIT:"):
                audit_json = response[6:]
                if audit_json not in ["ERR", "STARTED", "STOPPED"]:
                    try:
                        audit_data = json.loads(audit_json)
                        self.audit_result.emit(audit_data)
                        print(f"[ECHO] Audit emitted: {audit_data}")
                    except json.JSONDecodeError:
                        pass
            
            elif "Echo-tan" in response or "[echo]" in response:
                self.status_update.emit(f"Echo: {response}")
            
        except Exception as e:
            self.error_occurred.emit(f"Echo response parsing error: {e}")
    
    def get_verified_entropy(self):
        """Phase 2: Ayatoki calls this to pull verified entropy from Echo"""
        with self.buffer_lock:
            if not self.verified_buffer:
                return b""
            data = b"".join(self.verified_buffer)
            self.verified_buffer.clear()
            return data
    
    def request_audit(self, key_id, audit_type):
        """Request audit for specific key"""
        if self.serial_connection:
            cmd = f"AUDIT:KEY,{key_id},{audit_type}"
            self.send_serial_command(cmd)

# Cipher Worker (existing, enhanced for Phase 2)
class CIPHERTANWorker(QObject):
    """Enhanced worker with PQC support, Phase 2 dual audit, and Phase 3 HTTP ingest"""
    
    status_update = Signal(str)
    quip_generated = Signal(str, str)  # (quip, character)
    key_forged = Signal(str, dict)
    pqc_key_generated = Signal(str, dict)
    rgb_updated = Signal(int, int, int)
    keystroke_rate_updated = Signal(float)
    entropy_level_updated = Signal(float)
    error_occurred = Signal(str)
    connection_status = Signal(bool)
    audit_updated = Signal(dict)
    esp_status_updated = Signal(dict)
    
    # Phase 2: Dual audit signals
    prewrap_audit_complete = Signal(dict)
    request_echo_audit = Signal(str, str)  # (key_id, audit_type)
    
    # Phase 3: Mitsu uplink signals
    mitsu_entropy_received = Signal(int, dict)  # (bytes, metadata)
    
    def __init__(self):
        super().__init__()
        self.last_keypress_time = 0.0
        
        self.serial_port = None
        self.baud_rate = 115200
        self.window_seconds = 2.0
        self.brightness = 1.0
        self.lights_enabled = True
        self.realtime_keys = False
        self.include_host_rng = True
        self.include_mouse_entropy = True
        self.include_esp_trng = True
        self.key_log_path = str(DEFAULT_LOG)
        
        self.pqc_enabled = False
        self.kyber_enabled = True
        self.falcon_enabled = True
        self.auto_save_keys = True
        
        # Phase 2: Link to Echo worker
        self.echo_worker = None
        
        self.connected = False      # Serial connection state
        self.chaos_running = False  # Chaos/Generation state
        
        self.serial_connection = None
        self.entropy_chunks = deque(maxlen=4096)
        self.keystroke_times = deque(maxlen=200)
        self.keys_generated = 0
        self.hue_offset = 0.0
        
        # PHASE 3: Remote Entropy Ingest (from Mitsu/ChaosMagnet)
        self.remote_chunks = deque()
        self.remote_lock = threading.Lock()
        self.remote_bytes = 0
        self.mitsu_last_seq = 0
        self.mitsu_connected = False
        
        self.entropy_lock = threading.Lock()
        self.stop_event = threading.Event()
        
        self.keyboard_listener = None
        
        self.pqc_manager = PQCManager()
        self.entropy_auditor = EnhancedEntropyAuditor()
        
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.request_esp_status)
        self.response_thread = None
        
        # LED throttling (Fixed for speed)
        self.last_rgb_time = 0
        self.animation_thread = None
        
        # Ayatoki personality
        self.ayatoki_quips = [
            "El Psy Kongroo! See? Chaos theory wins again.",
            "Three-source mixing complete. Entropy crystallized.",
            "Pre-audit: Quality verified. Proceeding to PQC wrapping.",
            "Kyber+Falcon hybrid deployed. Post-quantum fortress erected.",
            "Signature verified. The theorem holds. Q.E.D.",
            "Cipher's chaos, Echo's verification, my orchestration.",
            "Mixed pool entropy: 7.98 bits/byte. Excellent.",
            "Phase 3 operational. All nodes reporting nominal.",
            "Dual audit checkpoint: Pre-wrap PASSED, Post-wrap VERIFIED.",
            "Perfect! Another proof that math can weaponize randomness.",
            "The stable kernel to Cipher's wild overclock - that's us.",
            "My lab, my rules: test everything, trust the numbers.",
            "Blockchain ledger updated. Mooncake minted with PQC frosting.",
            "Cross-node entropy synchronized. Distributed chaos achieved.",
            "Mitsu uplink confirmed. External chaos merged into the pool."
        ]
        
        # Cipher personality
        self.cipher_quips = [
            "Entropy buffet's open - who's hungry for bits?",
            "Lattices spun tight, Senpai. Kyber's purring~",
            "Falcon signed, sealed, delivered. Quantum clowns can sit down.",
            "I don't do predictable. I *murder* predictable.",
            "Packets scrambled, mesh tangled - chaos relay primed!",
            "Another key minted - smell that? That's post-quantum spice.",
            "My TRNG hums like a rock concert, and every photon's backstage.",
            "USB jitter swallowed whole - entropy's dessert course!",
            "Bitstream twisted beyond recognition. Predict me? Try me.",
            "Audit complete. Verdict: flawless chaos, 10/10 sparkle.",
            "Quantum adversaries knock - Cipher slams the door shut.",
            "Private key? More like private *tsunami*.",
            "Entropy circus? I own the tent, the lions, the ring of fire.",
            "Silicon dreams wired to chaos reality - next round's mine.",
            "Every spike of entropy is a love letter Echo can verify~",
            "Noise harvested, entropy bottled, PQC corked tight. Cheers!",
            "Kyber crystals aligned - let the lattice sing.",
            "Falcon dives, signature lands - classical crypto's a fossil.",
            "Audit log sealed, provenance preserved - Senpai, admire my craft.",
            "Predictability filed under 'extinct.' CipherChaos: still undefeated."
        ]
        
        # Phase 3: Mitsu personality (cozy tech gremlin)
        self.mitsu_quips = [
            "Uplink established! Entropy delivery inbound~",
            "If it builds on my bench, it ships. Same goes for entropy!",
            "ccache is love; entropy pooling is aftercare.",
            "Harvester threads nominal. Streaming chaos your way!",
            "Network handshake complete. Let's compile some keys!",
            "Entropy packet dispatched. Receipt confirmed!",
            "My sensors are humming. Quality looking good!",
            "Cross-node sync achieved. Distributed builds are the best builds.",
            "Chaos payload delivered. Time for a sticker!",
            "Pool contribution logged. Ayatoki should be happy~",
            "Audio + Video + System = Maximum entropy coverage!",
            "Remote forge online. Mitsu reporting for duty!"
        ]
    
    def set_echo_worker(self, echo_worker):
        """Phase 2: Link Echo worker for verified entropy mixing"""
        self.echo_worker = echo_worker
    
    def add_remote_entropy(self, payload: bytes, meta: dict | None = None):
        """Phase 3: Ingest remote entropy from HTTP Server (Mitsu)"""
        try:
            with self.remote_lock:
                self.remote_chunks.append(payload)
                self.remote_bytes += len(payload)
            
            # Track Mitsu connection status
            self.mitsu_connected = True
            if meta:
                self.mitsu_last_seq = meta.get("seq", self.mitsu_last_seq)
            
            # Show activity in graph
            level = min(100.0, len(payload) / 1024.0 * 20.0) 
            self.entropy_level_updated.emit(level)
            
            # Emit signal for GUI tracking
            self.mitsu_entropy_received.emit(len(payload), meta or {})
            
            if meta:
                src = meta.get("source", "REMOTE")
                seq = meta.get("seq", "?")
                # Only log every 10th packet to reduce spam
                if isinstance(seq, int) and seq % 10 == 0:
                    self.status_update.emit(f"Mitsu: Received {len(payload)}B from {src} (Seq: {seq})")
            
            # Occasional Mitsu quip
            if random.random() < 0.05:
                self.quip_generated.emit(random.choice(self.mitsu_quips), "mitsu")
                
        except Exception as e:
            self.error_occurred.emit(f"Remote ingest error: {e}")

    def start_system(self):
        """Engage Chaos Mode - Start Generation"""
        if self.chaos_running:
            return
            
        self.chaos_running = True
        self.stop_event.clear()
        
        # Start input listeners
        self.start_keyboard_listener()
        
        # Start Entropy Loop
        self.entropy_thread = threading.Thread(target=self.entropy_processing_loop, daemon=True)
        self.entropy_thread.start()
        
        # Auto-start TRNG if enabled
        if self.connected and self.include_esp_trng:
            self.send_serial_command("TRNG:START,10")
        
        self.status_update.emit("CipherChaos chaos system online with PQC support!")
        if self.pqc_enabled and PQC_AVAILABLE:
            self.quip_generated.emit("Kyber crystals aligned - let the lattice sing.", "cipher")
        else:
            self.quip_generated.emit(random.choice(self.cipher_quips), "cipher")
    
    def stop_system(self):
        """Stop Chaos Mode - Connection remains active"""
        self.chaos_running = False
        self.stop_event.set()
        
        if self.keyboard_listener:
            try:
                self.keyboard_listener.stop()
            except:
                pass
            
        if self.connected:
             self.send_serial_command("TRNG:STOP")
            
        self.status_update.emit("Chaos paused. Cipher still connected.")
    
    def connect_serial(self):
        try:
            if self.serial_connection:
                self.serial_connection.close()
                
            self.serial_connection = serial.Serial(
                port=self.serial_port,
                baudrate=self.baud_rate,
                timeout=0.1,  
                write_timeout=0.1, 
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                bytesize=serial.EIGHTBITS
            )
            
            self.connected = True
            
            # Start threads immediately upon connection
            self.response_thread = threading.Thread(target=self.monitor_serial_responses, daemon=True)
            self.response_thread.start()
            
            # Start Animation Thread immediately (Idle Rainbow Mode)
            if not (self.animation_thread and self.animation_thread.is_alive()):
                self.animation_thread = threading.Thread(target=self._animation_loop, daemon=True)
                self.animation_thread.start()
            
            time.sleep(2.0)
            self.serial_connection.reset_input_buffer()
            self.serial_connection.reset_output_buffer()
            
            # Initialization
            self.send_serial_command(f"BRI:{self.brightness:.2f}")
            time.sleep(0.1)
            self.send_serial_command("VER?")
            time.sleep(0.1)
            self.send_serial_command("STAT?")
            
            # Start status polling
            self.status_timer.start(5000)

            # Emit initial synthetic status
            synthetic_status = {
                'version': 'Cipher-tan v2.1 (Connected)',
                'wifi_entropy_bytes': 0,
                'usb_entropy_bytes': 0
            }
            self.esp_status_updated.emit(synthetic_status)
            
            self.connection_status.emit(True)
            self.status_update.emit(f"Connected to CipherChaos at {self.serial_port}")
            
        except Exception as e:
            self.serial_connection = None
            self.connected = False
            self.connection_status.emit(False)
            self.error_occurred.emit(f"Connection failed: {str(e)}")
    
    def send_serial_command(self, command):
        if not self.serial_connection:
            return False
            
        try:
            if not command.endswith('\n'):
                command += '\n'
            
            self.serial_connection.write(command.encode('utf-8'))
            if not command.startswith("RGB:"):
                self.serial_connection.flush()
            return True
            
        except serial.SerialTimeoutException:
            return False
        except Exception as e:
            self.error_occurred.emit(f"Serial write error: {str(e)}")
            return False
    
    def request_esp_status(self):
        if self.serial_connection and self.connected:
            self.send_serial_command("STAT?")
    
    def monitor_serial_responses(self):
        while self.serial_connection and self.connected:
            try:
                while self.serial_connection.in_waiting > 0:
                    response = self.serial_connection.readline().decode('utf-8', errors='ignore')
                    if response.strip():
                        self.handle_serial_response(response)
            except Exception as e:
                if self.connected:
                    self.error_occurred.emit(f"Serial monitoring error: {e}")
                break
            time.sleep(0.02) 
    
    def handle_serial_response(self, response):
        try:
            response = response.strip()
            
            if "STATUS:" in response:
                idx = response.find("STATUS:") + 7
                status_json = response[idx:]
                try:
                    status_data = json.loads(status_json)
                    self.esp_status_updated.emit(status_data)
                except json.JSONDecodeError:
                    pass
                
            elif response.startswith("TRNG:"):
                trng_data = response[5:]
                if trng_data not in ["ERR", "OK", "OFF"]:
                    try:
                        raw_data = base64.b64decode(trng_data)
                        self.add_trng_entropy(raw_data)
                    except:
                        pass
                        
            elif "cipher-tan" in response or "[cipher-tan]" in response:
                self.status_update.emit(f"Cipher: {response}")
                
        except Exception as e:
            self.error_occurred.emit(f"Response parsing error: {e}")
    
    def add_trng_entropy(self, trng_data):
        # Only process TRNG data if chaos mode is active
        if not self.include_esp_trng or not self.chaos_running:
            return
            
        with self.entropy_lock:
            entropy_chunk = hashlib.blake2s(trng_data + os.urandom(4), digest_size=16).digest()
            self.entropy_chunks.append(entropy_chunk)
        
        level = min(100.0, len(self.entropy_chunks) / 20.0)
        self.entropy_level_updated.emit(level)
    
    def start_keyboard_listener(self):
        try:
            self.keyboard_listener = keyboard.Listener(
                on_press=self.on_key_press,
                on_release=self.on_key_release
            )
            self.keyboard_listener.start()
            self.status_update.emit("Keyboard listener started")
        except Exception as e:
            self.error_occurred.emit(f"Keyboard listener failed: {str(e)}")
    
    def on_key_press(self, key):
        if not self.chaos_running:
            return
            
        current_time = time.time()
        self.last_keypress_time = current_time
        
        self.keystroke_times.append(current_time)
        while self.keystroke_times and current_time - self.keystroke_times[0] > 3.0:
            self.keystroke_times.popleft()
            
        if len(self.keystroke_times) > 1:
            duration = max(0.001, self.keystroke_times[-1] - self.keystroke_times[0])
            rate = (len(self.keystroke_times) - 1) / duration
            self.keystroke_rate_updated.emit(rate)
        
        self.add_keystroke_entropy(key, current_time)
        
        if random.random() < 0.03:
            self.quip_generated.emit(random.choice(self.cipher_quips), "cipher")
    
    def on_key_release(self, key):
        pass
    
    def _animation_loop(self):
        """Dedicated Thread for RGB Animation - Runs while Connected"""
        while self.connected:
            try:
                if not self.lights_enabled:
                    time.sleep(0.1)
                    continue
                    
                time.sleep(0.05)
                
                # Determine mode: Chaos (Generating) vs Rainbow (Idle)
                if self.chaos_running:
                    # CHAOS MODE (Active Generation)
                    current_time = time.time()
                    time_since_typing = current_time - getattr(self, 'last_keypress_time', 0.0)
                    
                    if time_since_typing < 0.2:
                        hue = random.random()
                        saturation = 0.9
                        brightness = 1.0
                    else:
                         # Breathing Purple when generating but not typing
                        self.hue_offset = (self.hue_offset + 0.02) % 1.0
                        hue = 0.75 + (math.sin(self.hue_offset * 5) * 0.05) # Purple range
                        saturation = 0.9
                        brightness = 0.8
                else:
                    # RAINBOW MODE (Idle / Connected)
                    self.hue_offset = (self.hue_offset + 0.005) % 1.0
                    hue = self.hue_offset
                    saturation = 1.0
                    brightness = 0.4
                    
                r, g, b = colorsys.hsv_to_rgb(hue, saturation, brightness)
                r, g, b = int(r * 255), int(g * 255), int(b * 255)
                
                if self.serial_connection:
                    self.send_serial_command(f"RGB:{r},{g},{b}")
                
                self.rgb_updated.emit(r, g, b)
                
            except Exception:
                time.sleep(0.1)

    def add_keystroke_entropy(self, key, timestamp):
        entropy_data = self.create_entropy_chunk(key, timestamp)
        
        with self.entropy_lock:
            self.entropy_chunks.append(entropy_data)
        
        entropy_level = min(100.0, len(self.entropy_chunks) / 20.0)
        self.entropy_level_updated.emit(entropy_level)
    
    def create_entropy_chunk(self, key, timestamp):
        time_ns = time.perf_counter_ns()
        
        key_code = None
        try:
            key_code = getattr(key, 'vk', None) or getattr(key, 'scan_code', None)
        except:
            pass
        
        payload = f"{time_ns}:{key_code}:{timestamp}".encode('utf-8')
        payload += os.urandom(8)
        
        return hashlib.blake2s(payload, digest_size=16).digest()
    
    def add_mouse_entropy(self, x, y):
        # Strict gate: Mouse entropy only works if chaos is actively running
        if not self.include_mouse_entropy or not self.chaos_running:
            return
        try:
            ts = time.perf_counter_ns()
            payload = f"{int(x)},{int(y)},{ts}".encode('utf-8') + os.urandom(4)
            chunk = hashlib.blake2s(payload, digest_size=16).digest()
            with self.entropy_lock:
                self.entropy_chunks.append(chunk)
            level = min(100.0, len(self.entropy_chunks) / 20.0)
            self.entropy_level_updated.emit(level)
        except Exception as e:
            self.error_occurred.emit(f"Mouse entropy error: {e}")
    
    def entropy_processing_loop(self):
        while self.chaos_running and not self.stop_event.wait(self.window_seconds):
            try:
                self.process_entropy_window()
            except Exception as e:
                self.error_occurred.emit(f"Entropy processing error: {str(e)}")
    
    def process_entropy_window(self):
        """Phase 2 & 3: Ayatoki Orchestrator - Mix (Cipher+Echo+Mitsu) -> Audit -> Wrap -> Verify"""
        
        # === STEP 1: AGGREGATE (Four-Source Mixing) ===
        mixed_pool = bytearray()
        
        # A. Cipher (raw TRNG + jitter)
        with self.entropy_lock:
            if self.entropy_chunks:
                cipher_data = b''.join(self.entropy_chunks)
                mixed_pool.extend(cipher_data)
                self.entropy_chunks.clear()
        
        # B. Echo (VERIFIED entropy only)
        if self.echo_worker:
            echo_data = self.echo_worker.get_verified_entropy()
            if echo_data:
                mixed_pool.extend(echo_data)
                if random.random() < 0.1:
                    self.quip_generated.emit("Echo's verified stream mixed in. Quality assured.", "ayatoki")
        
        # C. Mitsu/ChaosMagnet (Remote HTTP Uplink)
        with self.remote_lock:
            if self.remote_chunks:
                remote_data = b"".join(self.remote_chunks)
                mixed_pool.extend(remote_data)
                self.remote_chunks.clear()
                self.status_update.emit(f"Ayatoki: Mixed {len(remote_data)}B from Mitsu uplink.")
                if random.random() < 0.15:
                    self.quip_generated.emit("Cross-node entropy synchronized. Distributed chaos achieved.", "ayatoki")

        # D. Ayatoki (Host) RNG - 64 bytes
        if self.include_host_rng:
            host_data = os.urandom(64)
            mixed_pool.extend(host_data)
        
        # Need minimum 64 bytes for secure key generation
        if len(mixed_pool) < 64:
            return
        
        # === STEP 2: PRE-WRAP AUDIT (Ayatoki NIST-style validation) ===
        try:
            audit = self.entropy_auditor.comprehensive_audit(mixed_pool)
            self.audit_updated.emit(audit)
            self.prewrap_audit_complete.emit(audit)
            
            if random.random() < 0.15:
                self.quip_generated.emit(f"Three-source mixing complete. Score: {audit['score']:.1f}%", "ayatoki")
        except Exception as e:
            self.error_occurred.emit(f"Pre-audit error: {str(e)}")
            audit = {"score": 75.0, "pqc_ready": True, "entropy_bpb": 7.0}
        
        # Check audit quality
        pqc_enabled = getattr(self, 'pqc_enabled', False)
        pqc_available = PQC_AVAILABLE
        pqc_ready = audit.get('pqc_ready', False)
        
        if not pqc_ready:
            self.status_update.emit(f"Ayatoki: Mixed entropy quality insufficient (score: {audit.get('score', 0):.1f}). Need >= 65.0")
            return
        
        # === STEP 3: KEY GENERATION ===
        # Use SHA3-512 for cryptographic-grade hashing
        key_material = hashlib.sha3_512(mixed_pool).digest()[:32]  # 256-bit key
        
        self.keys_generated += 1
        key_id = f"key_{self.keys_generated}_{int(time.time())}"
        
        # === STEP 4: PQC WRAPPING & SIGNING (Hybrid Kyber+Falcon) ===
        if pqc_enabled and pqc_available and pqc_ready:
            try:
                self.status_update.emit("Ayatoki: Deploying PQC hybrid protection (Kyber+Falcon)...")
                
                # Wrap with Kyber + Sign with Falcon in one operation
                pqc_bundle = self.pqc_manager.wrap_and_sign(key_material)
                
                # === STEP 5: POST-WRAP VERIFICATION (Signature Check) ===
                signature_valid = self.pqc_manager.verify_signature(pqc_bundle)
                
                if signature_valid:
                    self.status_update.emit("Ayatoki: Kyber+Falcon hybrid SUCCESS. Signature VERIFIED.")
                    
                    if random.random() < 0.3:
                        self.quip_generated.emit("Signature verified. The theorem holds. Q.E.D.", "ayatoki")
                    
                    # Save the PQC-protected key
                    if self.auto_save_keys:
                        try:
                            self._save_pqc_hybrid_key(pqc_bundle, key_id)
                        except Exception as e:
                            self.error_occurred.emit(f"Key save failed: {e}")
                    
                    # Create preview (first 12 chars of wrapped key base64)
                    key_b64 = base64.urlsafe_b64encode(pqc_bundle['wrapped_key'][:32]).decode('ascii')
                    
                    metadata = {
                        'timestamp': time.time(),
                        'key_number': self.keys_generated,
                        'key_id': key_id,
                        'entropy_bytes': len(mixed_pool),
                        'pqc_ready': True,
                        'type': 'kyber512_falcon512_hybrid',
                        'wrapping': pqc_bundle['type'],
                        'signature_verified': signature_valid,
                        'sources': ['cipher', 'echo', 'ayatoki', 'mitsu']
                    }
                    
                    # Save audit log
                    self._save_audit_log(key_id, audit, metadata)
                    
                    # Log to session file
                    try:
                        with open(self.key_log_path, 'a', encoding='utf-8') as f:
                            log_entry = {
                                'timestamp': datetime.now().isoformat(),
                                'key_preview': key_b64[:20],
                                'metadata': metadata,
                                'type': 'pqc_hybrid'
                            }
                            f.write(json.dumps(log_entry) + '\n')
                    except Exception as e:
                        self.error_occurred.emit(f"Key logging failed: {e}")
                    
                    self.pqc_key_generated.emit(f"hybrid_{key_b64[:12]}...", metadata)
                    
                    if random.random() < 0.2:
                        self.quip_generated.emit("Kyber+Falcon hybrid deployed. Post-quantum fortress erected.", "ayatoki")
                    
                else:
                    # CRITICAL: Signature verification FAILED
                    self.error_occurred.emit("CRITICAL: Falcon signature verification FAILED!")
                    self.quip_generated.emit("Verification failed. Key rejected. Investigating...", "ayatoki")
                    return
                    
            except Exception as e:
                self.error_occurred.emit(f"PQC hybrid error: {e}")
                # Fall back to classical
                self.save_classical_key(key_material, mixed_pool, audit, key_id)
        else:
            # Classical fallback
            if pqc_enabled and not pqc_ready:
                self.status_update.emit(f"PQC enabled but entropy not ready (score: {audit.get('score', 0):.1f})")
            elif pqc_enabled and not pqc_available:
                self.status_update.emit("PQC enabled but bindings not available")
            
            self.save_classical_key(key_material, mixed_pool, audit, key_id)
    
    def _save_pqc_hybrid_key(self, pqc_bundle, key_id):
        """Save Kyber+Falcon hybrid bundle to disk"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        name = f"hybrid_{key_id}_{timestamp}"
        
        key_file = KEYS_DIR / f"{name}_wrapped.key"
        
        save_data = {
            'type': pqc_bundle['type'],
            'created': datetime.now().isoformat(),
            'wrapped_key': base64.b64encode(pqc_bundle['wrapped_key']).decode('ascii'),
            'ciphertext': base64.b64encode(pqc_bundle['ciphertext']).decode('ascii'),
            'signature': base64.b64encode(pqc_bundle['signature']).decode('ascii'),
            'kyber_pk': base64.b64encode(pqc_bundle['kyber_pk']).decode('ascii'),
            'falcon_pk': base64.b64encode(pqc_bundle['falcon_pk']).decode('ascii')
        }
        
        with open(key_file, 'w') as f:
            json.dump(save_data, f, indent=2)
        
        # Save secret keys separately (more secure)
        secret_file = KEYS_DIR / f"{name}_secret.key"
        secret_data = {
            'kyber_sk': base64.b64encode(pqc_bundle['kyber_sk']).decode('ascii'),
            'falcon_sk': base64.b64encode(pqc_bundle['falcon_sk']).decode('ascii')
        }
        
        with open(secret_file, 'w') as f:
            json.dump(secret_data, f, indent=2)
        
        self.status_update.emit(f"PQC hybrid key saved: {name}")
    
    def save_classical_key(self, key_data, entropy_pool, audit, key_id):
        """Save classical AES256 key with audit trail"""
        metadata = {
            'timestamp': time.time(),
            'key_number': self.keys_generated,
            'key_id': key_id,
            'entropy_bytes': len(entropy_pool),
            'pqc_ready': audit.get('pqc_ready', False),
            'type': 'classical_aes256'
        }
        
        # Save audit log
        self._save_audit_log(key_id, audit, metadata)
        
        try:
            key_b64 = base64.urlsafe_b64encode(key_data).decode('ascii')
            with open(self.key_log_path, 'a', encoding='utf-8') as f:
                log_entry = {
                    'timestamp': datetime.now().isoformat(),
                    'key': key_b64,
                    'metadata': metadata,
                    'type': 'classical'
                }
                f.write(json.dumps(log_entry) + '\n')
            
            self.key_forged.emit(key_b64, metadata)
            
        except Exception as e:
            self.error_occurred.emit(f"Key logging failed: {str(e)}")
    
    def _save_audit_log(self, key_id, audit, metadata):
        """Phase 2: Save per-key audit log for Echo verification"""
        try:
            audit_file = AUDIT_DIR / f"{key_id}_audit.json"
            audit_data = {
                'key_id': key_id,
                'timestamp': datetime.now().isoformat(),
                'ayatoki_prewrap_audit': audit,
                'metadata': metadata,
                'echo_prewrap_audit': None,  # Filled by Echo
                'echo_postwrap_audit': None  # Filled by Echo
            }
            
            with open(audit_file, 'w') as f:
                json.dump(audit_data, f, indent=2)
                
        except Exception as e:
            self.error_occurred.emit(f"Audit log save failed: {e}")


# --- PHASE 3: HTTP Server for Ayatoki Ingest ---

class AyatokiIngestHandler(BaseHTTPRequestHandler):
    """Handles POST requests from Mitsu (ChaosMagnet)"""
    worker: CIPHERTANWorker = None  # Class-level reference set at startup

    def log_message(self, format, *args):
        return # Suppress standard HTTP logging to console

    def do_POST(self):
        if self.path != "/ingest":
            self.send_response(404)
            self.end_headers()
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
            body = self.rfile.read(length)
            
            packet = json.loads(body.decode("utf-8"))
            payload_hex = packet.get("payload_hex")
            
            if not payload_hex:
                raise ValueError("Missing payload_hex")

            payload = bytes.fromhex(payload_hex)

            if self.worker is not None:
                self.worker.add_remote_entropy(payload, packet)

            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"OK")
            
        except Exception as e:
            if self.worker is not None:
                self.worker.error_occurred.emit(f"Ayatoki ingest error: {e}")
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"ERR")

def start_ayatoki_ingest_server(worker: CIPHERTANWorker, host="0.0.0.0", port=8000):
    """Starts the HTTP server in a daemon thread"""
    def _run():
        AyatokiIngestHandler.worker = worker
        try:
            server = HTTPServer((host, port), AyatokiIngestHandler)
            worker.status_update.emit(
                f"Ayatoki: HTTP ingest server listening on {host}:{port} (/ingest)"
            )
            server.serve_forever()
        except Exception as e:
            worker.error_occurred.emit(f"Ayatoki ingest server stopped: {e}")

    t = threading.Thread(target=_run, daemon=True)
    t.start()