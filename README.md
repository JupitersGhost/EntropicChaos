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

**Current Status:**  
**Phase 2: Dual Audit System COMPLETE** — Ayatoki + Echo perform independent NIST-style validation; PQC hybrid wrapping now includes integrity checks across **three devices**.

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

## Phase 2: Cobra Lab Dual Audit (COMPLETE)

The new Phase 2 system introduces a **Dual Hardware Auditor Model**:

### 1. **Pre-Wrap Audit (Ayatoki Host)**  
Ayatoki runs NIST SP 800-90B-inspired tests:

- Frequency  
- Runs  
- Chi-Square  
- Longest-run  
- Shannon entropy estimation  

Keys **cannot** be wrapped until these pass.

### 2. **Post-Wrap Audit (Echo-tan)**  
Echo-tan independently:

- Re-evaluates entropy  
- Confirms byte distribution quality  
- Verifies post-wrap Falcon512 signature integrity  
- Acts as a hardware check-and-balance against Ayatoki  

### 3. **Cipher-tan**  
Primary entropy source feeding TRNG bytes + jitter into the mix.

**Result:**  
Keys are only finalized when **all three nodes agree on entropy quality**, ensuring credible provenance.

---

## Entropy Sources

- **Keyboard Timing**: Microsecond granularity.  
- **Mouse Movement**: Micro-jitter entropy.  
- **ESP32 TRNG (Cipher + Echo)**: Hardware-level randomness.  
- **USB Timing Jitter**: Host-device communication noise.  
- **Host RNG**: Linux `/dev/urandom` integration.

---

## GUI Features (Ayatoki Node)

- **Modern PySide6 interface** (Cobra Lab aesthetic).
- **Three-node status panels**: Cipher · Echo · Ayatoki.
- **Live entropy graph & audit dashboard**.
- **PQC indicators**: Kyber512/Falcon512 readiness.
- **Configurable runtime parameters**:
  - sample windows  
  - brightness  
  - PQC enable/disable  
  - logging paths  
- **JSON-based key logs with full metadata**.

---

## Development Phases

### Phase 1: Cobra Lab MVP – **COMPLETE**

Goal: Establish Ayatoki + Cipher-tan with GUI + PQC support.

Achievements:
- Host orchestrator ready  
- Cipher-tan TRNG streaming  
- PQC bindings functional  
- Baseline audit + key generation flow  

### Phase 2: Echo Dual Auditor – **COMPLETE**

Goal: Introduce Echo-tan as independent hardware auditor.

Achievements:
- Echo integrated  
- Verified streaming  
- Pre-wrap + post-wrap audits  
- Falcon signature verification  
- Full tri-node visualization in GUI  

### Phase 3: Mitsu Network Harvester – **NEXT**

Will add:
- Remote entropy frames via Tailscale  
- CPU jitter, thermal noise  
- Idle-state guardrails  

### Phase 4: Dynamic Class System – **PLANNED**

Nodes may dynamically assume:
`harvester`, `auditor`, `validator`, `wrapper`

### Phase 5: Blockchain Ledger Integration – **PLANNED**

All key events anchored in Gorō/Kasumi blockchain with Falcon signatures.

---

## Setup & Installation

### Hardware (Cipher-tan & Echo-tan)

- ESP32-S3 board  
- WS2812 LED (GPIO48 primary)  
- USB CDC @ 115200 baud  
- 5V USB power  

Fallback LED pins are auto-detected where possible.

### Ayatoki Host

- Fedora x86_64 (or Ubuntu/Debian)  
- Python 3.8+  
- Rust installed  

### Software Installation

```bash
git clone https://github.com/JupitersGhost/CipherChaos.git
cd CipherChaos

python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt
````

Build PQC bindings:

```bash
pip install maturin==1.6.0
maturin develop --release
```

Flash ESP32 firmware using Thonny or esptool.

Run GUI:

```bash
python main.py
```

---

## ESP32 Firmware (Cipher-tan v2.1)

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

**Personality quips** are preserved internally for debugging but do not affect functionality.

---

## File Structure

```
Entropic Chaos / Cobra Lab/
├── main.py                 # GUI entry point (Ayatoki)
├── function.py             # Workers (Cipher/Echo), PQC manager
├── gui.py                  # UI layout + logic
├── requirements.txt
├── icon.png
├── README.md
│
├── cipher-firmware/
│   └── main.py             # Cipher-tan firmware
│
└── echo-firmware/
    └── main.py             # Echo-tan firmware
│
├── Cargo.toml
├── src/lib.rs
└── target/release/libpqcrypto_bindings.so
```

*(Optional internal tools such as local Discord logging scripts exist separately but are not part of the core system.)*

---

## Configuration

### GUI Config

* Window duration
* Keystroke capture
* Mouse entropy
* TRNG usage
* PQC enable/disable
* JSON logging path

### ESP32 Config (flash-stored)

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
* Resistant to quantum attacks

### Falcon512 (Signatures)

* NIST finalist
* Used for key provenance + audit trail signatures

Hybrid wrapping:
AES256 key XORed with Kyber shared secret + Falcon512 signature bundling.

---

## License & Attribution

Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at [http://www.apache.org/licenses/LICENSE-2.0](http://www.apache.org/licenses/LICENSE-2.0).

**Core technologies:**

* **PySide6**: Qt for Python (LGPL/Commercial dual license)
* **pqcrypto**: Kyber/Falcon implementations (CC0/Public Domain)
* **MicroPython**: Python 3 for microcontrollers (MIT)
* **Rust PyO3**: Rust bindings for Python (Apache-2.0/MIT)

**Artwork:**
Character artwork and branding were created specifically for this project.

---

## Contact

**GitHub:** [https://github.com/JupitersGhost/CipherChaos](https://github.com/JupitersGhost/CipherChaos)
**Email:** [acousticminja@gmail.com](mailto:acousticminja@gmail.com)

**Philosophy:**

> "Everyone, regardless of the scale of their network, deserves digital sovereignty."

<div align="center">
  <img src="icon.png" alt="Entropic Chaos" width="120" height="120">

**Entropic Chaos / Cobra Lab**
*Distributed Post-Quantum Entropy Generation*
Built with 🔐 by RW from Cobra Tech / CHIRASU

</div>

