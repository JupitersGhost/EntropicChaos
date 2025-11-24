# Entropic Chaos

<div align="center">
  <img src="icon.png" alt="Entropic Chaos" width="200" height="200" style="border-radius: 50%;">
  
  **Distributed Post-Quantum Entropy Generation Network**
  
  *NIST SP 800-90B Audit-Before-Wrap Architecture*
</div>

---

**Entropic Chaos** is a production-quality distributed entropy generation network across the CHIRASU home network mesh. This project showcases rigorous entropy validation through NIST SP 800-90B auditing *before* Post-Quantum Cryptography key wrapping, positioning it as a credible demonstration of next-generation cryptographic systems.

> **⚠️ WARNING:** *THIS IS A PROOF OF CONCEPT SYSTEM. DO NOT USE TO SECURE CRITICAL NETWORKS WITHOUT INDEPENDENT AUDITING.*

The network features personality-driven interaction through three character nodes:
- **Cipher-tan** (ESP32-S3): Entropy harvester with TRNG, WiFi noise, and USB jitter collection.
- **Echo-tan** (ESP32-S3): Runs same firmware as Cipher-tan, but validates entropy before sending.
- **Ayatoki** (Dell OptiPlex/Fedora): Orchestrator node coordinating the distributed system, running full NIST suite, mixing, and pre/post audits.

**Current Status:** Phase 2 Complete - Dual Audit System (Ayatoki + Echo) operational with PQC Hybrid Wrapping + 3 device entropy.

## Features

### Core Architecture
- **Audit-Before-Wrap Principle**: Entropy validated by dedicated hardware (Echo-tan) before PQC wrapping.
- **Distributed Harvesting**: Multi-node entropy generation across CHIRASU network.
- **Immutable Audit Trails**: Hardware heartbeat verification and persistent logging.
- **PQC Hybrid**: Kyber512 (KEM) + Falcon512 (Signing) protecting classical keys.

### Phase 2: Cobra Lab Dual Audit (✅ COMPLETE)
- **Ayatoki Orchestrator**: Modular Python architecture (PySide6).
- **Dual Audit System**: 
    1. **Pre-Wrap**: Ayatoki validates raw entropy using NIST SP 800-90B statistical tests (Frequency, Runs, Chi-Square).
    2. **Post-Wrap**: Ayatoki cryptographically verifies the Falcon512 signature to guarantee the provenance and integrity of the Kyber512-wrapped key.
- **Cipher-tan ESP32-S3**: Primary entropy harvester (TRNG + Jitter).
- **Echo-tan ESP32-S3**: Dedicated auditor node streaming verified entropy for the mix.
- **Tri-Node Chat**: Real-time GUI interaction between Cipher, Echo, and Ayatoki.

### Entropy Sources
- **Keystroke Timing**: Sub-microsecond timing precision from keyboard events.
- **Mouse Movement**: Micro-movements contribute to entropy pool.
- **ESP32 TRNG**: Hardware true random number generator (Cipher + Echo).
- **USB Jitter**: Inter-arrival timing entropy from USB communications.
- **Host RNG**: OS-level /dev/urandom integration.

### GUI Features (Ayatoki Node)
- **Modern Interface**: PySide6-based with Cobra Lab aesthetic (black/red/purple theme).
- **Multi-Character Status**: Distinct panels for Cipher, Echo, and Ayatoki.
- **Audit Dashboard**: Live NIST SP 800-90B compliance monitoring.
- **PQC Indicators**: Visual confirmation of Kyber/Falcon application.
- **Configurable Settings**: Brightness, timing windows, PQC algorithms.
- **Key Logging**: JSON-based storage with comprehensive metadata.

## Development Phases

### Phase 1: Cobra Lab MVP ✅ **COMPLETE**
**Goal:** Ayatoki + Cipher-tan → Entropic Chaos GUI with PQC support
**Achievements:**
- Ayatoki orchestrator running Fedora with full GUI.
- Cipher-tan ESP32-S3 responding with enhanced v2.1 firmware.
- PQC bindings (Kyber512 + Falcon512) built and functional.

### Phase 2: Echo Dual Auditor ✅ **COMPLETE**
**Goal:** Echo as dedicated NIST auditor + secondary entropy harvester
**Achievements:**
- **Echo-tan Integrated**: Validates entropy quality independent of Host.
- **Dual Audit Logic**: Pre-wrap (Host) and Post-wrap (Echo) verification.
- **Verified Streaming**: Echo streams only health-checked TRNG bytes.
- **Hybrid PQC**: Keys are wrapped (Kyber) and Signed (Falcon).
- **GUI Upgrade**: Three-character interaction panel implemented.

### Phase 3: Mitsu Network Harvester 🚧 **NEXT UP**
**Goal:** Add Mitsu laptop as remote entropy contributor
**Planned Features:**
- Small Python daemon on Mitsu-chan (systemd service).
- Entropy frames sent over Tailscale network.
- **Guardrails**: Only accept frames when Mitsu idle.
- Sensor inputs: CPU temp, load jitter, I/O timing.

### Phase 4: Dynamic Class System 📋 **PLANNED**
**Goal:** Nodes dynamically shift roles based on system state
**Class Definitions:** `harvester`, `auditor`, `validator`, `wrapper`

### Phase 5: Blockchain Ledger Integration 📋 **PLANNED**
**Goal:** Anchor all key events in Gorō + Kasumi's blockchain

**Event Structure:**
```json
{
  "event_type": "entropy_key_issued",
  "key_id": "kyber512_wrapped_abc123...",
  "entropy_sources": ["cipher", "echo", "mitsu"],
  "prewrap_audit": {"score": 78.2, "entropy_bpb": 7.1},
  "postwrap_audit": {"score": 80.5, "entropy_bpb": 7.0},
  "pqc": {"kem": "Kyber512", "sig": "Falcon512"},
  "role_assignments": {...},
  "falcon_signature": "..."
}
````

**Workflow:**

1.  Ayatoki generates key with full audit trail.
2.  Echo signs off on post-wrap verification.
3.  Event serialized and signed with Falcon512.
4.  Sent to Gorō/Kasumi blockchain RPC endpoint.
5.  Query key provenance via `/get_event key_id`.

## Setup & Installation

### Hardware Setup

**Cipher-tan/Echo-tan ESP32-S3 Boards:**

1.  **Board Selection**: Any ESP32-S3 with accessible GPIO pins (tested: ESP32-S3-DevKitC-1).
2.  **LED Configuration**:
      - **Primary**: WS2812 addressable LED on GPIO48 (auto-detected).
      - **Fallback**: Tries GPIO 8, 38, 48, 47, 21, 2 if primary fails.
      - **Manual RGB**: GPIO47 (R), GPIO21 (G), GPIO14 (B) if WS2812 unavailable.
3.  **USB Connection**: Serial communication at 115200 baud (USB CDC).
4.  **Power**: 5V via USB (powers board + LED).

**Ayatoki Orchestrator:**

  - Dell OptiPlex or similar x86\_64 system.
  - Fedora Linux (or Ubuntu/Debian).
  - Available USB port for Cipher-tan connection.
  - Optional: udev rule for persistent `/dev/ttyCIPHER` symlink.

### Software Installation (Ayatoki Orchestrator)

1.  **Clone the repository**:

    ```bash
    cd ~  # Or your preferred location
    git clone [https://github.com/JupitersGhost/CipherChaos.git](https://github.com/JupitersGhost/CipherChaos.git)
    cd CipherChaos
    ```

2.  **Create and activate virtual environment** (strongly recommended):

    ```bash
    # Create virtual environment
    python3 -m venv venv

    # Activate virtual environment
    source venv/bin/activate
    ```

3.  **Install Python dependencies**:

    ```bash
    pip install -r requirements.txt
    ```

4.  **Build PQC bindings** (required for Kyber512/Falcon512):

    ```bash
    # Ensure Rust toolchain is installed first
    # If not: curl --proto '=https' --tlsv1.2 -sSf [https://sh.rustup.rs](https://sh.rustup.rs) | sh

    # Install maturin (Rust-to-Python build tool)
    pip install maturin==1.6.0

    # Build and install the PQC bindings
    maturin develop --release
    ```

5.  **Flash Cipher-tan & Echo-tan Firmware**:

      - Use Thonny IDE or `esptool`.
      - Upload `cipher-firmware/main.py` to Cipher-tan.
      - Upload `echo-firmware/main.py` to Echo-tan.

6.  **Run Entropic Chaos GUI**:

    ```bash
    # Make sure virtual environment is activated
    source venv/bin/activate

    # Launch the GUI
    python main.py
    ```

## ESP32-S3 Firmware (Cipher-tan v2.1 Enhanced)

### Status Response Format

The `STAT?` command returns JSON with:

```json
{
  "version": "cipher-tan Enhanced v2.1-Fixed-Complete",
  "uptime_ms": 12345678,
  "keys_forged": 5,
  "wifi_entropy_bytes": 128,
  "usb_entropy_bytes": 256
}
```

### Cipher-tan Personality

The firmware features Cipher-tan's personality quips based on configured `personality_level`:

  - **Startup**: "\*\*\* cipher-tan online\! Ready to wreak cryptographic havoc\!"
  - **Key Forging**: "[\*] Key forged in the fires of chaos\!"
  - **Errors**: "\\m/ Error handled like a boss\! cipher-tan recovers\!"

## File Structure

```
Entropic Chaos / Cobra Lab/
├── main.py                 # Main GUI application entry point
├── function.py             # Logic, Workers (Cipher/Echo), PQC Manager
├── gui.py                  # UI Layout, Styles, Widgets
├── cipher-bot.py           # Discord bot for Cipher-tan monitoring
├── requirements.txt        # Python dependencies
├── icon.png                # Main Cobra Lab logo
├── README.md               # This file
│
├── cipher-firmware/
│   └── main.py             # ESP32-S3 firmware for Cipher-tan (Harvester)
│
└── echo-firmware/
    └── main.py             # ESP32-S3 firmware for Echo-tan (Auditor)
│
├── Cargo.toml              # Rust PQC bindings configuration
├── src/
│   └── lib.rs              # Rust PQC bindings implementation
│
└── target/                 # Rust build artifacts (auto-generated)
    └── release/
        └── libpqcrypto_bindings.so  # Compiled PQC bindings
```

## Configuration

### GUI Configuration (Ayatoki Orchestrator)

  - **Entropy Collection**: Window Duration, Keystroke Capture, Mouse Entropy, Host RNG, ESP32 TRNG.
  - **PQC Settings**: Enable PQC, Kyber512 KEM, Falcon512 Signatures, Auto-save Keys.
  - **Logging**: Key Log Path, JSON Log Format.

### ESP32 Configuration

The firmware stores configuration in **flash memory** at `cipher_enhanced_cfg.json`:

```json
{
  "led_pin": 48,
  "brightness": 1.0,
  "personality_level": 0.3,
  "debug_mode": false,
  "led_type": "ws2812"
}
```

## Post-Quantum Cryptography

**Kyber512 KEM (Key Encapsulation Mechanism):**

  - NIST FIPS 203 standardized (originally Kyber).
  - Lattice-based cryptography resistant to quantum attacks.
  - Hybrid approach: Classical AES256 key XORed with Kyber shared secret.

**Falcon512 (Digital Signatures):**

  - NIST post-quantum signature finalist.
  - Used for key authentication and audit trail signing.

## License & Attribution

**License:** MIT License

**This project uses:**

  - **PySide6**: Qt for Python (LGPL/Commercial dual license)
  - **pqcrypto**: Post-quantum cryptography implementations (Public Domain / CC0)
  - **MicroPython**: Python 3 implementation for microcontrollers (MIT)
  - **PyO3**: Rust-Python bindings (Apache-2.0 / MIT dual license)
  - **discord.py**: Discord API wrapper (MIT)

**Character & Art:**

  - Cipher-tan, Echo-tan, and Cobra Lab branding are original creations by me.
  - Icons created via Gemini + Grok with specific instructions on each character and their designs. All icons and characters were created before generation.
  - Character artwork represents the chaotic and precise nature of cryptographic entropy.

**Acknowledgments:**

  - NIST for standardization efforts in post-quantum cryptography.
  - pqcrypto maintainers for production-quality implementations.
  - ESP32 and MicroPython communities for hardware support.
  - Discord developer community for bot frameworks.

## Contact & Community

**GitHub**: [https://github.com/JupitersGhost/CipherChaos](https://github.com/JupitersGhost/CipherChaos)

**Discord**: [https://discord.gg/dabcxHkFxG](https://discord.gg/dabcxHkFxG)
*\#Where my homelab network lives plus integration with Entropic Chaos. Roadmap eventually will include many of these devices as sources of entropy.*

**Email**: acousticminja@gmail.com

**Documentation**: See `project_phases.txt` for detailed development roadmap.

**Hardware**: ESP32-S3 development boards, commodity x86\_64 servers, standard networking gear.

**Philosophy**: "Everyone, regardless of the scale and scope of their network, should be able to have digital sovereignty."

-----

\<div align="center"\>
\<img src="icon.png" alt="Entropic Chaos" width="120" height="120"\>

**Entropic Chaos / Cobra Lab**

*Distributed Post-Quantum Entropy Generation*

Built with 🔐 by RW from Cobra Tech/CHIRASU

Powered by ESP32-S3 · Fedora Linux · Rust · Python · Discord

\</div\>

```
```
