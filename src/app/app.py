import sys
from pathlib import Path

from PySide6.QtGui import QGuiApplication
import PySide6.QtCore as QtCore
from PySide6.QtCore import QObject, Slot
from PySide6.QtQml import QQmlApplicationEngine


# Set important Folder and File Paths
QML_FOLDER_PATH = Path(__file__).parents[2] / "qml"
QML_MAIN_FILE_PATH = QML_FOLDER_PATH / "Main.qml"


# The Backend
class BackEnd(QObject):
    @Slot()
    def test_hello(self):
        print("Test Hello Working")


# The Main Application
class App:
    def __init__(self):
        # Create the Backend
        self.backend = BackEnd()

        # Initialize the main app GUI
        self.app = QGuiApplication(sys.argv)

        # Set Name
        self.app.setApplicationName("PTBAnime")
        self.app.setDesktopFileName("dev.polartblock.ptbanime")

        # Setup Engine
        self.engine = QQmlApplicationEngine()
        self.engine.rootContext().setContextProperty("backend", self.backend)
        self.engine.load(QtCore.QUrl.fromLocalFile(QML_MAIN_FILE_PATH))
        
        # Check if QML loaded successfully
        if not self.engine.rootObjects(): sys.exit(-1)

        # Start the app
        self.exit_code = self.app.exec()

        # Exit
        sys.exit(self.exit_code)


def run():
    # Create the App and run it
    app = App()
