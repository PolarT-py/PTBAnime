import sys
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Gdk, GLib
from ui import *


class Application(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.polartblock.ptbanime")
        GLib.set_application_name("PTBAnime")

    def do_activate(self):
        # Create Main Window
        win = Gtk.ApplicationWindow(application=self, title="PTBAnime")
        win.set_default_size(600, 400)
        win.set_size_request(600, 400)
        win.set_resizable(True)

        # Header Bar
        headerbar = Gtk.HeaderBar()
        headerbar.set_title_widget(Gtk.Label(label="PTBAnime - Library"))
        headerbar.pack_end(Gtk.MenuButton(icon_name="open-menu-symbolic"))
        headerbar.pack_start(Gtk.MenuButton(icon_name="view-refresh"))

        # Search Bar
        search_bar = Gtk.SearchBar()

        # Boxes
        main_home_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        main_home_box.set_margin_top(20)
        main_home_box.set_margin_bottom(20)
        main_home_box.set_margin_start(20)
        main_home_box.set_margin_end(20)

        # Description
        label = Gtk.Label(label="Welcome to PTBAnime!\nYour personal Anime player.")
        label.set_justify(Gtk.Justification.CENTER)
        label.set_hexpand(True)
        label.set_vexpand(True)
        label.set_halign(Gtk.Align.CENTER)
        label.set_valign(Gtk.Align.START)

        # Main Content Grid
        content_grid = Gtk.FlowBox()
        content_grid.set_vexpand(True)
        content_grid.set_halign(Gtk.Align.START)
        for anime in fetch_anime_folder():
            anime_data, anime_cover_path = get_anime_info(anime)
            title = anime_data["title"] if settings["title-language"] == "jp" else anime_data["title-en"]
            fixed = Gtk.Fixed()
            fixed.set_size_request(320, 440)
            fixed.put(AnimeCard(title, anime_cover_path), 0, 0)
            fixed.set_halign(Gtk.Align.CENTER)
            # content_grid.append(fixed)
            main_home_box.append(fixed)
        content_grid_scroll = Gtk.ScrolledWindow()
        content_grid_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.ALWAYS)
        content_grid_scroll.set_child(content_grid)

        main_home_box.append(label)
        main_home_box.append(search_bar)
        main_home_box.append(content_grid_scroll)

        # Add Box
        win.set_child(main_home_box)

        win.set_titlebar(headerbar)

        get_anime_info("Kotourasan")  # Testing
        fetch_anime_folder()
        win.present()

# Run App
if __name__ == "__main__":
    app = Application()
    exit_status = app.run(sys.argv)
    sys.exit(exit_status)
# I can't get this to launch
