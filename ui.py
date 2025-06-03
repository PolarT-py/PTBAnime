import os
import json

import gi

gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Gdk, GLib

from anime_index import index_anime_folders, VIDEO_EXTENSIONS, ANIME_JSON_FILE

base_dir = os.path.dirname(os.path.abspath(__file__))

settings_file_path = os.path.join(base_dir, "settings.json")

if not os.path.exists(settings_file_path):
    with open(settings_file_path, "w") as f:
        json.dump({"first_time": True, "anime_folder": ""}, f, indent=4)


with open(settings_file_path, "r") as f:
    app_settings = json.load(f)
    anime_dir = app_settings.get("anime_folder", "")  # This will be the indexed root folder

ptbanime_data_file = {
    "title": "Anime Title",
    "title-en": "Anime Title (en)",
    "last-episode": 1,
    "last-episode-timestamp": 0
}


class AnimeCard(Gtk.Button):
    def __init__(self, anime_data, placeholder_path=None, on_card_clicked_callback=None):
        super().__init__()  # Call Gtk.Button constructor

        self.anime_data = anime_data
        self.on_card_clicked_callback = on_card_clicked_callback

        inner_content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        inner_content_box.set_vexpand(False)
        inner_content_box.set_hexpand(False)
        inner_content_box.set_valign(Gtk.Align.START)
        inner_content_box.set_halign(Gtk.Align.CENTER)

        title = anime_data.get("name", "Unknown Anime")

        banner_filename = anime_data.get("banner_picture")


        banner_path = None
        if banner_filename and anime_data.get("folder_path"):
            banner_path = os.path.join(anime_data["folder_path"], banner_filename)


        if banner_path and os.path.exists(banner_path):
            self.image = Gtk.Image.new_from_file(banner_path)
        elif placeholder_path and os.path.exists(placeholder_path):
            self.image = Gtk.Image.new_from_file(placeholder_path)
        else:
            self.image = Gtk.Image.new_from_icon_name("image-missing")

        self.image.set_pixel_size(150)
        self.image.set_vexpand(False)
        self.image.set_hexpand(False)

        self.label = Gtk.Label(label=title)
        self.label.set_wrap(True)
        self.label.set_max_width_chars(15)
        self.label.set_xalign(0.5)

        inner_content_box.append(self.image)
        inner_content_box.append(self.label)

        self.set_child(inner_content_box)
        self.connect("clicked", self._on_card_clicked)

        self.add_css_class("anime-card")
        self.add_css_class("flat-button")
        self.set_has_frame(False)

    def _on_card_clicked(self, button):
        if self.on_card_clicked_callback:
            self.on_card_clicked_callback(self.anime_data)



class SeasonCard(Gtk.Button):
    def __init__(self, season_data, anime_folder_path, placeholder_path=None, on_card_clicked_callback=None):
        super().__init__()

        self.season_data = season_data
        self.on_card_clicked_callback = on_card_clicked_callback

        inner_content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        inner_content_box.set_vexpand(False)
        inner_content_box.set_hexpand(False)
        inner_content_box.set_valign(Gtk.Align.START)
        inner_content_box.set_halign(Gtk.Align.CENTER)

        title = f"Season {season_data.get('season_number', 'Unknown')}"


        banner_filename = season_data.get("banner_picture")

        banner_path = None
        if banner_filename and season_data.get("season_folder_path"):
            banner_path = os.path.join(season_data["season_folder_path"], banner_filename)
        elif banner_filename and anime_folder_path:  # Fallback to anime root folder if season_folder_path is missing in banner_path construction
            banner_path = os.path.join(anime_folder_path, banner_filename)


        if banner_path and os.path.exists(banner_path):
            self.image = Gtk.Image.new_from_file(banner_path)
        elif placeholder_path and os.path.exists(placeholder_path):
            self.image = Gtk.Image.new_from_file(placeholder_path)
        else:
            self.image = Gtk.Image.new_from_icon_name("image-missing")

        self.image.set_pixel_size(150)
        self.image.set_vexpand(False)
        self.image.set_hexpand(False)

        self.label = Gtk.Label(label=title)
        self.label.set_wrap(True)
        self.label.set_max_width_chars(15)
        self.label.set_xalign(0.5)

        inner_content_box.append(self.image)
        inner_content_box.append(self.label)

        self.set_child(inner_content_box)
        self.connect("clicked", self._on_card_clicked)

        self.add_css_class("anime-card")  # Re-use the same styling for consistency
        self.add_css_class("flat-button")
        self.set_has_frame(False)

    def _on_card_clicked(self, button):
        if self.on_card_clicked_callback:
            self.on_card_clicked_callback(self.season_data)



class EpisodeCard(Gtk.Button):
    def __init__(self, episode_data, placeholder_path=None, on_card_clicked_callback=None):
        super().__init__()

        self.episode_data = episode_data
        self.on_card_clicked_callback = on_card_clicked_callback

        inner_content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        inner_content_box.set_vexpand(False)
        inner_content_box.set_hexpand(False)
        inner_content_box.set_valign(Gtk.Align.START)
        inner_content_box.set_halign(Gtk.Align.CENTER)

        title = episode_data.get("name", f"Episode {episode_data.get('episode_number', 'Unknown')}")


        thumbnail_path = episode_data.get("thumbnail_path")


        if thumbnail_path and os.path.exists(thumbnail_path):
            self.image = Gtk.Image.new_from_file(thumbnail_path)
        elif placeholder_path and os.path.exists(placeholder_path):
            self.image = Gtk.Image.new_from_file(placeholder_path)
        else:
            self.image = Gtk.Image.new_from_icon_name("video-x-generic") # Generic video icon

        self.image.set_pixel_size(150)
        self.image.set_vexpand(False)
        self.image.set_hexpand(False)

        self.label = Gtk.Label(label=title)
        self.label.set_wrap(True)
        self.label.set_max_width_chars(15)
        self.label.set_xalign(0.5)

        inner_content_box.append(self.image)
        inner_content_box.append(self.label)

        self.set_child(inner_content_box)
        self.connect("clicked", self._on_card_clicked)


        self.add_css_class("flat-button")
        self.set_has_frame(False)

    def _on_card_clicked(self, button):
        if self.on_card_clicked_callback:
            self.on_card_clicked_callback(self.episode_data)



class SeasonScreen(Gtk.Box):
    def __init__(self, anime_data, placeholder_path, on_season_card_clicked_callback, on_back_button_clicked_callback):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.set_margin_top(10)
        self.set_margin_bottom(10)
        self.set_margin_start(10)
        self.set_margin_end(10)
        self.set_vexpand(True)
        self.set_hexpand(True)

        self.anime_data = anime_data
        self.placeholder_path = placeholder_path
        self.on_season_card_clicked_callback = on_season_card_clicked_callback
        self.on_back_button_clicked_callback = on_back_button_clicked_callback


        back_button = Gtk.Button(label="Back to Anime List")
        back_button.set_halign(Gtk.Align.START)
        back_button.connect("clicked", lambda x: self.on_back_button_clicked_callback())
        self.append(back_button)

        header_label = Gtk.Label(label=f"Seasons for {anime_data.get('name', 'Unknown Anime')}")
        header_label.set_justify(Gtk.Justification.CENTER)
        header_label.add_css_class("title")
        header_label.set_halign(Gtk.Align.START)
        self.append(header_label)


        flowbox = Gtk.FlowBox()
        flowbox.set_selection_mode(Gtk.SelectionMode.NONE)
        flowbox.set_homogeneous(False)
        flowbox.set_max_children_per_line(5)
        flowbox.set_column_spacing(20)
        flowbox.set_row_spacing(20)
        flowbox.set_valign(Gtk.Align.START)
        flowbox.set_margin_top(10)
        flowbox.set_margin_bottom(10)
        flowbox.set_margin_start(10)
        flowbox.set_margin_end(10)

        seasons = anime_data.get("seasons", [])
        if not seasons:
            no_seasons_label = Gtk.Label(label="No seasons found for this anime.")
            no_seasons_label.set_halign(Gtk.Align.CENTER)
            self.append(no_seasons_label)
        else:
            for season_item in seasons:
                card = SeasonCard(
                    season_data=season_item,
                    anime_folder_path=anime_data.get("folder_path"),  # Pass anime folder for banner resolution
                    placeholder_path=self.placeholder_path,
                    on_card_clicked_callback=self.on_season_card_clicked_callback
                )
                flowbox.append(card)

        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_vexpand(True)
        scrolled_window.set_hexpand(True)
        scrolled_window.set_child(flowbox)
        self.append(scrolled_window)



class EpisodeScreen(Gtk.Box):
    def __init__(self, season_data, anime_name, placeholder_path, on_episode_card_clicked_callback, on_back_button_clicked_callback):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.set_margin_top(10)
        self.set_margin_bottom(10)
        self.set_margin_start(10)
        self.set_margin_end(10)
        self.set_vexpand(True)
        self.set_hexpand(True)

        self.season_data = season_data
        self.anime_name = anime_name
        self.placeholder_path = placeholder_path
        self.on_episode_card_clicked_callback = on_episode_card_clicked_callback
        self.on_back_button_clicked_callback = on_back_button_clicked_callback


        back_button = Gtk.Button(label=f"Back to Seasons for {self.anime_name}")
        back_button.set_halign(Gtk.Align.START)
        back_button.connect("clicked", lambda x: self.on_back_button_clicked_callback())
        self.append(back_button)

        header_label = Gtk.Label(label=f"Episodes for Season {season_data.get('season_number', 'Unknown')} of {self.anime_name}")
        header_label.set_justify(Gtk.Justification.CENTER)
        header_label.add_css_class("title")
        header_label.set_halign(Gtk.Align.START)
        self.append(header_label)

        flowbox = Gtk.FlowBox()
        flowbox.set_selection_mode(Gtk.SelectionMode.NONE)
        flowbox.set_homogeneous(False)
        flowbox.set_max_children_per_line(5)
        flowbox.set_column_spacing(20)
        flowbox.set_row_spacing(20)
        flowbox.set_valign(Gtk.Align.START)
        flowbox.set_margin_top(10)
        flowbox.set_margin_bottom(10)
        flowbox.set_margin_start(10)
        flowbox.set_margin_end(10)

        episodes = season_data.get("episodes", [])
        if not episodes:
            no_episodes_label = Gtk.Label(label="No episodes found for this season.")
            no_episodes_label.set_halign(Gtk.Align.CENTER)
            self.append(no_episodes_label)
        else:
            for episode_item in episodes:
                card = EpisodeCard(
                    episode_data=episode_item,
                    placeholder_path=self.placeholder_path,
                    on_card_clicked_callback=self.on_episode_card_clicked_callback
                )
                flowbox.append(card)

        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_vexpand(True)
        scrolled_window.set_hexpand(True)
        scrolled_window.set_child(flowbox)
        self.append(scrolled_window)




def get_anime_info(select_anime_folder):
    full_select_anime_folder = os.path.join(anime_dir, select_anime_folder)
    print(full_select_anime_folder)
    data_file_path = os.path.join(str(full_select_anime_folder), "PTBAnime-info.json")
    cover_image_path = os.path.join(str(base_dir), "assets", "anime_card_thumbnail.png")
    for ext in [".jpg", "jpeg", "png"]:
        candidate = os.path.join(str(full_select_anime_folder), f"cover{ext}")
        if os.path.isfile(candidate):
            cover_image_path = candidate
            break
    if os.path.isfile(data_file_path):
        print("Found PTBAnime data file!")
        with open(data_file_path, "r") as F:
            anime_data = json.load(F)
            print(anime_data)
    else:
        print("Creating new PTBAnime data file...")
        anime_data = ptbanime_data_file.copy()
        anime_data["title"] = select_anime_folder
        anime_data["title-en"] = select_anime_folder
        with open(data_file_path, "w") as F:
            json.dump(anime_data, F, indent=4)
        print("Created new PTBAnime data file!")
    return anime_data, cover_image_path


class FirstTimeSetupWindow(Gtk.ApplicationWindow):
    def __init__(self, app, *args, **kwargs):
        super().__init__(application=app, *args, **kwargs)
        self.set_default_size(500, 400)
        self.set_title("PTBAnime - First Time Setup")
        self.set_modal(True)

        self.selected_folder_path = ""

        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        main_box.set_margin_top(20)
        main_box.set_margin_bottom(20)
        main_box.set_margin_start(20)
        main_box.set_margin_end(20)
        self.set_child(main_box)

        header_label = Gtk.Label(label="Welcome to PTBAnime!\nLet's get your anime library set up.")
        header_label.set_justify(Gtk.Justification.CENTER)
        header_label.add_css_class("title")
        main_box.append(header_label)

        description_label = Gtk.Label(
            label="Please select the root folder containing all your anime series.\n"
                  "Each anime series should ideally be in its own subfolder, potentially with 'Season X' subfolders inside."
        )
        description_label.set_wrap(True)
        description_label.set_justify(Gtk.Justification.CENTER)
        main_box.append(description_label)

        folder_selection_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        main_box.append(folder_selection_box)

        folder_label = Gtk.Label(label="Selected Anime Root Folder:")
        folder_label.set_halign(Gtk.Align.START)
        folder_selection_box.append(folder_label)

        self.path_label = Gtk.Label(label="No folder selected")
        self.path_label.set_halign(Gtk.Align.START)
        self.path_label.set_wrap(True)
        folder_selection_box.append(self.path_label)

        change_folder_button = Gtk.Button(label="Change Folder")
        change_folder_button.connect("clicked", self.on_change_folder_clicked)
        folder_selection_box.append(change_folder_button)

        index_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        index_box.set_halign(Gtk.Align.CENTER)
        main_box.append(index_box)

        self.index_button = Gtk.Button(label="Start Indexing")
        self.index_button.connect("clicked", self.on_start_indexing_clicked)
        index_box.append(self.index_button)

        self.spinner = Gtk.Spinner()
        index_box.append(self.spinner)

        self.status_label = Gtk.Label(label="")
        main_box.append(self.status_label)

    def on_change_folder_clicked(self, button):
        dialog = Gtk.FileChooserDialog(
            title="Select Anime Root Folder",
            transient_for=self,
            action=Gtk.FileChooserAction.SELECT_FOLDER,
        )
        dialog.add_buttons(
            "_Cancel", Gtk.ResponseType.CANCEL,
            "_Select", Gtk.ResponseType.OK,
        )

        dialog.connect("response", self.on_file_chooser_response)
        dialog.present()

    def on_file_chooser_response(self, dialog, response):
        if response == Gtk.ResponseType.OK:
            self.selected_folder_path = dialog.get_file().get_path()
            self.path_label.set_label(self.selected_folder_path)
        dialog.destroy()

    def on_start_indexing_clicked(self, button):
        if not self.selected_folder_path or not os.path.isdir(self.selected_folder_path):
            self.show_message_dialog("No Folder Selected", "Please select a valid root folder to index.")
            return

        self.index_button.set_sensitive(False)
        self.spinner.start()
        self.status_label.set_label("Indexing in progress...")

        GLib.idle_add(self._perform_indexing_and_update_settings)

    def _perform_indexing_and_update_settings(self):
        try:
            indexed_count = index_anime_folders(self.selected_folder_path)
            self.status_label.set_label(f"Indexing complete! Found {indexed_count} anime series.")

            current_settings = {}
            if os.path.exists(settings_file_path):
                with open(settings_file_path, "r") as f:
                    current_settings = json.load(f)

            current_settings["first_time"] = False
            current_settings["anime_folder"] = self.selected_folder_path
            with open(settings_file_path, "w") as f:
                json.dump(current_settings, f, indent=4)

            self.show_message_dialog("Setup Complete",
                                     "Your anime library has been indexed. Please restart the application for the main view.",
                                     Gtk.MessageType.INFO)
            self.get_application().quit()
        except Exception as e:
            self.status_label.set_label(f"Indexing failed: {e}")
            self.show_message_dialog("Indexing Error", f"An error occurred during indexing: {e}", Gtk.MessageType.ERROR)
        finally:
            self.spinner.stop()
            self.index_button.set_sensitive(True)
        return False

    def show_message_dialog(self, title, message, message_type=Gtk.MessageType.INFO):
        dialog = Gtk.MessageDialog(
            transient_for=self,
            modal=True,
            message_type=message_type,
            buttons=Gtk.ButtonsType.OK,
            text=title,
            secondary_text=message,
        )
        dialog.connect("response", lambda d, r: d.destroy())
        dialog.present()


def create_anime_display_flowbox(placeholder_path, on_anime_card_clicked_callback=None):
    flowbox = Gtk.FlowBox()
    flowbox.set_selection_mode(Gtk.SelectionMode.NONE)  # Individual cards handle clicks
    flowbox.set_homogeneous(False)
    flowbox.set_max_children_per_line(5)  # Adjust as desired
    flowbox.set_column_spacing(20)
    flowbox.set_row_spacing(20)
    flowbox.set_valign(Gtk.Align.START)  # Align items to the top
    flowbox.set_margin_top(10)
    flowbox.set_margin_bottom(10)
    flowbox.set_margin_start(10)
    flowbox.set_margin_end(10)

    anime_data_from_json = {"animes": []}
    if os.path.exists(ANIME_JSON_FILE):
        try:
            with open(ANIME_JSON_FILE, "r") as f:
                anime_data_from_json = json.load(f)
        except json.JSONDecodeError:
            print(f"Warning: {ANIME_JSON_FILE} is corrupted or empty. Cannot display library.")

    for anime_item in anime_data_from_json.get("animes", []):
        card = AnimeCard(
            anime_data=anime_item,
            placeholder_path=placeholder_path,
            on_card_clicked_callback=on_anime_card_clicked_callback
        )
        flowbox.append(card)


    scrolled_window = Gtk.ScrolledWindow()
    scrolled_window.set_vexpand(True)
    scrolled_window.set_hexpand(True)
    scrolled_window.set_child(flowbox)

    return scrolled_window