"""
Entropic Chaos - Main Entry Point
Cobra Lab v0.6 - PHASE 3 (MITSU INTEGRATION)
Multi-device distributed entropy harvesting with PQC key wrapping.
Phase 3: Ayatoki Orchestrator + Cipher (Hardware) + Echo (Audit) + Mitsu (Network/Forge).

RESTORATION LOG:
- Fixed text encoding artifacts.
- Implemented Phase 3: Mitsu-chan integration.
- Added Pink theme (Accent 4) for Mitsu.
- Replaced Network Manager with Mitsu's Network Forge.
"""

import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon, QPixmap, QColor

# Import GUI module
from gui import CIPHERTANMainWindow
from function import CIPHER_COLORS

def main():
    """Main application entry point"""
    try:
        from PySide6 import QtCore
        if QtCore.QT_VERSION.startswith('5.'):
            QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    except Exception:
        pass
    
    app = QApplication(sys.argv)
    app.setApplicationName("Entropic Chaos · Cobra Lab Phase 3")
    app.setApplicationVersion("0.6-phase3-mitsu")

    # Set application icon
    try:
        icon_path = Path(__file__).parent / "icon.png"
        if icon_path.exists():
            app.setWindowIcon(QIcon(str(icon_path)))
        else:
            pixmap = QPixmap(64, 64)
            pixmap.fill(QColor(CIPHER_COLORS['accent']))
            app.setWindowIcon(QIcon(pixmap))
    except Exception:
        pass

    # Create and show main window
    window = CIPHERTANMainWindow()
    window.show()

    # Run application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()