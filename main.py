import sys
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Gdk, GLib
from ui import *


class Application(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="dev.polartblock.ptbanime")
        GLib.set_application_name("PTBAnime")
        self.query = ""
        self.content_grid = Gtk.FlowBox()
        print("Initialized")

    def _load_css(self):
        css = b"""
        .grid-item {
            border-radius: 21px;
            background-clip: padding-box;
            overflow: hidden;
            /*background-color: #000;*/
        }
        .anicard-box {
            /*background-color: green;*/
        }
        """
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(css)
        Gtk.StyleContext.add_provider_for_display(Gdk.Display.get_default(), css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

    def on_search_changed(self, entry):
        self.query = entry.get_text().lower()
        self.content_grid.invalidate_filter()

    def filter_func(self, child: Gtk.FlowBoxChild):
        if self.query == "":
            return True
        return self.query in child.get_child().title.lower()

    def refresh_grid(self, very_useful_and_insanely_short_parameter_that_is_important=None, very_useful_parameter_two=None):
        child = self.content_grid.get_first_child()
        while child:  # Remove all children
            next_child = child.get_next_sibling()
            self.content_grid.remove(child)
            child = next_child
        for anime in sorted(fetch_anime_folder()): # Add new
            anime_data, anime_cover_path = get_anime_info(anime)
            title = anime_data["title"] if settings["title-language"] == "jp" else anime_data["title-en"]
            fixed = Gtk.Fixed()
            fixed.set_size_request(160, 220)
            fixed.put(AnimeCard(title, anime_cover_path), 0, 0)
            fixed.set_halign(Gtk.Align.CENTER)
            # content_grid.append(fixed)
            self.content_grid.append(AnimeCard(title, anime_cover_path))

    def do_activate(self):
        print("Activated")
        # Create Main Window
        win = Gtk.ApplicationWindow(application=self)
        win.set_title("PTBAnime")
        win.set_default_size(1280, 720)
        win.set_size_request(1280, 720)
        win.set_resizable(True)

        # Header Bar and its buttons
        headerbar = Gtk.HeaderBar()
        headerbar.set_title_widget(Gtk.Label(label="PTBAnime - Library"))
        refresh_button = Gtk.Button(icon_name="view-refresh")
        refresh_button.connect("clicked", self.refresh_grid)
        headerbar.pack_start(refresh_button)
        menu = Gio.Menu()
        menu.append("Refresh Anime List", "app.refresh_anime_grid")
        refresh_action = Gio.SimpleAction.new("refresh_anime_grid", None)
        refresh_action.connect("activate", self.refresh_grid)
        self.add_action(refresh_action)
        menu.append("Change Anime Folder", "app.change_anime_folder")
        menu_button = Gtk.MenuButton(icon_name="open-menu-symbolic")
        menu_button.set_menu_model(menu)
        headerbar.pack_end(menu_button)

        # Search Bar
        search_entry = Gtk.SearchEntry()
        search_entry.set_placeholder_text("Search Anime...")
        search_entry.connect("search-changed", self.on_search_changed)
        search_entry.set_margin_start(100)
        search_entry.set_margin_end(100)
        search_entry.set_margin_top(10)

        # Boxes
        main_home_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        main_home_box.set_margin_top(0)
        main_home_box.set_margin_bottom(20)
        main_home_box.set_margin_start(0)
        main_home_box.set_margin_end(0)
        main_home_box_scroll = Gtk.ScrolledWindow()
        main_home_box_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.ALWAYS)
        main_home_box_scroll.set_child(main_home_box)

        # Description
        label = Gtk.Label(label="Welcome to PTBAnime!\nYour personal Anime player.")
        label.set_justify(Gtk.Justification.CENTER)
        label.set_hexpand(True)
        label.set_vexpand(False)
        label.set_halign(Gtk.Align.CENTER)
        label.set_valign(Gtk.Align.START)

        # Main Content Grid
        self.content_grid.set_max_children_per_line(8)
        # content_grid.set_selection_mode(Gtk.SelectionMode.NONE)
        self.content_grid.set_activate_on_single_click(False)
        self.content_grid.set_valign(Gtk.Align.START)
        self.content_grid.set_halign(Gtk.Align.CENTER)
        self.content_grid.set_hexpand(False)
        self.content_grid.set_vexpand(True)
        self.content_grid.set_filter_func(self.filter_func)
        self.refresh_grid()

        main_home_box.append(search_entry)
        main_home_box.append(label)
        main_home_box.append(self.content_grid)

        if settings["first-time"]:
            print("First time!")
            selected_folder = str(select_folder(win)) + "/"
            print(selected_folder)
            settings["anime_folder"] = selected_folder
            settings["first-time"] = False
            # with open(settings_path, "w") as F:
            #     print(settings)
                # json.dump(settings, F, indent=4)
                # update_anime_dir()
                # Doesn't work as expected yet

        # Add Box
        win.set_child(main_home_box_scroll)

        win.set_titlebar(headerbar)

        self._load_css()
        win.present()

# Run App
if __name__ == "__main__":
    app = Application()
    exit_status = app.run(sys.argv)
    sys.exit(exit_status)
# I can't get this to launch
