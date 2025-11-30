# Entropic Chaos

<div align="center">
  <img src="icon.png" alt="Entropic Chaos" width="200" height="200" style="border-radius: 50%;">
  
  **Distributed Post-Quantum Entropy Generation Network**
  
  *NIST SP 800-90B Audit-Before-Wrap Architecture*
</div>

---

**Entropic Chaos** is a production-quality distributed entropy generation network across the CHIRASU home network mesh. This project showcases rigorous entropy validation through NIST SP 800-90B auditing *before* Post-Quantum Cryptography key wrapping, positioning it as a credible demonstration of next-generation cryptographic systems.

> **⚠️ WARNING:** *THIS IS A PROOF OF CONCEPT SYSTEM. DO NOT USE TO SECURE CRITICAL NETWORKS WITHOUT INDEPENDENT AUDITING.*

The distributed network features **three cryptographic character-nodes**, each representing actual hardware roles:

- **Cipher-tan** (ESP32-S3): Primary entropy harvester (TRNG, WiFi noise, jitter).
- **Echo-tan** (ESP32-S3): Dedicated entropy **auditor** performing independent statistical validation.
- **Ayatoki** (Fedora Orchestrator): Host-side coordinator running full NIST-style test suite, mixing, and PQC pre/post wrap verification.
- **Mitsu-chan** (Remote Node – ChaosMagnet): Independent network harvester streaming entropy over LAN/Tailnet.

**Current Status:**  
**Phase 3: Mitsu Integration 95% COMPLETE — Stability pass in progress**

---

## Features

### Core Architecture

- **Audit-Before-Wrap Principle**  
  All entropy must pass statistical health checks (Ayatoki + Echo) **before** PQC operations.

- **Multi-node entropy harvesting**  
  ESP32 TRNGs + host jitter + mouse + keystrokes + USB timing variability.

- **Dual-hardware audit pipeline (Phase 2)**  
  Echo-tan’s independent validation prevents host-side bias or spoofed entropy.

- **PQC Hybrid Security**  
  - **Kyber512** (Key Encapsulation)  
  - **Falcon512** (Post-quantum digital signatures)  
  Used to wrap and sign entropy-derived keys.

- **Immutable audit trails**  
  Each key is logged with provenance, health scores, entropy byte counts, and signatures.

---

## Phase 3: Mitsu Integration — 95% COMPLETE

Mitsu-chan now operates as a **remote entropy harvester** via the ChaosMagnet subsystem:

- Remote entropy ingestion via Ayatoki’s HTTP ingest server (`/ingest`)
- ChaosMagnet collects CPU jitter, thermal noise, audio/video entropy, and HID timing
- Local health checks (RCT/APT/Shannon) before network transmission
- SHA-3 whitening before uplink
- Integrated into Ayatoki’s NIST pipeline
- All PQC readiness preserved

**Remaining work:**

- Stability fixes (thread tuning, video lifecycle management, UI throttling)
- Long-run stress testing on Mitsu-chan

---

## Entropy Sources

- **Keyboard Timing:** Microsecond-level jitter  
- **Mouse Movement:** Micro-jitter entropy  
- **ESP32 TRNG:** Hardware randomness  
- **USB Timing:** Device-to-host jitter  
- **Audio Noise:** Microphone randomness  
- **Camera Noise:** Sensor-level entropy  
- **Host RNG:** `/dev/urandom`  

---

## GUI Features (Ayatoki Node)

- PySide6 interface styled in Cobra Lab aesthetics
- Three-node panel visualization (Cipher · Echo · Ayatoki)
- Live entropy graph & audit dashboard
- PQC indicators (Kyber/Falcon readiness)
- Adjustable runtime parameters
- Full JSON metadata logging

---

## Development Phases

### Phase 1: Cobra Lab MVP — **COMPLETE**
### Phase 2: Dual Auditor (Echo-tan) — **COMPLETE**

### Phase 3: Mitsu Network Harvester — **95% COMPLETE**
(See above section)

### Phase 4: Dynamic Class System — **PLANNED**
Nodes may dynamically assume:
`harvester`, `auditor`, `validator`, `wrapper`

### Phase 5: Blockchain Ledger Integration — **PLANNED**
All key events anchored in Gorō/Kasumi blockchain with Falcon signatures.

---

## Setup & Installation

### Hardware (Cipher-tan & Echo-tan)

- ESP32-S3 boards  
- WS2812 LED (GPIO48 recommended)  
- USB CDC at 115200 baud  
- 5V USB power  

---

### Ayatoki Host

- Fedora x86_64 (or Ubuntu/Debian)  
- Python 3.8+  
- Rust installed  

### Mitsu Host (ChaosMagnet Node)

- Debian/Fedora/Ubuntu x86_64  
- Python 3.8+  
- Rust installed  
- Audio/mic, camera, mouse, CPU access recommended

---

### Ayatoki Software Installation

```bash
git clone https://github.com/JupitersGhost/entropic-chaos.git
cd entropic-chaos

python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt
````

Build PQC bindings:

```bash
pip install maturin==1.6.0
maturin develop --release
```

Run Ayatoki (Cobra Lab GUI):

```bash
python main.py
```

---

# ESP32 Firmware

## Cipher-tan v2.1

`STAT?` response:

```json
{
  "version": "cipher-tan Enhanced v2.1-Fixed-Complete",
  "uptime_ms": 12345678,
  "keys_forged": 5,
  "wifi_entropy_bytes": 128,
  "usb_entropy_bytes": 256
}
```

## Echo-tan v2.1

Echo-tan firmware:

```
echo-firmware/main.py
```

To install:

1. Connect the ESP32-S3
2. Open in Thonny or MicroPython flasher
3. Flash as main script
4. Ensure Ayatoki config matches the COM port or `/dev/ttyACM*`

Echo will:

* Perform independent entropy checks
* Validate Falcon signatures
* Report status to Cobra Lab GUI

---

# ChaosMagnet (Mitsu-chan Remote Harvester)

ChaosMagnet runs on a **separate device** such as Mitsu-chan, sending entropy over LAN/Tailnet to Ayatoki.

> Ayatoki = Lab + ESP32 Manager
> ChaosMagnet = Remote entropy forge node

### Install (on Mitsu or other remote node)

```bash
cd ChaosMagnet

python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt
```

Build PQC bindings (same as Ayatoki):

```bash
cd pqc_module
pip install maturin==1.6.0
maturin develop --release
cd ..
```

Run ChaosMagnet:

```bash
python main.py
```

ChaosMagnet provides:

* System entropy harvesting
* CPU jitter + thermal noise
* Microphone audio entropy
* Camera entropy
* HID timing entropy
* Local NIST checks (RCT/APT/Shannon)
* SHA-3 whitening
* Frame uplink to Ayatoki’s `/ingest` endpoint

---

# File Structure

```text
Entropic Chaos / Cobra Lab/
├── main.py                     # Ayatoki GUI entry point
├── function.py                 # Cipher/Echo workers + PQC manager
├── gui.py                      # PySide6 UI
├── requirements.txt            # Ayatoki host dependencies
├── icon.png
├── README.md
│
├── cipher-firmware/
│   └── main.py                 # Cipher-tan firmware
│
├── echo-firmware/
│   └── main.py                 # Echo-tan firmware
│
├── ChaosMagnet/                # Mitsu-chan remote entropy harvester
│   ├── main.py                 # ChaosMagnet UI entry point
│   ├── core.py                 # ChaosEngine (mixing, tests, SHA-3)
│   ├── harvester.py            # Entropy harvesters (CPU/audio/video/HID)
│   ├── config.py               # ChaosMagnet configuration
│   ├── utils.py                # Shannon + helper utilities
│   ├── requirements.txt        # Python deps for ChaosMagnet
│   └── pqc_module/             # Rust PQC bindings for ChaosMagnet
│       ├── Cargo.toml
│       └── src/
│           └── lib.rs
│
├── Cargo.toml                  # PQC bindings (Ayatoki)
├── src/
│   └── lib.rs                  # Rust PQC implementation
└── target/release/
    └── libpqcrypto_bindings.so
```

*(Optional internal tools such as local Discord scripts exist separately.)*

---

## Configuration

### GUI Config

* Window duration
* Keystroke capture
* Mouse entropy
* TRNG usage
* PQC enable/disable
* JSON log directory

### ESP32 Config (stored in flash)

```json
{
  "led_pin": 48,
  "brightness": 1.0,
  "personality_level": 0.3,
  "debug_mode": false,
  "led_type": "ws2812"
}
```

---

## Post-Quantum Cryptography

### Kyber512 (KEM)

* NIST FIPS 203-approved
* Lattice-based
* Quantum-resistant

### Falcon512 (Digital Signatures)

* NIST FIPS 205
* Used for key provenance and audits

**Hybrid wrapping:**
AES-256 key XORed with Kyber shared secret + Falcon-signed metadata bundle.

---

## License & Attribution

Licensed under the Apache License 2.0.

Core technologies:

* PySide6
* pqcrypto
* MicroPython
* Rust PyO3

Artwork & CHIRASU branding created specifically for this project.

---

## Contact

GitHub: [https://github.com/JupitersGhost/CipherChaos](https://github.com/JupitersGhost/CipherChaos)
Email: [acousticminja@gmail.com](mailto:acousticminja@gmail.com)

**Philosophy:**

> "Everyone, regardless of the scale of their network, deserves digital sovereignty."

<div align="center">
  <img src="icon.png" alt="Entropic Chaos" width="120" height="120">

**Entropic Chaos / Cobra Lab**
*Distributed Post-Quantum Entropy Generation*
Built with 🔐 by RW from Cobra Tech / CHIRASU

</div>

