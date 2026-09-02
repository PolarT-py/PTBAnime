import sys
from pathlib import Path

import PySide6.QtCore as QtCore
from PySide6.QtCore import QObject, Slot, QSettings, QStandardPaths
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine


# Set Organization Name and Domain
QtCore.QCoreApplication.setOrganizationName("PolarTea Studios")
QtCore.QCoreApplication.setOrganizationDomain("dev.polartblock.ptbanime")
QtCore.QCoreApplication.setApplicationName("PTBAnime")
QtCore.QCoreApplication.setApplicationVersion("2.0.1")

# Set important Folder and File Paths
QML_FOLDER_PATH = Path(__file__).parents[2] / "qml"
QML_MAIN_FILE_PATH = QML_FOLDER_PATH / "Main.qml"

APPDATA = QStandardPaths.writableLocation(QStandardPaths.AppDataLocation)
print("AppData Path:", APPDATA)


# The Backend
class BackEnd(QObject):
    @Slot()
    def test_hello(self):
        print("Test Hello Working")


# The Main Application
class App:
    def __init__(self):
        # Load Settings
        self.settings = QSettings("PolarTea Studios", "PTBAnime")

        # Create the Backend
        self.backend = BackEnd()

        # Initialize the main App
        self.app = QGuiApplication(sys.argv)

        # Set Desktop File Name
        self.app.setDesktopFileName("dev.polartblock.ptbanime")

        # Setup the Engine
        self.engine = QQmlApplicationEngine()
        self.engine.rootContext().setContextProperty("backend", self.backend)
        self.engine.load(QtCore.QUrl.fromLocalFile(QML_MAIN_FILE_PATH))
        
        # Check if QML loaded successfully
        if not self.engine.rootObjects(): sys.exit(-1)

        # Start the app
        self.exit_code = self.app.exec()

        # Exit normally
        sys.exit(self.exit_code)


def run():
    # Create the App and run it
    app = App()
