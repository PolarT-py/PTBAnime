import sys
import os
import json

import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk

base_dir = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(base_dir, "settings.json"), "r") as f:
    anime_dir = json.load(f)["anime_folder"]  # Where all your anime is stored
ptbanime_data_file = {
    "title": "Anime Title",          # Title
    "title-en": "Anime Title (en)",  # Title in english
    "last-episode": 1,               # Last episode you watched
    "last-episode-timestamp": 0      # Where you last left off
}


class AnimeCard(Gtk.Box):  # Creates a card (Grid Item) for the Grid that shows all the anime
    def __init__(self, title="Placeholder Title", image_path=None):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        if image_path is None:
            self.image = Gtk.Image.new_from_file(os.path.join(base_dir, "assets", "anime_card_thumbnail.png"))  # anime_card_thumbnail.png is a placeholder thumbnail used when
        else:                                                                                                   #                           no thumbnail is found in the folder
            self.image = Gtk.Image.new_from_file(image_path)  # image_path is the FULL path to the image
        self.label = Gtk.Label(label=title)
        self.append(self.image)
        self.append(self.label)

def create_card_grid_item():  # Adds the Anime Card to the Grid that shows all the anime
    pass

def get_anime_info(select_anime_folder):  # Gets the anime info. Testing...
    # select_anime_folder is the anime folder name
    full_select_anime_folder = os.path.join(anime_dir, select_anime_folder)  # Full anime folder path
    print(full_select_anime_folder)
    data_file_path = os.path.join(str(full_select_anime_folder), "PTBAnime-info.json")  # Full data file path
    cover_image_path = os.path.join(str(base_dir), "assets", "anime_card_thumbnail.png")  # Default cover image
    for ext in [".jpg", "jpeg", "png"]:  # Find cover image. If not found default cover image is used
        candidate = os.path.join(str(full_select_anime_folder), f"cover{ext}")
        if os.path.isfile(candidate):
            cover_image_path = candidate
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
