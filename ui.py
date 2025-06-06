import os
import json
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Gdk, Gio, Pango, GdkPixbuf

base_dir = os.path.dirname(os.path.abspath(__file__))
settings_path = os.path.join(base_dir, "settings.json")
with open(settings_path, "r") as f:
    settings = json.load(f)
anime_dir = settings.get("anime_folder", os.path.join(os.path.expanduser("~"), "Anime"))
ptbanime_data_file = {
    "title": "Anime Title",          # Title
    "title-en": "Anime Title (en)",  # Title in english
    "last-episode": 1,               # Last episode you watched
    "last-episode-timestamp": 0,     # Where you last left off
    "description": "Default description. You should edit the PTBAnime-info.json file in the folder of this anime to change the description, you can also change other stuff too, like the english and japanese titles. Changing the titles won't change your folder name. "
}


class AnimeCard(Gtk.Box):  # Creates a card (Grid Item) for a Grid
    def __init__(self, title="Placeholder Title", image_path=None):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        self.label = Gtk.Label(label=title)
        self.title = title
        self.size = (280, 400)

        if image_path is None:
            image_path = os.path.join(base_dir, "assets", "anime_card_thumbnail.png")
        bad_cover_texture = GdkPixbuf.Pixbuf.new_from_file(image_path)
        cover_texture = bad_cover_texture.scale_simple(self.size[0], self.size[1], GdkPixbuf.InterpType.BILINEAR)

        self.set_size_request(self.size[0], self.size[1])
        self.set_spacing(0)
        self.set_hexpand(False)
        self.set_vexpand(False)
        self.set_halign(Gtk.Align.CENTER)
        self.set_valign(Gtk.Align.CENTER)
        self.set_margin_start(10)
        self.set_margin_end(10)
        self.set_margin_top(30)
        self.set_margin_bottom(30)
        self.set_css_classes(["anicard-box"])

        self.cover = Gtk.Picture.new_for_pixbuf(cover_texture)
        self.cover.set_content_fit(Gtk.ContentFit.FILL)
        self.cover.set_size_request(self.size[0], self.size[1])
        self.cover.set_css_classes(["grid-item"])
        self.cover.set_hexpand(False)
        self.cover.set_vexpand(False)
        self.cover.set_halign(Gtk.Align.CENTER)
        self.cover.set_valign(Gtk.Align.START)
        self.append(self.cover)

        self.label.set_size_request(self.size[0] - 20, 40)
        self.label.set_valign(Gtk.Align.START)
        self.label.set_hexpand(False)
        self.label.set_vexpand(True)
        self.label.set_halign(Gtk.Align.CENTER)
        self.label.set_valign(Gtk.Align.FILL)
        self.label.set_wrap(True)
        self.label.set_wrap_mode(Pango.WrapMode.WORD)
        self.label.set_lines(2)
        self.label.set_ellipsize(Pango.EllipsizeMode.MIDDLE)
        self.label.set_justify(Gtk.Justification.CENTER)
        self.append(self.label)

def fetch_anime_folder():
    found_anime = [name for name in os.listdir(anime_dir) if os.path.isdir(os.path.join(anime_dir, name))]
    print(found_anime)
    return found_anime

def get_anime_info(select_anime_folder):  # Gets the anime info. Testing...
    # select_anime_folder is the anime folder name
    full_select_anime_folder = os.path.join(anime_dir, select_anime_folder)  # Full anime folder path
    print(full_select_anime_folder)
    data_file_path = os.path.join(str(full_select_anime_folder), "PTBAnime-info.json")  # Full data file path
    cover_image_path = os.path.join(str(base_dir), "assets", "anime_card_thumbnail.png")  # Default cover image
    for ext in [".jpg", "jpeg", "png"]:  # Find cover image. If not found default cover image is used
        candidate = os.path.join(str(full_select_anime_folder), f"cover.{ext}")
        if os.path.isfile(candidate):
            cover_image_path = candidate
            print("Found cover")
            break
    if os.path.isfile(data_file_path):
        # Get PTBAnime-data.json
        print("Found PTBAnime data file!")
        with open(data_file_path, "r") as F:
            anime_data = json.load(F)
            print(anime_data)
        # Check for missing keys, and fill them if not present
        missing = False
        if "title" not in anime_data:
            missing = True
            anime_data["title"] = ptbanime_data_file["title"]
            print("Filled in missing title")
        if "title-en" not in anime_data:
            missing = True
            anime_data["title-en"] = ptbanime_data_file["title-en"]
            print("Filled in missing title-en")
        if "last-episode" not in anime_data:
            missing = True
            anime_data["last-episode"] = ptbanime_data_file["last-episode"]
            print("Filled in missing last-episode")
        if "last-episode-timestamp" not in anime_data:
            missing = True
            anime_data["last-episode-timestamp"] = ptbanime_data_file["last-episode-timestamp"]
            print("Filled in missing last-episode-timestamp")
        if "description" not in anime_data:
            missing = True
            anime_data["description"] = ptbanime_data_file["description"]
            print("Filled in missing description")
        if missing:
            with open(data_file_path, "w") as F:
                json.dump(anime_data, F, indent=4)
    else:  # Data file doesn't exist. Create data file automatically
        print("Creating new PTBAnime data file...")
        anime_data = ptbanime_data_file.copy()
        anime_data["title"] = select_anime_folder
        anime_data["title-en"] = select_anime_folder
        with open(data_file_path, "w") as F:
            json.dump(anime_data, F, indent=4)
        print("Created new PTBAnime data file!")
    return anime_data, cover_image_path  # Return the anime data and cover image path

def select_folder(window: Gtk.Window, on_folder_selected: callable):
    dialog = Gtk.FileChooserNative.new(
        title="Select the folder where your Anime is",
        parent=window,
        action=Gtk.FileChooserAction.SELECT_FOLDER,
        accept_label="Select",
        cancel_label="Cancel"
    )

    def on_response(_dialog, response_id):
        folder = None
        if response_id == Gtk.ResponseType.ACCEPT:
            folder = _dialog.get_file().get_path()
            print("Selected folder:", folder)
        else:
            print("Cancelled")
        _dialog.destroy()
        on_folder_selected(folder)  # Call back

    dialog.connect("response", on_response)
    dialog.show()


def update_anime_dir():
    global anime_dir
    anime_dir = settings.get("anime_folder", os.path.join(os.path.expanduser("~"), "Anime"))

def check_settings():  # Fix settings options if empty
    if "anime_folder" not in settings or settings["anime_folder"] == "":
        settings["anime_folder"] = os.path.expanduser("~")
    if "title-language" not in settings or settings["title-language"] == "":
        settings["title-language"] = "en"
    if "first-time" not in settings or settings["first-time"] == "":
        settings["first-time"] = True
    with open(settings_path, "w") as F:
        json.dump(settings, F, indent=4)
    update_anime_dir()
