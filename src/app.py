import sys
from pathlib import Path

import PySide6.QtCore as QtCore
from PySide6.QtCore import QObject, Property, Slot, QSettings, QStandardPaths
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine

from backend import library, cache_manager


# Set Organization Name and Domain
QtCore.QCoreApplication.setOrganizationName("PolarTea Studios")
QtCore.QCoreApplication.setOrganizationDomain("dev.polartblock.ptbanime")
QtCore.QCoreApplication.setApplicationName("PTBAnime")
QtCore.QCoreApplication.setApplicationVersion("2.0.3")

# Set important Folder and File Paths
QML_FOLDER_PATH = Path(__file__).parents[1] / "qml"
QML_MAIN_FILE_PATH = QML_FOLDER_PATH / "Main.qml"

APPDATA = QStandardPaths.writableLocation(QStandardPaths.AppDataLocation)
print("Debug: AppData Path:", APPDATA)


# The Backend
class BackEnd(QObject):
    def __init__(self, settings):
        super().__init__(); self.settings: QSettings = settings

    # Check if it's first time running
    @Property(bool)
    def is_first_time(self):
        return self.settings.value("app/first_time", True, type=bool)
    
    # Set a setting
    @Slot(str, str)
    def set_setting(self, key, value):
        self.settings.setValue(key, value)
    
    # Get a setting
    @Slot(str, str, result=str)
    def get_setting(self, key, default):
        return self.settings.value(key, default)


# The Main Application
class App:
    def __init__(self):
        # Load Settings
        self.settings = QSettings("PolarTea Studios", "PTBAnime")

        # Create cache manager
        self.cache_manager = cache_manager.CacheManager(APPDATA)

        # For testing purposes to test first time running
        # self.settings.setValue("app/first_time", True)

        # If there's no setting for app/first_time, it's the first time running
        if not self.settings.contains("app/first_time"):
            self.settings.setValue("app/first_time", True)

        # Create the Backend
        self.backend = BackEnd(self.settings)

        # Initialize the main App
        self.app = QGuiApplication(sys.argv)

        # Set Desktop File Name
        self.app.setDesktopFileName("dev.polartblock.ptbanime")

        # Setup the Engine
        self.engine = QQmlApplicationEngine()

        # Provide Context
        self.engine.rootContext().setContextProperty("backend", self.backend)

        # Load the Engine
        self.engine.load(QtCore.QUrl.fromLocalFile(QML_MAIN_FILE_PATH))

        # Check if QML loaded successfully
        if not self.engine.rootObjects(): print("Debug: QML failed to load - THERES NOTHING!"); sys.exit(-1)

        # If First Time is detected, print and reset
        if self.settings.value("app/first_time", True, type=bool):
            print("Debug: First time running Detected!")
            self.settings.setValue("app/first_time", False)
        
        # Test Library Backend
        library.scan_anime_folder(self.settings.value("app/anime_folder_path"))  # "file:///run/media/polar/Skibidi Riz/ani-cli/anime"

        # Start the app
        self.exit_code = self.app.exec()

        # Exit normally
        sys.exit(self.exit_code)


def run():
    # Create the App and run it
    app = App()
