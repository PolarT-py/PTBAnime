import sys
import os
import json

import gi

gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib, Gdk, Gio  # Import Gio for file operations

# Import the UI classes and the new display function from ui.py
from ui import FirstTimeSetupWindow, create_anime_display_flowbox, SeasonScreen, EpisodeScreen # Import EpisodeScreen
# Import the VideoPlayerWindow
from video import VideoPlayerWindow

# Path to settings.json (assuming it's in the same directory as main.py)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SETTINGS_FILE_PATH = os.path.join(BASE_DIR, "settings.json")
ANIME_JSON_FILE = "anime.json"  # Defined in anime_index.py, but useful here for initial check


# Function to ensure settings.json exists and has default values
def ensure_settings_exist():
    if not os.path.exists(SETTINGS_FILE_PATH):
        default_settings = {
            "first_time": True,
            "anime_folder": ""  # Placeholder, will be updated by setup
        }
        with open(SETTINGS_FILE_PATH, "w") as f:
            json.dump(default_settings, f, indent=4)
        return default_settings
    else:
        try:
            with open(SETTINGS_FILE_PATH, "r") as f:
                settings = json.load(f)
                # Ensure 'first_time' key exists
                if "first_time" not in settings:
                    settings["first_time"] = True
                    with open(SETTINGS_FILE_PATH, "w") as f:  # Update settings file
                        json.dump(settings, f, indent=4)
                return settings
        except json.JSONDecodeError:
            print("Warning: settings.json is corrupted. Recreating with defaults.")
            os.remove(SETTINGS_FILE_PATH)  # Remove corrupted file
            return ensure_settings_exist()  # Re-call to create new default settings


# Function to ensure dummy assets for AnimeCard exist
def ensure_assets_exist():
    assets_dir = os.path.join(BASE_DIR, "assets")
    if not os.path.exists(assets_dir):
        os.makedirs(assets_dir)
    dummy_thumbnail_path = os.path.join(assets_dir, "anime_card_thumbnail.png")
    if not os.path.exists(dummy_thumbnail_path):
        try:
            # Attempt to create a tiny transparent PNG if Pillow is installed
            from PIL import Image
            img = Image.new('RGBA', (1, 1), (0, 0, 0, 0))
            img.save(dummy_thumbnail_path)
        except ImportError:
            # Fallback if Pillow is not installed
            print(
                "Pillow not found. Please create 'assets/anime_card_thumbnail.png' manually to avoid Gtk.Image errors.")
            print("You can use any small PNG image and name it 'anime_card_thumbnail.png' in the 'assets' folder.")
    return dummy_thumbnail_path


class MainApplication(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.polartblock.ptbanime")
        GLib.set_application_name("PTBAnime")
        self.settings = ensure_settings_exist()
        self.dummy_thumbnail_path = ensure_assets_exist()
        self.main_window = None  # To hold the main application window instance
        self.current_anime_data = None # To store the currently viewed anime data for back navigation
        self.current_season_data = None # To store the currently viewed season data for back navigation

    def do_activate(self):
        # --- Apply CSS for flat buttons ---
        css_provider = Gtk.CssProvider()
        css = b"""
        .flat-button {
          background-color: transparent;
          border: none;
          padding: 0;
          margin: 0;
          box-shadow: none; /* Ensure no shadow */
        }
        .flat-button:hover {
          background-color: rgba(200, 200, 200, 0.1); /* Subtle hover effect */
        }
        .flat-button:active {
          background-color: rgba(150, 150, 150, 0.2); /* Subtle active effect */
        }
        /* Optional: Basic styling for anime-card, if not already defined */
        .anime-card {
            border-radius: 8px; /* Rounded corners for the card itself */
            overflow: hidden; /* Ensures content respects border-radius */
            /* Add other card styling like background-color, border, etc. */
            background-color: #303030; /* Dark background for cards */
            border: 1px solid #404040;
        }
        .anime-card label {
            padding: 5px; /* Padding for the label text */
            color: #E0E0E0; /* Light text color */
        }
        """
        css_provider.load_from_data(css)
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(), css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
        # --- End CSS Application ---

        if self.settings.get("first_time", True):
            win = FirstTimeSetupWindow(self)
            self.main_window = win  # Assign the setup window to main_window
        else:
            if not self.main_window:  # Create main window only if it doesn't exist
                self.main_window = Gtk.ApplicationWindow(application=self, title="PTBAnime")
                self.main_window.set_default_size(800, 600)
                self.main_window.set_size_request(600, 400)
                self.main_window.set_resizable(True)

                self.headerbar = Gtk.HeaderBar()
                self.headerbar.set_title_widget(Gtk.Label(label="PTBAnime - Library"))
                self.main_window.set_titlebar(self.headerbar)

                # Back button for navigation
                self.back_button = Gtk.Button.new_from_icon_name("go-previous-symbolic")
                self.back_button.set_tooltip_text("Go Back")
                self.back_button.connect("clicked", self._on_back_button_clicked)
                self.headerbar.pack_start(self.back_button)
                self.back_button.set_visible(False)  # Hide initially

                self.headerbar.pack_end(Gtk.MenuButton(icon_name="open-menu-symbolic"))
                self.headerbar.pack_start(Gtk.MenuButton(icon_name="view-refresh"))

                # Use a Gtk.Stack to manage different views
                self.stack = Gtk.Stack()
                self.stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
                self.stack.set_transition_duration(300)

                # Main library view
                self.library_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
                self.library_box.set_margin_top(10)
                self.library_box.set_margin_bottom(10)
                self.library_box.set_margin_start(10)
                self.library_box.set_margin_end(10)

                library_label = Gtk.Label(label="Your Anime Library:")
                library_label.set_justify(Gtk.Justification.LEFT)
                library_label.set_hexpand(True)
                library_label.set_vexpand(False)
                library_label.set_halign(Gtk.Align.START)
                library_label.add_css_class("title")

                search_bar = Gtk.SearchBar()  # Placeholder for future search functionality

                self.anime_display_area = create_anime_display_flowbox(
                    self.dummy_thumbnail_path,
                    on_anime_card_clicked_callback=self._on_anime_card_clicked
                )
                self.anime_display_area.set_vexpand(True)

                self.library_box.append(library_label)
                self.library_box.append(search_bar)
                self.library_box.append(self.anime_display_area)

                self.stack.add_named(self.library_box, "library_view")
                self.main_window.set_child(self.stack)  # Set the stack as the child of the window

            # Always show the main window if it exists
            self.main_window.present()

    def _on_anime_card_clicked(self, anime_data):
        """
        Callback function when an AnimeCard is clicked.
        Switches to the SeasonScreen for the selected anime.
        """
        print(f"Anime Card Clicked: {anime_data.get('name')}")
        self.current_anime_data = anime_data # Store current anime data

        # Create the SeasonScreen for the selected anime
        season_screen = SeasonScreen(
            anime_data=anime_data,
            placeholder_path=self.dummy_thumbnail_path,
            on_season_card_clicked_callback=self._on_season_card_clicked,
            on_back_button_clicked_callback=self._show_main_anime_list # Pass callback for back button
        )

        # Add the season screen to the stack if not already present
        stack_child_name = f"season_view_{anime_data.get('name', 'unknown_anime').replace(' ', '_')}"
        if not self.stack.get_child_by_name(stack_child_name):
            self.stack.add_named(season_screen, stack_child_name)

        # Switch to the season screen
        self.stack.set_visible_child_name(stack_child_name)
        self.headerbar.get_title_widget().set_label(anime_data.get('name', 'Seasons'))
        self.back_button.set_visible(True)  # Show back button

    def _on_season_card_clicked(self, season_data):
        """
        Callback function when a SeasonCard is clicked.
        Switches to the EpisodeScreen for the selected season.
        """
        print(f"Season Card Clicked: Season {season_data.get('season_number')}")
        self.current_season_data = season_data # Store current season data

        # Create the EpisodeScreen for the selected season
        episode_screen = EpisodeScreen(
            season_data=season_data,
            anime_name=self.current_anime_data.get('name', 'Unknown Anime'), # Pass anime name for header
            placeholder_path=self.dummy_thumbnail_path,
            on_episode_card_clicked_callback=self._on_episode_card_clicked,
            on_back_button_clicked_callback=self._show_season_list # Pass callback for back button
        )

        # Add the episode screen to the stack
        stack_child_name = f"episode_view_{self.current_anime_data.get('name', 'unknown').replace(' ', '_')}_season_{season_data.get('season_number', 'unknown')}"
        if not self.stack.get_child_by_name(stack_child_name):
            self.stack.add_named(episode_screen, stack_child_name)

        # Switch to the episode screen
        self.stack.set_visible_child_name(stack_child_name)
        self.headerbar.get_title_widget().set_label(f"Season {season_data.get('season_number')} - {self.current_anime_data.get('name', 'Episodes')}")


    def _on_episode_card_clicked(self, episode_data):
        """
        Callback function when an EpisodeCard is clicked.
        Plays the selected episode.
        """
        print(f"Episode Card Clicked: {episode_data.get('name', f'Episode {episode_data.get('episode_number', 'Unknown')}')}")

        file_path = episode_data.get("file_path")

        if file_path and os.path.exists(file_path):
            print(f"Attempting to play: {file_path}")
            video_window = VideoPlayerWindow(self, file_path)
            video_window.present()
        else:
            print(f"No playable file found for episode: {episode_data.get('name', 'Unknown Episode')}.")
            dialog = Gtk.MessageDialog(
                transient_for=self.main_window,
                modal=True,
                message_type=Gtk.MessageType.WARNING,
                buttons=Gtk.ButtonsType.OK,
                text="No Playable Episode File",
                secondary_text=f"Could not find a valid playable file for this episode: {episode_data.get('name', 'Unknown Episode')}. "
                               f"Please ensure the file exists and is accessible."
            )
            dialog.connect("response", lambda d, r: d.destroy())
            dialog.present()

    def _show_main_anime_list(self):
        """
        Switches the view back to the main anime list.
        """
        self.stack.set_visible_child_name("library_view")
        self.headerbar.get_title_widget().set_label("PTBAnime - Library")
        self.back_button.set_visible(False)
        self.current_anime_data = None # Clear current anime data

    def _show_season_list(self):
        """
        Switches the view back to the season list for the current anime.
        """
        if self.current_anime_data:
            stack_child_name = f"season_view_{self.current_anime_data.get('name', 'unknown_anime').replace(' ', '_')}"
            self.stack.set_visible_child_name(stack_child_name)
            self.headerbar.get_title_widget().set_label(self.current_anime_data.get('name', 'Seasons'))
            self.current_season_data = None # Clear current season data
        else:
            self._show_main_anime_list() # Fallback to main anime list if anime data is missing

    def _on_back_button_clicked(self, button):
        """
        Handles the 'Back' button click to navigate the Gtk.Stack.
        Determines the previous screen based on the current visible child.
        """
        current_child_name = self.stack.get_visible_child_name()

        if current_child_name.startswith("episode_view_"):
            # If on an episode view, go back to the season view
            self._show_season_list()
        elif current_child_name.startswith("season_view_"):
            # If on a season view, go back to the library view
            self._show_main_anime_list()
        # No action if already on the library view or another unhandled screen


if __name__ == "__main__":
    app = MainApplication()
    exit_status = app.run(sys.argv)
    sys.exit(exit_status)