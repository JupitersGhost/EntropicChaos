"""
Entropic Chaos - GUI Module
All GUI components, main window, panels, and styling
Phase 3: Mitsu-chan Network Forge Integration
"""

import os
import random
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import Qt, QObject, QThread, Signal, Slot, QTimer, QSize, QPoint, QEvent
from PySide6.QtGui import (QIcon, QAction, QPixmap, QColor, QTextCursor, QPainter, 
                          QBrush, QLinearGradient, QPen, QFont, QPalette)
from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QComboBox, QHBoxLayout, QVBoxLayout,
    QCheckBox, QDoubleSpinBox, QFileDialog, QTextEdit, QGroupBox, QLineEdit,
    QMessageBox, QSystemTrayIcon, QMenu, QSlider, QProgressBar, QFrame, QScrollArea,
    QSizePolicy, QMainWindow, QStatusBar, QTabWidget
)

from serial.tools import list_ports

# Import from function module
from function import (
    CIPHER_COLORS, DEFAULT_DIR, KEYS_DIR, LOGS_DIR, AUDIT_DIR, DEFAULT_LOG,
    PQC_AVAILABLE, MLKEM_AVAILABLE,
    _cc_get_icon, _cc_get_pixmap,
    EntropyVisualization, NetworkManager, EchoWorker, CIPHERTANWorker,
    start_ayatoki_ingest_server # Phase 3 Import
)

class CIPHERTANMainWindow(QMainWindow):
    """Main window with Phase 3 Mitsu integration and four-character interface"""
    
    def __init__(self):
        super().__init__()
        self.last_keypress_time = 0.0
        try:
            self.setWindowIcon(_cc_get_icon())
        except Exception:
            pass
        
        self.setMouseTracking(True)
        try:
            QApplication.instance().installEventFilter(self)
        except Exception:
            pass
        
        self.setAttribute(Qt.WA_AcceptTouchEvents, False)
        
        # State
        self.network_manager = NetworkManager()
        self.worker = None
        self.worker_thread = None
        self.echo_worker = None  # Phase 2
        self.echo_worker_thread = None  # Phase 2
        
        # UI state
        self.keys_generated = 0
        self.entropy_level = 0.0
        self.keystroke_rate = 0.0
        self.rgb_color = {'r': 196, 'g': 0, 'b': 255}
        self.audit_score = 95.0
        
        # Phase 2: Echo state
        self.echo_audit_score = 0.0
        self.echo_connected = False
        
        # Phase 3: Mitsu state
        self.mitsu_connected = False
        self.mitsu_bytes_received = 0
        self.mitsu_last_seq = 0
        
        # ESP32 state
        self.wifi_entropy_bytes = 0
        self.usb_entropy_bytes = 0
        self.wifi_ap_count = 0
        self.wifi_joined = False
        self.esp_version = "Unknown"
        self.trng_streaming = False
        
        # Ayatoki personality quips
        self.ayatoki_quips = [
            "El Psy Kongroo! See? Chaos theory wins again.",
            "Perfect! Another proof that math can weaponize randomness.",
            "Senpai, watch this - I'm about to make entropy my *thesis topic*.",
            "The math proof of emotion? Still searching. But this key? Solved.",
            "One explosion closer to enlightenment. Science demands sacrifice!",
            "Efficiency achieved through controlled chaos. Beautiful, isn't it?",
            "My entropy charm is glowing. Must be a good key.",
            "Kikku would be jealous of this innovation. *smirks*",
            "Blockchain ledger updated. Another mooncake minted!",
            "The stable kernel to Cipher's wild overclock - that's us.",
            "Sensor data nominal. Proceeding with experimental protocol.",
            "This is what happens when logic serves wonder, Senpai.",
            "Phase 3 operational. All nodes reporting nominal!",
            "Dual audit complete. The theorem holds. Q.E.D.",
            "My lab, my rules: test everything, trust the numbers."
        ]
        
        self.init_ui()
        self.setup_worker()
        self.setup_echo_worker()  # Phase 2
        self.setup_tray()
        self.connect_signals()
        self.refresh_serial_ports()
        
        self.setMinimumSize(1000, 700)
        self.resize(1200, 900)
    
    def eventFilter(self, obj, event):
        if event.type() == QEvent.MouseMove and self.worker:
            try:
                pos = getattr(event, "globalPosition", None)
                if callable(pos):
                    gp = pos()
                    x, y = int(gp.x()), int(gp.y())
                else:
                    p = getattr(event, "globalPos", lambda: None)()
                    if p is not None:
                        x, y = int(p.x()), int(p.y())
                    else:
                        return False
                
                if hasattr(self.worker, "add_mouse_entropy"):
                    self.worker.add_mouse_entropy(x, y)
            except Exception:
                pass
        return False
    
    def init_ui(self):
        """Initialize UI with Phase 3 enhancements"""
        self.setWindowTitle("Entropic Chaos - Cobra Lab Phase 3 (Mitsu Integration)")
        self.setStyleSheet(self.get_stylesheet())
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Header
        header = self.create_header()
        main_layout.addWidget(header)
        
        # Content in scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        
        # Main panels
        panels_layout = QHBoxLayout()
        
        # Left column
        left_column = QVBoxLayout()
        left_column.addWidget(self.create_cipher_connection_panel())
        left_column.addWidget(self.create_echo_connection_panel())  # Phase 2
        left_column.addWidget(self.create_control_panel())
        
        # Right column  
        right_column = QVBoxLayout()
        right_column.addWidget(self.create_status_panel())
        right_column.addWidget(self.create_dual_audit_panel())  # Phase 2
        right_column.addWidget(self.create_mitsu_network_panel())  # Phase 3: Mitsu replaces old network
        
        panels_layout.addLayout(left_column, 1)
        panels_layout.addLayout(right_column, 1)
        
        scroll_layout.addLayout(panels_layout)
        
        # Visualization
        scroll_layout.addWidget(self.create_visualization_panel())
        
        # Phase 3: Four-character quip panel
        scroll_layout.addWidget(self.create_quad_quip_panel())
        
        scroll_layout.addWidget(self.create_log_panel())
        
        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area, 1)
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Entropic Chaos - Cobra Lab Phase 3 System Ready")
    
    def create_header(self):
        """Create header with Phase 3 branding"""
        header = QFrame()
        header.setFixedHeight(88)
        header.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 {CIPHER_COLORS['accent']}, 
                    stop:0.33 {CIPHER_COLORS['accent2']},
                    stop:0.66 {CIPHER_COLORS['accent3']},
                    stop:1 {CIPHER_COLORS['accent4']});
                border-radius: 15px;
            }}
        """)
        
        layout = QHBoxLayout(header)
        
        # Avatar
        avatar = QLabel()
        icon_path = Path(__file__).parent / "icon.png"
        if icon_path.exists():
            avatar.setPixmap(QPixmap(str(icon_path)).scaled(60, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            avatar.setText("CL")
        avatar.setStyleSheet("font-size: 36px; color: white; background: transparent;")
        avatar.setFixedSize(60, 60)
        avatar.setAlignment(Qt.AlignCenter)
        
        # Title
        title_widget = QWidget()
        title_widget.setStyleSheet("background: transparent;")
        title_layout = QVBoxLayout(title_widget)
        
        title = QLabel("Entropic Chaos - Cobra Lab Phase 3 - Node: Ayatoki")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: white;")
        
        subtitle = QLabel("Cipher - Echo - Ayatoki - Mitsu | Quad-Source PQC Entropy Forge")
        subtitle.setStyleSheet("font-size: 12px; color: rgba(255,255,255,0.8);")
        
        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)
        
        layout.addWidget(avatar)
        layout.addWidget(title_widget, 1)
        layout.addStretch()
        
        return header
    
    def create_cipher_connection_panel(self):
        """Cipher-tan connection panel"""
        panel = QGroupBox("Cipher-tan Hardware Connection")
        panel.setStyleSheet(f"""
            QGroupBox {{
                border: 3px solid {CIPHER_COLORS['accent2']};
                border-radius: 12px;
                margin: 24px 8px 12px 8px;
                padding-top: 20px;
                background-color: #1a0a1a;
            }}
            QGroupBox::title {{
                color: {CIPHER_COLORS['accent2']};
                font-weight: bold;
                font-size: 11pt;
            }}
        """)
        
        layout = QVBoxLayout(panel)
        
        # Port selection
        port_layout = QHBoxLayout()
        port_layout.addWidget(QLabel("Port:"))
        
        self.cipher_port_combo = QComboBox()
        self.cipher_port_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        port_layout.addWidget(self.cipher_port_combo, 2)
        
        self.refresh_cipher_ports_btn = QPushButton("Refresh")
        self.refresh_cipher_ports_btn.clicked.connect(self.refresh_serial_ports)
        port_layout.addWidget(self.refresh_cipher_ports_btn)
        
        layout.addLayout(port_layout)
        
        # Manual port
        manual_layout = QHBoxLayout()
        manual_layout.addWidget(QLabel("Manual:"))
        self.cipher_manual_port_edit = QLineEdit()
        self.cipher_manual_port_edit.setPlaceholderText("/dev/ttyCIPHER or COM8")
        manual_layout.addWidget(self.cipher_manual_port_edit, 2)
        layout.addLayout(manual_layout)
        
        # Connection buttons
        conn_layout = QHBoxLayout()
        self.cipher_connect_btn = QPushButton("Connect Cipher-tan")
        self.cipher_disconnect_btn = QPushButton("Disconnect")
        self.cipher_disconnect_btn.setEnabled(False)
        
        conn_layout.addWidget(self.cipher_connect_btn)
        conn_layout.addWidget(self.cipher_disconnect_btn)
        layout.addLayout(conn_layout)
        
        # Status
        self.cipher_connection_status = QLabel("Disconnected")
        self.cipher_connection_status.setStyleSheet(f"color: {CIPHER_COLORS['error']};")
        layout.addWidget(self.cipher_connection_status)
        
        return panel
    
    def create_echo_connection_panel(self):
        """Phase 2: Echo-tan connection panel"""
        panel = QGroupBox("Echo-tan Auditor Connection")
        panel.setStyleSheet(f"""
            QGroupBox {{
                border: 3px solid {CIPHER_COLORS['accent3']};
                border-radius: 12px;
                margin: 24px 8px 12px 8px;
                padding-top: 20px;
                background-color: #0a1a1f;
            }}
            QGroupBox::title {{
                color: {CIPHER_COLORS['accent3']};
                font-weight: bold;
                font-size: 11pt;
            }}
        """)
        
        layout = QVBoxLayout(panel)
        
        # Port selection
        port_layout = QHBoxLayout()
        port_layout.addWidget(QLabel("Port:"))
        
        self.echo_port_combo = QComboBox()
        self.echo_port_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        port_layout.addWidget(self.echo_port_combo, 2)
        
        self.refresh_echo_ports_btn = QPushButton("Refresh")
        self.refresh_echo_ports_btn.clicked.connect(self.refresh_serial_ports)
        port_layout.addWidget(self.refresh_echo_ports_btn)
        
        layout.addLayout(port_layout)
        
        # Manual port
        manual_layout = QHBoxLayout()
        manual_layout.addWidget(QLabel("Manual:"))
        self.echo_manual_port_edit = QLineEdit()
        self.echo_manual_port_edit.setPlaceholderText("/dev/ttyECHO or COM9")
        manual_layout.addWidget(self.echo_manual_port_edit, 2)
        layout.addLayout(manual_layout)
        
        # Connection buttons
        conn_layout = QHBoxLayout()
        self.echo_connect_btn = QPushButton("Connect Echo-tan")
        self.echo_disconnect_btn = QPushButton("Disconnect")
        self.echo_disconnect_btn.setEnabled(False)
        
        conn_layout.addWidget(self.echo_connect_btn)
        conn_layout.addWidget(self.echo_disconnect_btn)
        layout.addLayout(conn_layout)
        
        # Status
        self.echo_connection_status = QLabel("Disconnected")
        self.echo_connection_status.setStyleSheet(f"color: {CIPHER_COLORS['error']};")
        layout.addWidget(self.echo_connection_status)
        
        return panel
    
    def create_control_panel(self):
        """Enhanced control panel with Phase 3 features"""
        panel = QGroupBox("Chaos Control (Ayatoki)")
        panel.setStyleSheet(f"""
            QGroupBox {{
                border: 3px solid {CIPHER_COLORS['accent']};
                border-radius: 12px;
                margin: 24px 8px 12px 8px;
                padding-top: 20px;
                background-color: {CIPHER_COLORS['panel']};
            }}
            QGroupBox::title {{
                color: {CIPHER_COLORS['accent']};
                font-weight: bold;
                font-size: 11pt;
            }}
        """)
        
        layout = QVBoxLayout(panel)
        
        # Main buttons
        btn_layout = QHBoxLayout()
        self.start_btn = QPushButton("Start Chaos Storm")
        self.stop_btn = QPushButton("Stop Chaos")
        self.stop_btn.setEnabled(False)
        
        btn_layout.addWidget(self.start_btn)
        btn_layout.addWidget(self.stop_btn)
        layout.addLayout(btn_layout)
        
        # TRNG Streaming
        trng_group = QFrame()
        trng_group.setStyleSheet(f"border: 1px solid {CIPHER_COLORS['muted']}; border-radius: 6px; padding: 8px;")
        trng_layout = QVBoxLayout(trng_group)
        
        trng_label = QLabel("ESP32 TRNG Streaming:")
        trng_label.setStyleSheet(f"font-weight: bold; color: {CIPHER_COLORS['accent2']};")
        trng_layout.addWidget(trng_label)
        
        trng_controls = QHBoxLayout()
        self.trng_rate_spin = QDoubleSpinBox()
        self.trng_rate_spin.setRange(1.0, 50.0)
        self.trng_rate_spin.setValue(10.0)
        self.trng_rate_spin.setSuffix(" Hz")
        
        self.trng_start_btn = QPushButton("Start TRNG")
        self.trng_stop_btn = QPushButton("Stop TRNG")
        self.trng_stop_btn.setEnabled(False)
        
        trng_controls.addWidget(QLabel("Rate:"))
        trng_controls.addWidget(self.trng_rate_spin)
        trng_controls.addWidget(self.trng_start_btn)
        trng_controls.addWidget(self.trng_stop_btn)
        trng_layout.addLayout(trng_controls)
        
        layout.addWidget(trng_group)
        
        # Settings
        settings_layout = QVBoxLayout()
        
        window_layout = QHBoxLayout()
        window_layout.addWidget(QLabel("Window (s):"))
        self.window_spin = QDoubleSpinBox()
        self.window_spin.setRange(0.2, 30.0)
        self.window_spin.setSingleStep(0.1) 
        self.window_spin.setValue(2.0)
        window_layout.addWidget(self.window_spin)
        settings_layout.addLayout(window_layout)
        
        brightness_layout = QHBoxLayout()
        brightness_layout.addWidget(QLabel("LED Brightness:"))
        self.brightness_slider = QSlider(Qt.Horizontal)
        self.brightness_slider.setRange(1, 100)
        self.brightness_slider.setValue(100)
        self.brightness_label = QLabel("100%")
        self.brightness_label.setMinimumWidth(40)
        brightness_layout.addWidget(self.brightness_slider, 2)
        brightness_layout.addWidget(self.brightness_label)
        settings_layout.addLayout(brightness_layout)
        
        layout.addLayout(settings_layout)
        
        # Checkboxes
        self.realtime_cb = QCheckBox("Realtime keys")
        self.host_rng_cb = QCheckBox("Include host RNG")
        self.host_rng_cb.setChecked(True)
        self.mouse_rng_cb = QCheckBox("Include Mouse Entropy")
        self.mouse_rng_cb.setChecked(True)
        self.esp_trng_cb = QCheckBox("Include ESP32 TRNG")
        self.esp_trng_cb.setChecked(True)
        self.lights_cb = QCheckBox("RGB lights")
        self.lights_cb.setChecked(True)
        
        # PQC Controls
        self.pqc_cb = QCheckBox("Enable PQC Key Wrapping")
        self.pqc_cb.setChecked(False)
        self.pqc_cb.setStyleSheet(f"color: {CIPHER_COLORS['pqc']}; font-weight: bold;")
        if not PQC_AVAILABLE:
            self.pqc_cb.setEnabled(False)
            self.pqc_cb.setText("Enable PQC Key Wrapping (Not Available)")
        
        layout.addWidget(self.realtime_cb)
        layout.addWidget(self.host_rng_cb)
        layout.addWidget(self.mouse_rng_cb)
        layout.addWidget(self.esp_trng_cb) 
        layout.addWidget(self.lights_cb)
        layout.addWidget(self.pqc_cb)
        
        # PQC algorithm controls
        pqc_status_layout = QHBoxLayout()
        self.kyber_cb = QCheckBox("Kyber512 KEM")
        self.kyber_cb.setChecked(True)
        self.kyber_cb.setEnabled(PQC_AVAILABLE)
        self.kyber_cb.setStyleSheet(f"color: {CIPHER_COLORS['pqc']};")

        self.falcon_cb = QCheckBox("Falcon512 Signatures") 
        self.falcon_cb.setChecked(True)
        self.falcon_cb.setEnabled(PQC_AVAILABLE)
        self.falcon_cb.setStyleSheet(f"color: {CIPHER_COLORS['pqc']};")

        pqc_status_layout.addWidget(self.kyber_cb)
        pqc_status_layout.addWidget(self.falcon_cb)
        layout.addLayout(pqc_status_layout)
        
        # Log file
        log_layout = QVBoxLayout()
        log_layout.addWidget(QLabel("Key Log File:"))
        log_file_layout = QHBoxLayout()
        self.log_path_edit = QLineEdit(str(DEFAULT_LOG))
        self.browse_log_btn = QPushButton("Browse...")
        log_file_layout.addWidget(self.log_path_edit, 2)
        log_file_layout.addWidget(self.browse_log_btn)
        log_layout.addLayout(log_file_layout)
        layout.addLayout(log_layout)
        
        return panel
    
    def create_status_panel(self):
        """Enhanced status panel with dual device tracking"""
        panel = QGroupBox("Live Status (Ayatoki Orchestrator)")
        layout = QVBoxLayout(panel)
        
        self.keys_label = QLabel("Keys Generated: 0")
        self.key_type_label = QLabel("Key Type: Classical AES256")
        self.key_type_label.setStyleSheet(f"color: {CIPHER_COLORS['text']};")
        self.entropy_label = QLabel("Entropy Level: 0.0%")
        self.keystroke_label = QLabel("Keystroke Rate: 0.0/s")
        self.rgb_label = QLabel("RGB: (196, 0, 255)")
        
        layout.addWidget(self.keys_label)
        layout.addWidget(self.key_type_label)
        layout.addWidget(self.entropy_label)
        layout.addWidget(self.keystroke_label)
        layout.addWidget(self.rgb_label)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet(f"color: {CIPHER_COLORS['muted']};")
        layout.addWidget(separator)
        
        # Cipher ESP32 status
        cipher_label = QLabel("Cipher-tan ESP32:")
        cipher_label.setStyleSheet(f"font-weight: bold; color: {CIPHER_COLORS['accent2']};")
        layout.addWidget(cipher_label)
        
        self.cipher_version_label = QLabel("Version: Unknown")
        self.cipher_wifi_entropy_label = QLabel("WiFi Entropy: 0 bytes")
        self.cipher_usb_entropy_label = QLabel("USB Jitter: 0 bytes")
        
        layout.addWidget(self.cipher_version_label)
        layout.addWidget(self.cipher_wifi_entropy_label)
        layout.addWidget(self.cipher_usb_entropy_label)
        
        # Separator
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.HLine)
        separator2.setFrameShadow(QFrame.Sunken)
        separator2.setStyleSheet(f"color: {CIPHER_COLORS['muted']};")
        layout.addWidget(separator2)
        
        # Phase 2: Echo ESP32 status
        echo_label = QLabel("Echo-tan ESP32:")
        echo_label.setStyleSheet(f"font-weight: bold; color: {CIPHER_COLORS['accent3']};")
        layout.addWidget(echo_label)
        
        self.echo_version_label = QLabel("Version: Unknown")
        self.echo_health_label = QLabel("Health Status: OK")
        self.echo_audited_label = QLabel("Keys Audited: 0")
        
        layout.addWidget(self.echo_version_label)
        layout.addWidget(self.echo_health_label)
        layout.addWidget(self.echo_audited_label)
        
        # Separator
        separator3 = QFrame()
        separator3.setFrameShape(QFrame.HLine)
        separator3.setFrameShadow(QFrame.Sunken)
        separator3.setStyleSheet(f"color: {CIPHER_COLORS['muted']};")
        layout.addWidget(separator3)
        
        # Progress bars
        self.entropy_progress = QProgressBar()
        self.entropy_progress.setStyleSheet(f"""
            QProgressBar {{
                border: 2px solid {CIPHER_COLORS['muted']};
                border-radius: 8px;
                text-align: center;
                background-color: {CIPHER_COLORS['bg']};
            }}
            QProgressBar::chunk {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {CIPHER_COLORS['accent']}, stop:1 {CIPHER_COLORS['accent2']});
                border-radius: 6px;
            }}
        """)
        layout.addWidget(QLabel("Entropy Pool:"))
        layout.addWidget(self.entropy_progress)
        
        self.audit_progress = QProgressBar()
        self.audit_progress.setStyleSheet(f"""
            QProgressBar {{
                border: 2px solid {CIPHER_COLORS['muted']};
                border-radius: 8px;
                text-align: center;
                background-color: {CIPHER_COLORS['bg']};
            }}
            QProgressBar::chunk {{
                background-color: {CIPHER_COLORS['success']};
                border-radius: 6px;
            }}
        """)
        layout.addWidget(QLabel("Quality Score:"))
        layout.addWidget(self.audit_progress)
        
        return panel
    
    def create_dual_audit_panel(self):
        """Phase 2: Dual audit display (Ayatoki + Echo)"""
        panel = QGroupBox("Dual Entropy Audit")
        layout = QVBoxLayout(panel)
        
        # Tab widget for dual audits
        tabs = QTabWidget()
        
        # Ayatoki Pre-wrap Audit
        ayatoki_tab = QWidget()
        ayatoki_layout = QVBoxLayout(ayatoki_tab)
        
        ayatoki_header = QLabel("Ayatoki Pre-Wrap Validation")
        ayatoki_header.setStyleSheet(f"font-weight: bold; color: {CIPHER_COLORS['accent']}; font-size: 12pt;")
        ayatoki_layout.addWidget(ayatoki_header)
        
        score_layout = QHBoxLayout()
        score_layout.addWidget(QLabel("Overall Score:"))
        self.ayatoki_audit_score_label = QLabel("95.0%")
        self.ayatoki_audit_score_label.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {CIPHER_COLORS['success']};")
        score_layout.addWidget(self.ayatoki_audit_score_label)
        ayatoki_layout.addLayout(score_layout)
        
        self.ayatoki_frequency_test_label = QLabel("Frequency Test: Passed")
        self.ayatoki_runs_test_label = QLabel("Runs Test: Passed")
        self.ayatoki_chi_square_label = QLabel("Chi-Square: Passed")
        self.ayatoki_entropy_rate_label = QLabel("Entropy Rate: 7.8 bits/byte")
        
        ayatoki_layout.addWidget(self.ayatoki_frequency_test_label)
        ayatoki_layout.addWidget(self.ayatoki_runs_test_label)
        ayatoki_layout.addWidget(self.ayatoki_chi_square_label)
        ayatoki_layout.addWidget(self.ayatoki_entropy_rate_label)
        
        self.ayatoki_pqc_ready_label = QLabel("PQC Ready: No")
        self.ayatoki_pqc_ready_label.setStyleSheet(f"color: {CIPHER_COLORS['pqc']}; font-weight: bold;")
        ayatoki_layout.addWidget(self.ayatoki_pqc_ready_label)
        # Post-wrap summary (kept with pre-wrap tests for researcher clarity)
        self.ayatoki_last_wrap_label = QLabel("Last Key Wrap: Classical only (no PQC layer yet)")
        self.ayatoki_wrap_algorithm_label = QLabel("Wrap Algorithm: --")
        ayatoki_layout.addWidget(self.ayatoki_last_wrap_label)
        ayatoki_layout.addWidget(self.ayatoki_wrap_algorithm_label)
        
        tabs.addTab(ayatoki_tab, "Ayatoki Pre-Wrap")
        
        # Echo Post-wrap Verification (Ayatoki's signature check)
        echo_tab = QWidget()
        echo_layout = QVBoxLayout(echo_tab)
        
        echo_header = QLabel("Post-Wrap Verification (Falcon Signature)")
        echo_header.setStyleSheet(f"font-weight: bold; color: {CIPHER_COLORS['accent3']}; font-size: 12pt;")
        echo_layout.addWidget(echo_header)
        
        echo_desc = QLabel("Ayatoki verifies Falcon signatures after key wrapping")
        echo_desc.setStyleSheet(f"color: {CIPHER_COLORS['muted']}; font-size: 9pt; font-style: italic;")
        echo_layout.addWidget(echo_desc)
        
        echo_score_layout = QHBoxLayout()
        echo_score_layout.addWidget(QLabel("Signature Status:"))
        self.echo_audit_score_label = QLabel("Waiting for keys...")
        self.echo_audit_score_label.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {CIPHER_COLORS['accent3']};")
        echo_score_layout.addWidget(self.echo_audit_score_label)
        echo_layout.addLayout(echo_score_layout)
        
        self.echo_health_status_label = QLabel("Status: No keys generated yet")
        self.echo_verdict_label = QLabel("Verdict: Awaiting first key")
        
        echo_layout.addWidget(self.echo_health_status_label)
        echo_layout.addWidget(self.echo_verdict_label)
        
        # Note about Echo's internal health
        echo_note = QLabel("Note: Echo's internal health checks (RCT/APT) are shown in the Status panel above")
        echo_note.setStyleSheet(f"color: {CIPHER_COLORS['muted']}; font-size: 8pt; font-style: italic; margin-top: 10px;")
        echo_layout.addWidget(echo_note)
        
        tabs.addTab(echo_tab, "Post-Wrap Verification")
        
        layout.addWidget(tabs)
        
        return panel
    
    def create_mitsu_network_panel(self):
        """Phase 3: Mitsu-chan Network Forge panel (replaces old network panel)"""
        panel = QGroupBox("Mitsu-chan Network Forge")
        panel.setStyleSheet(f"""
            QGroupBox {{
                border: 3px solid {CIPHER_COLORS['accent4']};
                border-radius: 12px;
                margin: 24px 8px 12px 8px;
                padding-top: 20px;
                background-color: #1f0a1a;
            }}
            QGroupBox::title {{
                color: {CIPHER_COLORS['accent4']};
                font-weight: bold;
                font-size: 11pt;
            }}
        """)
        
        layout = QVBoxLayout(panel)
        
        # Mitsu avatar and status header
        header_layout = QHBoxLayout()
        
        mitsu_avatar = QLabel()
        mitsu_avatar.setPixmap(_cc_get_pixmap(48, "mitsu"))
        mitsu_avatar.setFixedSize(48, 48)
        header_layout.addWidget(mitsu_avatar)
        
        header_info = QVBoxLayout()
        self.mitsu_connection_status = QLabel("OFFLINE - Waiting for uplink...")
        self.mitsu_connection_status.setStyleSheet(f"color: {CIPHER_COLORS['warning']}; font-weight: bold;")
        self.mitsu_endpoint_label = QLabel("Endpoint: http://0.0.0.0:8000/ingest")
        self.mitsu_endpoint_label.setStyleSheet(f"color: {CIPHER_COLORS['muted']}; font-size: 9pt;")
        header_info.addWidget(self.mitsu_connection_status)
        header_info.addWidget(self.mitsu_endpoint_label)
        header_layout.addLayout(header_info, 1)
        
        layout.addLayout(header_layout)
        
        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f"color: {CIPHER_COLORS['accent4']};")
        layout.addWidget(sep)
        
        # Stats grid
        stats_layout = QVBoxLayout()
        
        self.mitsu_bytes_label = QLabel("Bytes Received: 0")
        self.mitsu_bytes_label.setStyleSheet(f"color: {CIPHER_COLORS['text']};")
        
        self.mitsu_seq_label = QLabel("Last Sequence: --")
        self.mitsu_seq_label.setStyleSheet(f"color: {CIPHER_COLORS['text']};")
        
        self.mitsu_source_label = QLabel("Last Source: --")
        self.mitsu_source_label.setStyleSheet(f"color: {CIPHER_COLORS['text']};")
        
        self.mitsu_quality_label = QLabel("Health: Awaiting data...")
        self.mitsu_quality_label.setStyleSheet(f"color: {CIPHER_COLORS['muted']};")
        
        stats_layout.addWidget(self.mitsu_bytes_label)
        stats_layout.addWidget(self.mitsu_seq_label)
        stats_layout.addWidget(self.mitsu_source_label)
        stats_layout.addWidget(self.mitsu_quality_label)
        
        layout.addLayout(stats_layout)
        
        # Separator
        sep2 = QFrame()
        sep2.setFrameShape(QFrame.HLine)
        sep2.setStyleSheet(f"color: {CIPHER_COLORS['muted']};")
        layout.addWidget(sep2)
        
        # CobraMesh status (legacy)
        mesh_label = QLabel("CobraMesh Status:")
        mesh_label.setStyleSheet(f"font-weight: bold; color: {CIPHER_COLORS['muted']};")
        layout.addWidget(mesh_label)
        
        self.headscale_status = QLabel("Headscale: Checking...")
        self.mesh_peers_label = QLabel("Mesh Peers: 0")
        self.uplink_status = QLabel("Tailscale: Disconnected")
        
        layout.addWidget(self.headscale_status)
        layout.addWidget(self.mesh_peers_label)
        layout.addWidget(self.uplink_status)
        
        # Manual command
        cmd_layout = QVBoxLayout()
        cmd_layout.addWidget(QLabel("Manual ESP32 Command:"))
        cmd_input_layout = QHBoxLayout()
        self.cmd_input = QLineEdit()
        self.cmd_input.setPlaceholderText("e.g., VER?, PIN:48, BRI:0.5")
        self.send_cmd_btn = QPushButton("Send to Cipher")
        self.send_echo_cmd_btn = QPushButton("Send to Echo")  # Phase 2
        cmd_input_layout.addWidget(self.cmd_input, 2)
        cmd_input_layout.addWidget(self.send_cmd_btn)
        cmd_input_layout.addWidget(self.send_echo_cmd_btn)
        cmd_layout.addLayout(cmd_input_layout)
        layout.addLayout(cmd_layout)
        
        return panel
    
    def create_visualization_panel(self):
        """Entropy visualization"""
        panel = QGroupBox("Entropy Visualization")
        layout = QVBoxLayout(panel)
        
        self.viz_widget = EntropyVisualization()
        self.viz_widget.setMinimumHeight(150)
        layout.addWidget(self.viz_widget)
        
        return panel
    
    def create_quad_quip_panel(self):
        """Phase 3: Four-character quip display (Cipher, Echo, Ayatoki, Mitsu)"""
        panel = QGroupBox("Character Status")
        layout = QVBoxLayout(panel)
        
        # Top row: Cipher + Echo
        top_row = QHBoxLayout()
        
        # Cipher-tan quips
        cipher_group = QFrame()
        cipher_group.setStyleSheet(f"border: 2px solid {CIPHER_COLORS['accent2']}; border-radius: 8px; padding: 8px; background-color: #1a0a1a;")
        cipher_layout = QHBoxLayout(cipher_group)
        
        cipher_avatar = QLabel()
        cipher_avatar.setPixmap(_cc_get_pixmap(48, "cipher"))
        cipher_avatar.setFixedSize(48, 48)
        cipher_layout.addWidget(cipher_avatar)
        
        self.cipher_quip_display = QTextEdit()
        self.cipher_quip_display.setReadOnly(True)
        self.cipher_quip_display.setMaximumHeight(70)
        self.cipher_quip_display.setPlaceholderText("Cipher-tan will sass you here...")
        cipher_layout.addWidget(self.cipher_quip_display, 1)
        
        top_row.addWidget(cipher_group)
        
        # Echo-tan quips
        echo_group = QFrame()
        echo_group.setStyleSheet(f"border: 2px solid {CIPHER_COLORS['accent3']}; border-radius: 8px; padding: 8px; background-color: #0a1a1f;")
        echo_layout = QHBoxLayout(echo_group)
        
        echo_avatar = QLabel()
        echo_avatar.setPixmap(_cc_get_pixmap(48, "echo"))
        echo_avatar.setFixedSize(48, 48)
        echo_layout.addWidget(echo_avatar)
        
        self.echo_quip_display = QTextEdit()
        self.echo_quip_display.setReadOnly(True)
        self.echo_quip_display.setMaximumHeight(70)
        self.echo_quip_display.setPlaceholderText("Echo-tan will whisper here...")
        echo_layout.addWidget(self.echo_quip_display, 1)
        
        top_row.addWidget(echo_group)
        layout.addLayout(top_row)
        
        # Bottom row: Ayatoki + Mitsu
        bottom_row = QHBoxLayout()
        
        # Ayatoki quips
        ayatoki_group = QFrame()
        ayatoki_group.setStyleSheet(f"border: 2px solid {CIPHER_COLORS['accent']}; border-radius: 8px; padding: 8px; background-color: {CIPHER_COLORS['panel']};")
        ayatoki_layout = QHBoxLayout(ayatoki_group)
        
        ayatoki_avatar = QLabel()
        ayatoki_avatar.setPixmap(_cc_get_pixmap(48, "ayatoki"))
        ayatoki_avatar.setFixedSize(48, 48)
        ayatoki_layout.addWidget(ayatoki_avatar)
        
        self.ayatoki_quip_display = QTextEdit()
        self.ayatoki_quip_display.setReadOnly(True)
        self.ayatoki_quip_display.setMaximumHeight(70)
        self.ayatoki_quip_display.setPlaceholderText("Ayatoki's lab notes appear here...")
        ayatoki_layout.addWidget(self.ayatoki_quip_display, 1)
        
        bottom_row.addWidget(ayatoki_group)
        
        # Mitsu quips (Phase 3)
        mitsu_group = QFrame()
        mitsu_group.setStyleSheet(f"border: 2px solid {CIPHER_COLORS['accent4']}; border-radius: 8px; padding: 8px; background-color: #1f0a1a;")
        mitsu_layout = QHBoxLayout(mitsu_group)
        
        mitsu_avatar = QLabel()
        mitsu_avatar.setPixmap(_cc_get_pixmap(48, "mitsu"))
        mitsu_avatar.setFixedSize(48, 48)
        mitsu_layout.addWidget(mitsu_avatar)
        
        self.mitsu_quip_display = QTextEdit()
        self.mitsu_quip_display.setReadOnly(True)
        self.mitsu_quip_display.setMaximumHeight(70)
        self.mitsu_quip_display.setPlaceholderText("Mitsu-chan's build logs appear here...")
        mitsu_layout.addWidget(self.mitsu_quip_display, 1)
        
        bottom_row.addWidget(mitsu_group)
        layout.addLayout(bottom_row)
        
        # Add initial quips
        self.add_quip("Entropy buffet's open - who's hungry for bits?", "cipher")
        self.add_quip("Every signal is a heartbeat. Every error, a sigh.", "echo")
        self.add_quip("El Psy Kongroo! See? Chaos theory wins again.", "ayatoki")
        self.add_quip("Remote forge online. Mitsu reporting for duty!", "mitsu")
        
        return panel
    
    def create_log_panel(self):
        """System log panel"""
        panel = QGroupBox("System Log")
        layout = QVBoxLayout(panel)
        
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        self.log_display.setMaximumHeight(120)
        self.log_display.setPlaceholderText("System messages will appear here...")
        self.log_display.setLineWrapMode(QTextEdit.WidgetWidth)
        
        layout.addWidget(self.log_display)
        
        self.add_log("Entropic Chaos - Cobra Lab Phase 3 initialized")
        if PQC_AVAILABLE:
            self.add_log("PQC bindings detected - Post-quantum key wrapping available")
        else:
            self.add_log("PQC bindings not found - Classical cryptography only")
        
        return panel
    
    def setup_worker(self):
        """Setup Cipher worker thread and Phase 3 HTTP ingest"""
        self.worker_thread = QThread()
        self.worker = CIPHERTANWorker()
        self.worker.moveToThread(self.worker_thread)
        self.worker_thread.start()
        
        # PHASE 3: Start the HTTP Ingest Server for Mitsu Uplink
        start_ayatoki_ingest_server(self.worker, host="0.0.0.0", port=8000)
    
    def setup_echo_worker(self):
        """Phase 2: Setup Echo worker thread and link to Ayatoki"""
        self.echo_worker_thread = QThread()
        self.echo_worker = EchoWorker()
        self.echo_worker.moveToThread(self.echo_worker_thread)
        self.echo_worker_thread.start()
        
        # Phase 2: Link Echo to Ayatoki orchestrator
        if self.worker:
            self.worker.set_echo_worker(self.echo_worker)
    
    def setup_tray(self):
        """Setup system tray"""
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return
            
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(_cc_get_icon())
        
        tray_menu = QMenu()
        tray_menu.addAction("Show Cobra Lab", self.show)
        tray_menu.addAction("Hide to Tray", self.hide)
        tray_menu.addSeparator()
        tray_menu.addAction("Start Chaos", self.start_chaos)
        tray_menu.addAction("Stop Chaos", self.stop_chaos)
        tray_menu.addSeparator()
        tray_menu.addAction("Quit", self.close)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()
        self.tray_icon.activated.connect(self.tray_icon_activated)
    
    def tray_icon_activated(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            if self.isVisible():
                self.hide()
            else:
                self.show()
                self.raise_()
                self.activateWindow()
    
    def connect_signals(self):
        """Connect all signals including Phase 2 and Phase 3"""
        # Cipher connection buttons
        self.cipher_connect_btn.clicked.connect(self.connect_to_cipher)
        self.cipher_disconnect_btn.clicked.connect(self.disconnect_from_cipher)
        
        # Phase 2: Echo connection buttons
        self.echo_connect_btn.clicked.connect(self.connect_to_echo)
        self.echo_disconnect_btn.clicked.connect(self.disconnect_from_echo)
        
        # Control buttons
        self.start_btn.clicked.connect(self.start_chaos)
        self.stop_btn.clicked.connect(self.stop_chaos)
        self.send_cmd_btn.clicked.connect(self.send_manual_command_to_cipher)
        self.send_echo_cmd_btn.clicked.connect(self.send_manual_command_to_echo)
        self.cmd_input.returnPressed.connect(self.send_manual_command_to_cipher)
        self.brightness_slider.valueChanged.connect(self.brightness_changed)
        self.browse_log_btn.clicked.connect(self.browse_log_file)
        self.pqc_cb.stateChanged.connect(self.on_pqc_checkbox_changed)
        
        # TRNG streaming
        self.trng_start_btn.clicked.connect(self.start_trng_stream)
        self.trng_stop_btn.clicked.connect(self.stop_trng_stream)
        
        # Cipher worker signals
        if self.worker:
            self.worker.status_update.connect(self.add_log)
            self.worker.quip_generated.connect(self.add_quip)
            self.worker.key_forged.connect(self.on_key_forged)
            self.worker.pqc_key_generated.connect(self.on_pqc_key_generated)
            self.worker.rgb_updated.connect(self.on_rgb_updated)
            self.worker.keystroke_rate_updated.connect(self.on_keystroke_rate_updated)
            self.worker.entropy_level_updated.connect(self.on_entropy_level_updated)
            self.worker.audit_updated.connect(self.on_audit_updated)
            self.worker.error_occurred.connect(self.on_error)
            self.worker.connection_status.connect(self.on_cipher_connection_status_changed)
            self.worker.esp_status_updated.connect(self.on_cipher_esp_status_updated)
            
            # Phase 2: Dual audit signals
            self.worker.request_echo_audit.connect(self.request_echo_audit)
            
            # Phase 3: Mitsu signals
            self.worker.mitsu_entropy_received.connect(self.on_mitsu_entropy_received)
        
        # Phase 2: Echo worker signals
        if self.echo_worker:
            self.echo_worker.status_update.connect(self.add_log)
            self.echo_worker.quip_generated.connect(self.add_quip)
            self.echo_worker.audit_result.connect(self.on_echo_audit_result)
            self.echo_worker.error_occurred.connect(self.on_error)
            self.echo_worker.connection_status.connect(self.on_echo_connection_status_changed)
            self.echo_worker.esp_status_updated.connect(self.on_echo_esp_status_updated)
            self.echo_worker.entropy_received.connect(self.on_echo_entropy_received)
        
        # Network manager
        self.network_manager.network_status_changed.connect(self.update_network_status)
    
    def get_stylesheet(self):
        """Enhanced stylesheet with character-specific colors"""
        return f"""
        QMainWindow {{
            background-color: {CIPHER_COLORS['bg']};
            color: {CIPHER_COLORS['text']};
        }}
        
        QWidget {{
            background-color: {CIPHER_COLORS['bg']};
            color: {CIPHER_COLORS['text']};
            font-family: 'Segoe UI', 'Roboto', Arial, sans-serif;
            font-size: 10pt;
        }}
        
        QGroupBox {{
            border: 2px solid {CIPHER_COLORS['accent']};
            border-radius: 12px;
            margin: 24px 8px 12px 8px;
            padding-top: 16px;
            font-weight: bold;
            background-color: {CIPHER_COLORS['panel']};
        }}
        
        QGroupBox::title {{
            subcontrol-origin: margin;
            subcontrol-position: top left;
            padding: 4px 8px;
            color: {CIPHER_COLORS['accent2']};
            font-size: 11pt;
        }}
        
        QPushButton {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                stop:0 {CIPHER_COLORS['accent']}, stop:1 {CIPHER_COLORS['accent2']});
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 8px;
            font-weight: bold;
            min-width: 80px;
            min-height: 32px;
        }}
        
        QPushButton:hover {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                stop:0 {CIPHER_COLORS['accent2']}, stop:1 {CIPHER_COLORS['accent']});
        }}
        
        QPushButton:pressed {{
            background: {CIPHER_COLORS['accent']};
        }}
        
        QPushButton:disabled {{
            background-color: {CIPHER_COLORS['muted']};
            color: {CIPHER_COLORS['bg']};
        }}
        
        QLineEdit, QComboBox, QDoubleSpinBox {{
            background-color: {CIPHER_COLORS['bg']};
            border: 2px solid {CIPHER_COLORS['muted']};
            border-radius: 6px;
            padding: 6px 8px;
            color: {CIPHER_COLORS['text']};
            min-height: 24px;
        }}
        
        QLineEdit:focus, QComboBox:focus, QDoubleSpinBox:focus {{
            border-color: {CIPHER_COLORS['accent']};
        }}
        
        QTextEdit {{
            background-color: {CIPHER_COLORS['bg']};
            border: 2px solid {CIPHER_COLORS['muted']};
            border-radius: 8px;
            padding: 8px;
            color: {CIPHER_COLORS['text']};
        }}
        
        QSlider::groove:horizontal {{
            border: 1px solid {CIPHER_COLORS['muted']};
            height: 8px;
            background: {CIPHER_COLORS['bg']};
            border-radius: 4px;
        }}
        
        QSlider::handle:horizontal {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                stop:0 {CIPHER_COLORS['accent']}, stop:1 {CIPHER_COLORS['accent2']});
            border: 1px solid {CIPHER_COLORS['accent']};
            width: 20px;
            height: 16px;
            margin: -4px 0;
            border-radius: 8px;
        }}
        
        QSlider::sub-page:horizontal {{
            background: {CIPHER_COLORS['accent']};
            border-radius: 4px;
        }}
        
        QCheckBox {{
            spacing: 8px;
            min-height: 24px;
        }}
        
        QCheckBox::indicator {{
            width: 18px;
            height: 18px;
            border: 2px solid {CIPHER_COLORS['muted']};
            border-radius: 4px;
            background-color: {CIPHER_COLORS['bg']};
        }}
        
        QCheckBox::indicator:checked {{
            background-color: {CIPHER_COLORS['accent']};
            border-color: {CIPHER_COLORS['accent']};
        }}
        
        QLabel {{
            color: {CIPHER_COLORS['text']};
            padding: 2px;
        }}
        
        QTabWidget::pane {{
            border: 2px solid {CIPHER_COLORS['muted']};
            border-radius: 8px;
            background: {CIPHER_COLORS['panel']};
        }}
        
        QTabBar::tab {{
            background: {CIPHER_COLORS['bg']};
            color: {CIPHER_COLORS['text']};
            border: 1px solid {CIPHER_COLORS['muted']};
            padding: 8px 16px;
            margin-right: 2px;
        }}
        
        QTabBar::tab:selected {{
            background: {CIPHER_COLORS['accent']};
            color: white;
        }}
        
        QStatusBar {{
            background-color: {CIPHER_COLORS['panel']};
            border-top: 1px solid {CIPHER_COLORS['accent']};
            color: {CIPHER_COLORS['text']};
        }}
        """

    def refresh_serial_ports(self):
        """Refresh available serial ports for both devices"""
        self.cipher_port_combo.clear()
        self.echo_port_combo.clear()
        
        ports = list_ports.comports()
        
        # Check for specific symlinks on Linux/Unix
        if os.path.exists("/dev/ttyCIPHER"):
            self.cipher_port_combo.addItem("/dev/ttyCIPHER - Symlink", "/dev/ttyCIPHER")
        if os.path.exists("/dev/ttyECHO"):
            self.echo_port_combo.addItem("/dev/ttyECHO - Symlink", "/dev/ttyECHO")
        
        for port in ports:
            desc = f"{port.device} - {port.description}"
            if "CH340" in port.description or "CP210" in port.description or "FTDI" in port.description:
                desc += " (Likely ESP32)"
            
            self.cipher_port_combo.addItem(desc, port.device)
            self.echo_port_combo.addItem(desc, port.device)
        
        if not ports and self.cipher_port_combo.count() == 0:
            self.cipher_port_combo.addItem("No ports found", "")
            self.echo_port_combo.addItem("No ports found", "")
            
        self.add_log(f"Found {len(ports)} serial ports")
    
    def browse_log_file(self):
        """Browse for log file"""
        filename, _ = QFileDialog.getSaveFileName(
            self, 
            "Choose Key Log File", 
            str(DEFAULT_LOG), 
            "Text Files (*.txt);;JSON Files (*.json);;All Files (*)"
        )
        
        if filename:
            self.log_path_edit.setText(filename)
    
    def brightness_changed(self, value):
        """Handle brightness change"""
        self.brightness_label.setText(f"{value}%")
        if self.worker:
            self.worker.brightness = value / 100.0
            if self.worker.serial_connection:
                self.worker.send_serial_command(f"BRI:{value/100.0:.2f}")
    
    def connect_to_cipher(self):
        """Connect to Cipher-tan ESP32"""
        if not self.worker:
            return
            
        port = self.cipher_manual_port_edit.text().strip()
        if not port:
            port = self.cipher_port_combo.currentData()
            
        if not port:
            QMessageBox.warning(self, "Connection Error", "Please select or enter a COM port for Cipher-tan")
            return
            
        self.worker.serial_port = port
        self.worker.connect_serial()
    
    def disconnect_from_cipher(self):
        """Disconnect from Cipher-tan ESP32"""
        if self.worker and self.worker.serial_connection:
            self.worker.serial_connection.close()
            self.worker.serial_connection = None
            self.on_cipher_connection_status_changed(False)
    
    def connect_to_echo(self):
        """Phase 2: Connect to Echo-tan ESP32"""
        if not self.echo_worker:
            return
            
        port = self.echo_manual_port_edit.text().strip()
        if not port:
            port = self.echo_port_combo.currentData()
            
        if not port:
            QMessageBox.warning(self, "Connection Error", "Please select or enter a COM port for Echo-tan")
            return
            
        self.echo_worker.serial_port = port
        self.echo_worker.connect_serial()
    
    def disconnect_from_echo(self):
        """Phase 2: Disconnect from Echo-tan ESP32"""
        if self.echo_worker and self.echo_worker.serial_connection:
            self.echo_worker.serial_connection.close()
            self.echo_worker.serial_connection = None
            self.on_echo_connection_status_changed(False)
    
    def start_chaos(self):
        """Start the chaos system with Phase 3 quad-source mixing"""
        if not self.worker:
            return
            
        # Apply settings to Cipher worker
        self.worker.window_seconds = self.window_spin.value()
        self.worker.brightness = self.brightness_slider.value() / 100.0
        self.worker.realtime_keys = self.realtime_cb.isChecked()
        self.worker.include_host_rng = self.host_rng_cb.isChecked()
        self.worker.include_esp_trng = self.esp_trng_cb.isChecked()
        self.worker.lights_enabled = self.lights_cb.isChecked()
        self.worker.include_mouse_entropy = self.mouse_rng_cb.isChecked()
        self.worker.key_log_path = self.log_path_edit.text().strip() or str(DEFAULT_LOG)
        
        self.worker.pqc_enabled = self.pqc_cb.isChecked()
        self.worker.kyber_enabled = self.kyber_cb.isChecked() if hasattr(self, 'kyber_cb') else True
        self.worker.falcon_enabled = self.falcon_cb.isChecked() if hasattr(self, 'falcon_cb') else True
        
        # Start Cipher
        self.worker.start_system()
        
        # Phase 2: Start Echo if connected
        if self.echo_worker and self.echo_worker.connected:
            self.echo_worker.start_system()
        
        # Update UI
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.status_bar.showMessage("Chaos Storm Active - Quad-source mixing engaged!")
        
        # Ayatoki quip
        self.add_quip("Phase 3 operational. All nodes reporting nominal!", "ayatoki")
    
    def stop_chaos(self):
        """Stop the chaos system"""
        if self.worker:
            self.worker.stop_system()
        
        if self.echo_worker:
            self.echo_worker.stop_system()
            
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.status_bar.showMessage("Chaos Storm Stopped")
        
        self.add_quip("Experiment paused. Reviewing data...", "ayatoki")
    
    def send_manual_command_to_cipher(self):
        """Send manual command to Cipher"""
        if not self.worker or not self.worker.serial_connection:
            QMessageBox.warning(self, "Not Connected", "Please connect to Cipher-tan first")
            return
            
        command = self.cmd_input.text().strip()
        if command:
            success = self.worker.send_serial_command(command)
            if success:
                self.add_log(f"Sent to Cipher: {command}")
            else:
                self.add_log(f"Failed to send to Cipher: {command}")
            self.cmd_input.clear()
    
    def send_manual_command_to_echo(self):
        """Phase 2: Send manual command to Echo"""
        if not self.echo_worker or not self.echo_worker.serial_connection:
            QMessageBox.warning(self, "Not Connected", "Please connect to Echo-tan first")
            return
            
        command = self.cmd_input.text().strip()
        if command:
            success = self.echo_worker.send_serial_command(command)
            if success:
                self.add_log(f"Sent to Echo: {command}")
            else:
                self.add_log(f"Failed to send to Echo: {command}")
            self.cmd_input.clear()
    
    def start_trng_stream(self):
        """Start TRNG streaming from Cipher"""
        if not self.worker or not self.worker.serial_connection:
            QMessageBox.warning(self, "Not Connected", "Please connect to Cipher-tan first")
            return
        
        rate = int(self.trng_rate_spin.value())
        command = f"TRNG:START,{rate}"
        
        if self.worker.send_serial_command(command):
            self.trng_streaming = True
            self.trng_start_btn.setEnabled(False)
            self.trng_stop_btn.setEnabled(True)
            self.add_log(f"TRNG streaming started at {rate} Hz")
            self.add_quip("My TRNG hums like a rock concert, and every photon's backstage.", "cipher")
        else:
            self.add_log("Failed to start TRNG streaming")

    def stop_trng_stream(self):
        """Stop TRNG streaming"""
        if not self.worker or not self.worker.serial_connection:
            return
        
        if self.worker.send_serial_command("TRNG:STOP"):
            self.trng_streaming = False
            self.trng_start_btn.setEnabled(True)
            self.trng_stop_btn.setEnabled(False)
            self.add_log("TRNG streaming stopped")
        else:
            self.add_log("Failed to stop TRNG streaming")
    
    def update_network_status(self, status):
        """Update network status"""
        if status['headscale']:
            self.headscale_status.setText("Headscale: Connected")
            self.headscale_status.setStyleSheet(f"color: {CIPHER_COLORS['success']};")
            self.uplink_status.setText("Tailscale: Active")
            self.uplink_status.setStyleSheet(f"color: {CIPHER_COLORS['success']};")
        else:
            self.headscale_status.setText("Headscale: Disconnected")
            self.headscale_status.setStyleSheet(f"color: {CIPHER_COLORS['error']};")
            self.uplink_status.setText("Tailscale: Standalone")
            self.uplink_status.setStyleSheet(f"color: {CIPHER_COLORS['warning']};")
        
        self.mesh_peers_label.setText(f"Mesh Peers: {status['mesh_peers']}")
    
    def add_log(self, message):
        """Add log message"""
        timestamp = datetime.now().strftime("[%H:%M:%S]")
        self.log_display.append(f"{timestamp} {message}")
        
        cursor = self.log_display.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.log_display.setTextCursor(cursor)
    
    def add_quip(self, quip, character="cipher"):
        """Phase 3: Add character-specific quip with proper styling"""
        timestamp = datetime.now().strftime("[%H:%M:%S]")
        
        # Character-specific colors and names
        if character == "cipher":
            color = CIPHER_COLORS['accent2']  # Purple
            name = "Cipher-tan"
            display = self.cipher_quip_display
        elif character == "echo":
            color = CIPHER_COLORS['accent3']  # Teal
            name = "Echo-tan"
            display = self.echo_quip_display
        elif character == "ayatoki":
            color = CIPHER_COLORS['accent']  # Red
            name = "Ayatoki"
            display = self.ayatoki_quip_display
        elif character == "mitsu":
            color = CIPHER_COLORS['accent4']  # Pink
            name = "Mitsu-chan"
            display = self.mitsu_quip_display
        else:
            color = CIPHER_COLORS['text']
            name = "System"
            display = self.log_display
        
        formatted_quip = f'<span style="color:{color}">{timestamp}</span> <b>{name}:</b> {quip}'
        
        display.append(formatted_quip)
        
        cursor = display.textCursor()
        cursor.movePosition(QTextCursor.End)
        display.setTextCursor(cursor)
        
    def on_pqc_checkbox_changed(self, state):
        """Update PQC state when checkbox changes"""
        if self.worker:
            self.worker.pqc_enabled = self.pqc_cb.isChecked()
            if self.worker.pqc_enabled:
                self.add_log("PQC Key Wrapping ENABLED")
                self.add_quip("Kyber crystals aligned - let the lattice sing.", "cipher")
                self.add_quip("Quantum protection layer activated. Proceeding with caution.", "ayatoki")
            else:
                self.add_log("PQC Key Wrapping DISABLED")
                self.add_quip("Back to classical crypto. Simple, elegant, but quantum-vulnerable.", "cipher")
    
    def on_key_forged(self, key_b64, metadata):
        """Handle classical key forged"""
        self.keys_generated = metadata.get('key_number', self.keys_generated + 1)
        self.keys_label.setText(f"Keys Generated: {self.keys_generated}")
        
        key_type = metadata.get('type', 'classical_aes256')
        if key_type == 'classical_aes256':
            self.key_type_label.setText("Key Type: Classical AES256")
            self.key_type_label.setStyleSheet(f"color: {CIPHER_COLORS['text']};")
        
        # For classical-only keys, reflect that in Ayatoki's wrap summary panel
        if hasattr(self, 'ayatoki_last_wrap_label'):
            self.ayatoki_last_wrap_label.setText("Last Key Wrap: Classical only (no PQC layer)")
        if hasattr(self, 'ayatoki_wrap_algorithm_label'):
            self.ayatoki_wrap_algorithm_label.setText("Wrap Algorithm: AES-256 (host)")
        
        key_preview = key_b64[:12] + "..." if len(key_b64) > 12 else key_b64
        self.add_log(f"Key forged: {key_preview}")
        
        # Ayatoki commentary
        if random.random() < 0.3:
            self.add_quip(random.choice(self.ayatoki_quips), "ayatoki")
    
    def on_pqc_key_generated(self, key_preview, metadata):
        """Handle PQC-wrapped key generated - Phase 3: Kyber+Falcon Hybrid"""
        key_type = metadata.get('type', 'unknown')
        wrapping = metadata.get('wrapping', '')
        signature_verified = metadata.get('signature_verified', False)
        sources = metadata.get('sources', [])

        # Reflect post-PQC wrap details in Ayatoki's audit panel
        if hasattr(self, 'ayatoki_last_wrap_label'):
            source_text = " + ".join(sources) if sources else "multi-source"
            self.ayatoki_last_wrap_label.setText(f"Last Key: {source_text} -> {wrapping}")
        if hasattr(self, 'ayatoki_wrap_algorithm_label'):
            self.ayatoki_wrap_algorithm_label.setText(f"Protection: {key_type}")

        # Phase 2: Update Echo Post-Wrap Verification tab
        if hasattr(self, 'echo_audit_score_label'):
            if signature_verified:
                self.echo_audit_score_label.setText("Signature Valid")
                self.echo_audit_score_label.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {CIPHER_COLORS['success']};")
                self.echo_health_status_label.setText("Post-Wrap: Falcon signature verified")
                self.echo_verdict_label.setText("Provenance chain intact. Key authenticated.")
            else:
                self.echo_audit_score_label.setText("Signature Failed")
                self.echo_audit_score_label.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {CIPHER_COLORS['error']};")
                self.echo_health_status_label.setText("Post-Wrap: Verification FAILED")
                self.echo_verdict_label.setText("CRITICAL: Signature could not be verified!")

        # Update key type display with signature status
        if 'hybrid' in key_type.lower():
            status_icon = "[OK]" if signature_verified else "[FAIL]"
            self.key_type_label.setText(f"Key Type: PQC Hybrid (Kyber+Falcon) {status_icon}")
            self.key_type_label.setStyleSheet(f"color: {CIPHER_COLORS['pqc']}; font-weight: bold;")
        elif 'kyber' in key_type.lower():
            self.key_type_label.setText("Key Type: PQC-Wrapped (Kyber512)")
            self.key_type_label.setStyleSheet(f"color: {CIPHER_COLORS['pqc']}; font-weight: bold;")
        elif 'falcon' in key_type.lower():
            self.key_type_label.setText("Key Type: PQC-Signed (Falcon512)")
            self.key_type_label.setStyleSheet(f"color: {CIPHER_COLORS['pqc']}; font-weight: bold;")
        
        self.add_log(f"PQC Key Generated ({wrapping}): {key_preview[:20]}... | Sig: {'VALID' if signature_verified else 'FAIL'}")
        
        # Character reactions - Phase 3 style
        if 'hybrid' in key_type.lower() and signature_verified:
            pqc_quips_ayatoki = [
                "Kyber+Falcon hybrid deployed. Post-quantum fortress erected.",
                "Signature verified. The theorem holds. Q.E.D.",
                "Four-source mixing complete. PQC protection: maximum.",
                "Perfect! Another proof that math can weaponize randomness."
            ]
            self.add_quip(random.choice(pqc_quips_ayatoki), "ayatoki")
        else:
            pqc_quips_cipher = [
                "Kyber crystals aligned - let the lattice sing.",
                "Falcon dives, signature lands - classical crypto's a fossil.",
                "Another key minted - smell that? That's post-quantum spice.",
                "Noise harvested, entropy bottled, PQC corked tight. Cheers!"
            ]
            self.add_quip(random.choice(pqc_quips_cipher), "cipher")
        
        if random.random() < 0.3 and signature_verified:
            echo_quips = [
                "Key observed and recorded. My audit stands witness.",
                "Signature verified. Provenance chain intact."
            ]
            self.add_quip(random.choice(echo_quips), "echo")
    
    def on_rgb_updated(self, r, g, b):
        """Handle RGB update"""
        self.rgb_color = {'r': r, 'g': g, 'b': b}
        self.rgb_label.setText(f"RGB: ({r}, {g}, {b})")
        
        if hasattr(self, 'viz_widget'):
            self.viz_widget.set_rgb_color(r, g, b)
    
    def on_keystroke_rate_updated(self, rate):
        """Handle keystroke rate update"""
        self.keystroke_rate = rate
        self.keystroke_label.setText(f"Keystroke Rate: {rate:.1f}/s")
        
        if hasattr(self, 'viz_widget'):
            self.viz_widget.add_keystroke_point(rate)
    
    def on_entropy_level_updated(self, level):
        """Handle entropy level update"""
        self.entropy_level = level
        self.entropy_label.setText(f"Entropy Level: {level:.1f}%")
        self.entropy_progress.setValue(int(level))
        
        if hasattr(self, 'viz_widget'):
            self.viz_widget.add_entropy_point(level)
    
    def on_error(self, error_msg):
        """Handle errors"""
        self.add_log(f"ERROR: {error_msg}")
        self.status_bar.showMessage(f"Error: {error_msg}", 5000)
    
    def on_cipher_connection_status_changed(self, connected):
        """Handle Cipher connection status changes"""
        if connected:
            self.cipher_connection_status.setText("Connected to Cipher-tan")
            self.cipher_connection_status.setStyleSheet(f"color: {CIPHER_COLORS['success']};")
            self.cipher_connect_btn.setEnabled(False)
            self.cipher_disconnect_btn.setEnabled(True)
            self.status_bar.showMessage("Cipher-tan connected")
            self.add_quip("RNG Queen reporting for duty! Let's chaos it up!", "cipher")
        else:
            self.cipher_connection_status.setText("Disconnected")
            self.cipher_connection_status.setStyleSheet(f"color: {CIPHER_COLORS['error']};")
            self.cipher_connect_btn.setEnabled(True)
            self.cipher_disconnect_btn.setEnabled(False)
            self.status_bar.showMessage("Cipher-tan disconnected")
    
    def on_echo_connection_status_changed(self, connected):
        """Phase 2: Handle Echo connection status changes"""
        if connected:
            self.echo_connection_status.setText("Connected to Echo-tan")
            self.echo_connection_status.setStyleSheet(f"color: {CIPHER_COLORS['success']};")
            self.echo_connect_btn.setEnabled(False)
            self.echo_disconnect_btn.setEnabled(True)
            self.echo_connected = True
            self.status_bar.showMessage("Echo-tan connected")
            self.add_quip("Audit systems online. Listening for entropy signals.", "echo")
        else:
            self.echo_connection_status.setText("Disconnected")
            self.echo_connection_status.setStyleSheet(f"color: {CIPHER_COLORS['error']};")
            self.echo_connect_btn.setEnabled(True)
            self.echo_disconnect_btn.setEnabled(False)
            self.echo_connected = False
            self.status_bar.showMessage("Echo-tan disconnected")
    
    @Slot(int, dict)
    def on_mitsu_entropy_received(self, byte_count, meta):
        """Phase 3: Handle entropy received from Mitsu"""
        self.mitsu_bytes_received += byte_count
        self.mitsu_connected = True
        
        # Update UI
        self.mitsu_connection_status.setText("ONLINE - Receiving entropy!")
        self.mitsu_connection_status.setStyleSheet(f"color: {CIPHER_COLORS['success']}; font-weight: bold;")
        
        self.mitsu_bytes_label.setText(f"Bytes Received: {self.mitsu_bytes_received}")
        
        if meta:
            seq = meta.get('seq', '--')
            source = meta.get('source', '--')
            health = meta.get('health', 'OK')
            
            self.mitsu_seq_label.setText(f"Last Sequence: {seq}")
            self.mitsu_source_label.setText(f"Last Source: {source}")
            self.mitsu_quality_label.setText(f"Health: {health}")
            
            if health == "OK":
                self.mitsu_quality_label.setStyleSheet(f"color: {CIPHER_COLORS['success']};")
            else:
                self.mitsu_quality_label.setStyleSheet(f"color: {CIPHER_COLORS['warning']};")
    
    @Slot(dict)
    def on_cipher_esp_status_updated(self, status):
        """Handle Cipher ESP32 status updates"""
        try:
            version = status.get('version', 'Unknown')
            if version != 'Unknown':
                self.cipher_version_label.setText(f"Version: {version}")
            
            wifi_bytes = status.get('wifi_entropy_bytes', 0)
            usb_bytes = status.get('usb_entropy_bytes', 0)
            
            self.cipher_wifi_entropy_label.setText(f"WiFi Entropy: {wifi_bytes} bytes")
            self.cipher_usb_entropy_label.setText(f"USB Jitter: {usb_bytes} bytes")
            
            if wifi_bytes > 0 and wifi_bytes % 100 == 0:
                self.add_quip("Packets scrambled, mesh tangled - chaos relay primed!", "cipher")
            
            if usb_bytes > 0 and usb_bytes % 50 == 0:
                self.add_quip("USB jitter swallowed whole - entropy's dessert course!", "cipher")
                
        except Exception as e:
            self.add_log(f"Error parsing Cipher ESP32 status: {e}")
    
    @Slot(dict)
    def on_echo_esp_status_updated(self, status):
        """Phase 2: Handle Echo ESP32 status updates"""
        try:
            version = status.get('version', 'Unknown')
            if version != 'Unknown':
                self.echo_version_label.setText(f"Version: {version}")
            
            health = status.get('trng_health', 'OK')
            health_failures = status.get('health_failures', 0)
            health_warnings = status.get('health_warnings', 0)
            keys_audited = status.get('keys_audited', 0)
            
            health_text = f"Health: {health}"
            if health_failures > 0:
                health_text += f" ({health_failures} failures)"
            elif health_warnings > 0:
                health_text += f" ({health_warnings} warnings)"
            
            self.echo_health_label.setText(health_text)
            self.echo_audited_label.setText(f"Keys Audited: {keys_audited}")
            
            # Update health color
            if health == "OK":
                self.echo_health_label.setStyleSheet(f"color: {CIPHER_COLORS['success']};")
            elif health == "WARN":
                self.echo_health_label.setStyleSheet(f"color: {CIPHER_COLORS['warning']};")
            else:
                self.echo_health_label.setStyleSheet(f"color: {CIPHER_COLORS['error']};")
            
            if keys_audited > 0 and keys_audited % 5 == 0:
                self.add_quip("Entropy validated. All tests nominal. Proceeding.", "echo")
                
        except Exception as e:
            self.add_log(f"Error parsing Echo ESP32 status: {e}")
    
    @Slot(int)
    def on_echo_entropy_received(self, byte_count):
        """Phase 2: Handle Echo verified entropy reception"""
        # Update Echo status to show it's actively streaming
        if hasattr(self, 'echo_audited_label'):
            current_text = self.echo_audited_label.text()
            if "Verified Entropy:" not in current_text:
                self.echo_audited_label.setText(f"Verified Entropy: +{byte_count}b")
        
        if random.random() < 0.03:
            self.add_quip("Internal health verified. Streaming pure entropy.", "echo")
    
    @Slot(dict)
    def on_audit_updated(self, audit: dict):
        """Update Ayatoki audit panel - Phase 2: Pre-Wrap Validation"""
        try:
            score = float(audit.get("score", 0.0))
            self.ayatoki_audit_score_label.setText(f"{score:.1f}%")
            if hasattr(self, 'audit_progress'):
                self.audit_progress.setValue(int(score))
            
            # Update individual test results
            self.ayatoki_frequency_test_label.setText(f"Frequency Test: {'Passed' if audit.get('freq_pass') else 'Needs work'}")
            self.ayatoki_runs_test_label.setText(f"Runs Test: {'Passed' if audit.get('runs_pass') else 'Needs work'}")
            self.ayatoki_chi_square_label.setText(f"Chi-Square: {'Passed' if audit.get('chi_pass') else 'Noisy'}")
            self.ayatoki_entropy_rate_label.setText(f"Entropy Rate: {audit.get('entropy_bpb', 0.0):.2f} bits/byte")
            
            # PQC readiness
            pqc_ready = audit.get('pqc_ready', False)
            self.ayatoki_pqc_ready_label.setText(f"PQC Ready: {'Yes - Proceeding' if pqc_ready else 'No - Gathering'}")
            if pqc_ready:
                self.ayatoki_pqc_ready_label.setStyleSheet(f"color: {CIPHER_COLORS['success']}; font-weight: bold;")
                if random.random() < 0.05:
                    self.add_quip("Pre-audit: Quality verified. Proceeding to PQC wrapping.", "ayatoki")
            else:
                self.ayatoki_pqc_ready_label.setStyleSheet(f"color: {CIPHER_COLORS['warning']}; font-weight: bold;")
                
        except Exception:
            pass
    
    @Slot(dict)
    def on_echo_audit_result(self, audit):
        """Phase 2: Handle Echo audit result"""
        try:
            key_id = audit.get('key_id', 'unknown')
            audit_type = audit.get('type', 'unknown')
            health = audit.get('health', 'OK')
            reason = audit.get('reason', 'No issues detected')
            
            self.echo_health_status_label.setText(f"Health: {health}")
            self.echo_verdict_label.setText(f"Verdict: {reason}")
            
            if health == "OK":
                self.echo_audit_score_label.setText("Passed")
                self.echo_audit_score_label.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {CIPHER_COLORS['success']};")
                self.add_quip("Key observed and recorded. My audit stands witness.", "echo")
            elif health == "WARN":
                self.echo_audit_score_label.setText("Warning")
                self.echo_audit_score_label.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {CIPHER_COLORS['warning']};")
                self.add_quip("Quality below threshold. Recommend additional collection.", "echo")
            else:
                self.echo_audit_score_label.setText("Failed")
                self.echo_audit_score_label.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {CIPHER_COLORS['error']};")
                self.add_quip("Deviation detected. Marking sample as suspect.", "echo")
            
            self.add_log(f"Echo audit ({audit_type}): {health} - {reason}")
            
            # Update audit log file
            self._update_echo_audit_log(key_id, audit_type, audit)
            
        except Exception as e:
            self.add_log(f"Error processing Echo audit: {e}")
    
    def _update_echo_audit_log(self, key_id, audit_type, audit_data):
        """Phase 2: Update per-key audit log with Echo's verdict"""
        try:
            import json
            audit_file = AUDIT_DIR / f"{key_id}_audit.json"
            
            if audit_file.exists():
                with open(audit_file, 'r') as f:
                    data = json.load(f)
                
                if audit_type == "prewrap":
                    data['echo_prewrap_audit'] = audit_data
                elif audit_type == "postwrap":
                    data['echo_postwrap_audit'] = audit_data
                
                with open(audit_file, 'w') as f:
                    json.dump(data, f, indent=2)
                    
        except Exception as e:
            self.add_log(f"Failed to update audit log: {e}")
    
    @Slot(str, str)
    def request_echo_audit(self, key_id, audit_type):
        """Phase 2: Request Echo to audit a specific key"""
        if self.echo_worker and self.echo_worker.serial_connection:
            self.echo_worker.request_audit(key_id, audit_type)
            self.add_log(f"Requested Echo audit: {key_id} ({audit_type})")
        else:
            self.add_log(f"Echo not connected - skipping {audit_type} audit for {key_id}")
    
    def resizeEvent(self, event):
        """Handle resize events"""
        super().resizeEvent(event)
        if hasattr(self, 'entropy_progress'):
            self.entropy_progress.update()
        if hasattr(self, 'audit_progress'):
            self.audit_progress.update()

    def closeEvent(self, event):
        """Handle close event"""
        if hasattr(self, 'tray_icon') and self.tray_icon.isVisible():
            self.hide()
            self.tray_icon.showMessage(
                "Entropic Chaos - Cobra Lab", 
                "Still running in background. Double-click tray icon to show.", 
                QSystemTrayIcon.Information, 
                3000
            )
            event.ignore()
        else:
            # Cleanup
            if self.worker:
                self.worker.stop_system()
            if self.echo_worker:
                self.echo_worker.stop_system()
            if self.worker_thread:
                self.worker_thread.quit()
                self.worker_thread.wait(3000)
            if self.echo_worker_thread:
                self.echo_worker_thread.quit()
                self.echo_worker_thread.wait(3000)
            event.accept()