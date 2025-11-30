# core.py
import hashlib
import threading
import collections
import time
import json
import os
import queue  # Standard Python thread-safe queue
import requests
from config import POOL_SIZE, HISTORY_LEN, KEYS_DIR, RCT_CUTOFF, APT_CUTOFF
from utils import calculate_shannon_entropy, HealthMonitor, get_timestamp

# --- RUST BINDINGS ---
try:
    import pqcrypto_bindings as pqc
    HAS_PQC = True
    print(" [*] PQC CORE: Rust Bindings Loaded (Kyber-512 + Falcon-512)")
except ImportError:
    HAS_PQC = False
    print(" [!] PQC CORE: Bindings missing. Falling back to standard crypto.")

class ChaosEngine:
    def __init__(self):
        # The Crypto State (Actual Mixing Pool - Always 32 bytes/256 bits)
        self.pool = b'\x00' * 32
        
        # The Display Pool (Rolling buffer for Entropy Graph & Math)
        self.display_pool = collections.deque(maxlen=POOL_SIZE)
        self.display_pool.extend([0] * POOL_SIZE)

        self.lock = threading.Lock()
        
        # Phase 3: Networking & Autonomy
        # MITSU CONFIG: Target is Ayatoki (Fedora) at .19
        self.ayatoki_url = "http://192.168.1.19:8000/ingest" 
        self.network_mode = True 
        self.sequence_id = 0
        
        # STABILITY FIX 1: Persistent Session
        # Reuses TCP connection to Ayatoki (Keep-Alive) to prevent socket exhaustion
        self.session = requests.Session()

        # --- STABILITY ARCHITECTURE: The Producer-Consumer Queue ---
        # Harvesters dump data here instantly. The worker processes it safely.
        self.input_queue = queue.Queue(maxsize=1000)
        
        # STABILITY FIX 2: Dedicated Network Queue
        # Decouples entropy processing from network latency.
        # Maxsize=100 ensures we don't eat RAM if the network dies.
        self.net_queue = queue.Queue(maxsize=100)
        
        # Metrics
        self.total_harvested = 0
        self.history_entropy = collections.deque([0.0]*HISTORY_LEN, maxlen=HISTORY_LEN)
        self.log_buffer = collections.deque(maxlen=20)
        
        # PQC Identity (Session Key)
        self.falcon_pk = None
        self.falcon_sk = None
        self.pqc_active = False 
        
        self.log("Engine Initialized. Waiting for entropy...")
        
        if HAS_PQC:
            self._init_pqc_identity()
            
        # START THE BACKGROUND WORKERS
        self.running = True
        
        # Thread 1: Crypto & Mixing (High Priority - CPU Bound)
        self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.worker_thread.start()
        
        # Thread 2: Network Uplink (Low Priority - IO Bound)
        # This thread handles the waiting/timeouts so the main thread doesn't have to.
        self.net_thread = threading.Thread(target=self._net_worker_loop, daemon=True)
        self.net_thread.start()

    def _init_pqc_identity(self):
        try:
            print("DEBUG: Attempting Falcon Keygen...")
            self.falcon_pk, self.falcon_sk = pqc.falcon_keygen()
            self.pqc_active = True
            self.log("IDENTITY: Falcon-512 Session Key Generated.")
        except Exception as e:
            self.pqc_active = False
            self.log(f"IDENTITY ERROR: {e}")

    def inject_entropy(self, source_name, data):
        """
        NON-BLOCKING ENTRY POINT.
        Harvesters call this. It returns INSTANTLY.
        """
        try:
            self.input_queue.put_nowait((source_name, data))
        except queue.Full:
            pass

    def _worker_loop(self):
        """
        The Entropy Processor.
        This loop MUST NEVER BLOCK on I/O. It only does Math and Queueing.
        """
        last_net_queue_time = 0.0
        
        while self.running:
            try:
                # Wait up to 1s for data
                source_name, data = self.input_queue.get(timeout=1.0)
            except queue.Empty:
                continue

            # --- 1. AUDIT (Local NIST Check) ---
            passed_rct, _ = HealthMonitor.repetition_count_test(data, RCT_CUTOFF)
            if not passed_rct: 
                self.input_queue.task_done()
                continue
                
            passed_apt, _ = HealthMonitor.adaptive_proportion_test(data, APT_CUTOFF)
            if not passed_apt: 
                self.input_queue.task_done()
                continue

            # --- 2. WHITEN (SHA-3 Compression) ---
            whitened_data = hashlib.sha3_256(data).digest()
            self.sequence_id += 1

            # --- 3. UPDATE LOCAL STATE ---
            with self.lock:
                # Mix into Crypto State
                hasher = hashlib.sha3_256()
                hasher.update(self.pool)
                hasher.update(source_name.encode())
                hasher.update(whitened_data)
                self.pool = hasher.digest()
                
                # Update GUI Graph Buffer
                self.display_pool.extend(whitened_data)
                self.total_harvested += len(whitened_data)

                # --- AUTONOMOUS MINTING LOGIC ---
                if self.total_harvested % 320 == 0:
                    pool_quality = calculate_shannon_entropy(bytes(self.display_pool))
                    
                    if self.sequence_id % 50 == 0:
                        self.log(f"LOCAL [{source_name}] Pool Qual: {pool_quality:.2f}")
                    
                    if pool_quality > 7.5 and self.pqc_active:
                        if self.sequence_id % 500 == 0:
                            self.log("AUTONOMOUS: High quality pool. Minting PQC Bundle...")
                            self.get_pqc_bundle(requester="MITSU_AUTO")

            # --- 4. PREPARE NETWORK PACKET (Non-Blocking) ---
            # Instead of sending here, we just build the packet and push to the Net Queue.
            now = time.time()
            if self.network_mode and (now - last_net_queue_time > 0.1): 
                last_net_queue_time = now
                
                chunk_entropy = calculate_shannon_entropy(whitened_data)
                packet = {
                    "node": "mitsu_chaos_magnet",
                    "seq": self.sequence_id,
                    "timestamp": get_timestamp(),
                    "ts_epoch": now,
                    "entropy_estimate": chunk_entropy,
                    "health": "OK",
                    "source": source_name,
                    "metrics": {"size": len(whitened_data)},
                    "payload_hex": whitened_data.hex(),
                    "digest": hashlib.sha3_256(data).hexdigest()
                }
                
                try:
                    # GRACEFUL FALLBACK: 
                    # If Net Queue is full (Ayatoki down?), we drop the packet
                    # to protect the main entropy loop.
                    self.net_queue.put_nowait(packet)
                except queue.Full:
                    # This pass is critical: It means "Drop packet and keep surviving"
                    pass
            
            self.input_queue.task_done()

    def _net_worker_loop(self):
        """
        The Network Uploader (Background Thread).
        Handles the slow HTTP requests to Ayatoki so the main loop stays fast.
        """
        while self.running:
            try:
                # Wait forever for a packet (blocking here is fine, this is a dedicated thread)
                packet = self.net_queue.get()
            except queue.Empty:
                continue

            try:
                # Use the persistent session!
                self.session.post(self.ayatoki_url, json=packet, timeout=0.5)
                
                if packet['seq'] % 50 == 0:
                    self.log(f"UPLINK: Sent Seq {packet['seq']} to Ayatoki")
            except Exception:
                # If Ayatoki is down, we silently fail here. 
                # This prevents the logs from spamming if the server is off.
                pass
            finally:
                self.net_queue.task_done()

    def get_pqc_bundle(self, requester="LOCAL"):
        """Generates, signs, and saves PQC keys."""
        if not self.pqc_active: return None
        with self.lock:
            kyber_pk, kyber_sk = pqc.kyber_keygen()
            context_hash = hashlib.sha3_256(self.pool + kyber_pk).digest()
            signature = pqc.falcon_sign(self.falcon_sk, context_hash)
            
            timestamp = time.time()
            bundle = {
                "type": "COBRA_PQC_BUNDLE",
                "requester": requester,
                "kyber_pk": kyber_pk.hex(),
                "kyber_sk": kyber_sk.hex(),
                "falcon_sig": signature.hex(),
                "falcon_signer_pk": self.falcon_pk.hex(),
                "timestamp": timestamp,
                "human_time": get_timestamp()
            }
            self._save_to_vault(bundle)
            return bundle

    def _save_to_vault(self, bundle):
        filename = f"key_{int(bundle['timestamp'])}_{bundle['kyber_pk'][:8]}.json"
        filepath = os.path.join(KEYS_DIR, filename)
        try:
            with open(filepath, "w") as f:
                json.dump(bundle, f, indent=2)
            self.log(f"VAULT: Saved {filename}")
        except Exception as e:
            self.log(f"VAULT ERROR: {e}")

    def log(self, message):
        ts = time.strftime("%H:%M:%S")
        self.log_buffer.append(f"[{ts}] {message}")

    def get_metrics(self):
        with self.lock:
            current_ent = calculate_shannon_entropy(bytes(self.display_pool))
            self.history_entropy.append(current_ent)
            return {
                "pool_hex": self.pool.hex().upper(),
                "total_bytes": self.total_harvested,
                "current_entropy": current_ent,
                "history": list(self.history_entropy),
                "logs": list(self.log_buffer),
                "pqc_ready": self.pqc_active,
                "net_mode": self.network_mode
            }