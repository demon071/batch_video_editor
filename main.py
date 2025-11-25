"""
Batch Video Editor - Main Entry Point

A production-ready PyQt5 desktop application for batch video editing using FFmpeg.
Supports GPU acceleration, multiple filters, and flexible codec settings.
"""
import sys
from pathlib import Path
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import Qt

from ui.main_window import MainWindow
from config.settings import AppConfig
from utils.system_check import check_ffmpeg


def main():
    """Main application entry point."""
    # Enable high DPI scaling BEFORE creating QApplication
    if hasattr(Qt, 'AA_EnableHighDpiScaling'):
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName("Batch Video Editor")
    app.setOrganizationName("BatchVideoEditor")

    
    # Check FFmpeg availability
    ffmpeg_available, ffmpeg_msg = check_ffmpeg()
    if not ffmpeg_available:
        QMessageBox.critical(
            None,
            "FFmpeg Not Found",
            f"{ffmpeg_msg}\n\n"
            "FFmpeg is required for this application to work.\n"
            "Please install FFmpeg and add it to your system PATH.\n\n"
            "Download from: https://ffmpeg.org/download.html"
        )
        return 1
    
    # Load configuration
    config = AppConfig()
    
    # Create and show main window
    window = MainWindow(config)
    window.show()
    
    # Run application
    return app.exec_()


if __name__ == '__main__':
    sys.exit(main())
