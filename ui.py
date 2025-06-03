import sys
import os
import json
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk

base_dir = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(base_dir, "settings.json"), "r") as f:
    anime_dir = json.load(f)["anime_folder"]


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

def get_anime_info(select_anime_folder):
    full_select_anime_folder = os.path.join(anime_dir, select_anime_folder)
    print(full_select_anime_folder)
