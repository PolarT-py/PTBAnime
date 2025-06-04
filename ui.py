import os
import json
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Gdk, Gio, Pango

base_dir = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(base_dir, "settings.json"), "r") as f:
    settings = json.load(f)
    anime_dir = settings["anime_folder"]  # Where all your anime is stored
ptbanime_data_file = {
    "title": "Anime Title",          # Title
    "title-en": "Anime Title (en)",  # Title in english
    "last-episode": 1,               # Last episode you watched
    "last-episode-timestamp": 0      # Where you last left off
}


class AnimeCard(Gtk.Box):  # Creates a card (Grid Item) for the Grid that shows all the anime
    def __init__(self, title="Placeholder Title", image_path=None):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        self.label = Gtk.Label(label=title)

        if image_path is None:
            image_path = os.path.join(base_dir, "assets", "anime_card_thumbnail.png")
        cover_texture = Gdk.Texture.new_from_file(Gio.File.new_for_path(image_path))

        self.set_size_request(320, 440)
        # self.set_hexpand(False)
        # self.set_vexpand(False)
        self.set_halign(Gtk.Align.CENTER)
        self.set_valign(Gtk.Align.CENTER)
        self.set_margin_start(30)
        self.set_margin_end(30)
        self.set_margin_top(30)
        self.set_margin_bottom(30)
        self.set_css_classes(["max-box"])
        self.cover = Gtk.Picture.new_for_paintable(cover_texture)
        self.cover.set_size_request(320, 400)
        self.cover.set_content_fit(Gtk.ContentFit.COVER)
        self.cover.set_css_classes(["grid-item"])
        self.cover.set_hexpand(False)
        self.cover.set_vexpand(False)
        self.cover.set_halign(Gtk.Align.CENTER)
        self.cover.set_valign(Gtk.Align.FILL)
        # self.cover.set_content_fit(Gtk.ContentFit.SCALE_DOWN)
        self.label.set_hexpand(False)
        self.label.set_vexpand(True)
        self.label.set_halign(Gtk.Align.CENTER)
        self.label.set_valign(Gtk.Align.FILL)
        self.label.set_wrap(True)
        self.label.set_wrap_mode(Pango.WrapMode.WORD)
        self.label.set_lines(2)
        self.label.set_ellipsize(Pango.EllipsizeMode.MIDDLE)

        self.append(self.cover)
        self.append(self.label)
        self._load_css()
    def _load_css(self):
        css = b"""
        .grid-item {
            border-radius: 21px;
            background-clip: padding-box;
            overflow: hidden;
        }
        .max-box {
            background-color: green;
        }
        """
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(css)
        Gtk.StyleContext.add_provider_for_display(Gdk.Display.get_default(), css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

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
    else:  # Data file doesn't exist. Create data file automatically
        print("Creating new PTBAnime data file...")
        anime_data = ptbanime_data_file.copy()
        anime_data["title"] = select_anime_folder
        anime_data["title-en"] = select_anime_folder
        with open(data_file_path, "w") as F:
            json.dump(anime_data, F, indent=4)
        print("Created new PTBAnime data file!")
    return anime_data, cover_image_path  # Return the anime data and cover image path
