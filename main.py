"""
Entropic Chaos - Main Entry Point
Cobra Lab v0.5 - PHASE 2 (FULL RESTORATION)
Multi-device distributed entropy harvesting with PQC key wrapping.
Phase 2: Ayatoki orchestrator + Cipher-tan + Echo-tan dual audit system.

RESTORATION LOG:
- Restored 1000+ lines of GUI styling and layout logic.
- Restored Phase 1 "Always Rotating" RGB idle animation.
- Implemented Phase 2 Dual Audit (Ayatoki Pre-wrap + Echo Post-wrap).
- Implemented Non-blocking Serial I/O for high performance.
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
    app.setApplicationName("Entropic Chaos · Cobra Lab Phase 2")
    app.setApplicationVersion("0.5-phase2-full")

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
