import sys
from pathlib import Path

import PySide6.QtCore as QtCore
from PySide6.QtCore import QObject, Property, Slot, QSettings, QStandardPaths, Signal, QThread
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine

from backend import library, cache_manager

import resources_rc


# Set Organization Name and Domain
QtCore.QCoreApplication.setOrganizationName("PolarTea Studios")
QtCore.QCoreApplication.setOrganizationDomain("dev.polartblock.ptbanime")
QtCore.QCoreApplication.setApplicationName("PTBAnime")
QtCore.QCoreApplication.setApplicationVersion("2.0.7")

# Set important Folder and File Paths
QML_FOLDER_PATH = Path(__file__).parents[1] / "qml"
QML_MAIN_FILE_PATH = QML_FOLDER_PATH / "Main.qml"

APPDATA = QStandardPaths.writableLocation(QStandardPaths.AppDataLocation)
print("Debug: AppData Path:", APPDATA)


# The Backend
class BackEnd(QObject):
    # Create signals
    animeLibraryChanged = Signal()

    def __init__(self, settings, cache_manager):
        super().__init__()
        self.settings: QSettings = settings
        self.cache_manager: cache_manager.CacheManager = cache_manager
        self._thread = None; self._worker = None
        self.search_filter = ""

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
    
    # Set a search filter
    @Slot(str)
    def set_search_filter(self, new):
        self.search_filter = new
        self.animeLibraryChanged.emit()

    # Fetch anime data from AniList, process, and add to cache
    @Slot()
    def update_cache(self):
        # Don't stack scans because it might do weird things
        if getattr(self, "_thread", None) is not None and self._thread.isRunning(): return

        # Setup Thread
        self._thread = QThread()
        self._worker = cache_manager.CacheWorker(self.cache_manager, self.settings.value("app/anime_folder_path"))
        self._worker.moveToThread(self._thread)

        # Connect the signals
        self._thread.started.connect(self._worker.run)
        self._worker.animeAdded.connect(self.animeLibraryChanged)
        self._worker.finished.connect(self._thread.quit)
        self._worker.finished.connect(self._worker.deleteLater)
        self._thread.finished.connect(self._on_cache_thread_finished)
        self._thread.finished.connect(self._thread.deleteLater)

        # Starta la magic
        self._thread.start()
    
    # Clean up worker thread after they finish working
    def _on_cache_thread_finished(self):
        self._thread = None; self._worker = None
    
    # Get homepage grid model
    @Slot(result=list)
    def get_anime(self):
        return library.get_home_page_grid(self.cache_manager.cache, self.search_filter)
    
    # Set properties for QML
    libraryAnime = Property(list, get_anime, notify=animeLibraryChanged)


# The Main Application
class App:
    def __init__(self):
        # Load Settings
        self.settings = QSettings("PolarTea Studios", "PTBAnime")

        # Create cache manager
        self.cache_manager = cache_manager.CacheManager(APPDATA)

        # If there's no setting for app/first_time, it's the first time running
        if not self.settings.contains("app/first_time"):
            self.settings.setValue("app/first_time", True)

        # Create the Backend
        self.backend = BackEnd(self.settings, self.cache_manager)

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

        # Start the app
        self.exit_code = self.app.exec()

        # Save the Cache
        self.cache_manager.save()

        # Exit normally
        sys.exit(self.exit_code)


def run():
    # Create the App and run it
    app = App()
