import sys
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gio, GLib  # Other stuff imported from ui
from ui import *


class Application(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="dev.polartblock.ptbanime")
        check_settings()
        GLib.set_application_name("PTBAnime")
        self.query = ""
        self.content_grid = Gtk.FlowBox()
        self.stack = Gtk.Stack()
        self.win = Gtk.ApplicationWindow()
        print("Initialized")

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
            self.content_grid.append(AnimeCard(anime_data, anime_cover_path))

    def choose_anime_folder(self, a=None, b=None):
        def handle_selected_folder(selected_folder):
            if selected_folder is None:
                print("No anime folder selected")
                return
            else:
                settings["anime_folder"] = selected_folder
            settings["first-time"] = False
            print("Selected folder", selected_folder)
            print("Settings anime folder", settings["anime_folder"])
            with open(settings_path, "w") as F:
                json.dump(settings, F, indent=4)

            update_anime_dir()
            self.refresh_grid()

        select_folder(self.win, handle_selected_folder)

    def go_to_library(self, filler_lol=None):
        self.stack.set_visible_child_name("Library")

    def go_to_episodes(self, filler_lol_2=None):
        self.stack.set_visible_child_name("Episodes")

    def on_anime_flowbox_child_activate(self, flowbox, child):
        print("Going to Anime:", child.get_child().title)
        self.update_episodes(child.get_child().info, child.get_child().image_path)
        self.go_to_episodes()

    def update_episodes(self, anime_data=ptbanime_data_file, cover_path=None):
        # Update HeaderBar
        self.headerbar_episodes.set_title_widget(Gtk.Label.new("PTBAnime - " + (anime_data["title"] if settings["title-language"] == "jp" else anime_data["title-en"])))
        # Update Cover
        if cover_path is None:
            bad_cover_picture_episodes = GdkPixbuf.Pixbuf.new_from_file(os.path.join(base_dir, "assets", "anime_card_thumbnail.png"))
        else:
            bad_cover_picture_episodes = GdkPixbuf.Pixbuf.new_from_file(cover_path)
        cover_picture_episodes_texture = bad_cover_picture_episodes.scale_simple(280, 400, GdkPixbuf.InterpType.BILINEAR)
        self.cover_picture_episodes.set_pixbuf(cover_picture_episodes_texture)
        self.title_episodes.set_label(anime_data["title"] if settings["title-language"] == "jp" else anime_data["title-en"])
        self.description_episodes.set_label(anime_data["description"])

    def do_activate(self):
        print("Activated")
        # Create Main Window
        self.win = Gtk.ApplicationWindow(application=self)
        self.win.set_title("PTBAnime")
        self.win.set_size_request(1200, 800)
        self.win.set_default_size(1200, 800)
        self.win.set_resizable(True)

        # Stack (For switching between pages)
        self.stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        self.stack.set_transition_duration(300)

        # Load pages
        self.load_library()
        self.load_episode_selection()

        # Check first time
        if settings["first-time"]:
            print("First time!")
            self.choose_anime_folder()

        # Set the Library to visible on launch
        self.stack.set_visible_child_name("Library")

        # Add Stack to window
        self.win.set_child(self.stack)

        load_css()
        self.win.present()

    def load_library(self):
        # Header Bar
        headerbar = Gtk.HeaderBar()
        headerbar.set_title_widget(Gtk.Label(label="PTBAnime - Episodes"))
        refresh_button = Gtk.Button(icon_name="view-refresh")
        refresh_button.connect("clicked", self.refresh_grid)
        headerbar.pack_start(refresh_button)
        menu = Gio.Menu()
        menu.append("Refresh Anime List", "app.refresh_anime_grid")
        refresh_action = Gio.SimpleAction.new("refresh_anime_grid", None)
        refresh_action.connect("activate", self.refresh_grid)
        self.add_action(refresh_action)
        menu.append("Change Anime Folder", "app.change-anime-folder")
        change_anime_folder_action = Gio.SimpleAction.new("change-anime-folder", None)
        change_anime_folder_action.connect("activate", self.choose_anime_folder)
        self.add_action(change_anime_folder_action)
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

        # Main Home Box (Library)
        main_home_box_outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
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
        self.content_grid.connect("child-activated", self.on_anime_flowbox_child_activate)
        self.refresh_grid()

        main_home_box_outer.append(headerbar)
        main_home_box_outer.append(main_home_box_scroll)
        main_home_box.append(search_entry)
        main_home_box.append(label)
        main_home_box.append(self.content_grid)
        self.stack.add_named(main_home_box_outer, "Library")

    def load_episode_selection(self):
        # Crappiest code yet! Confuzzling names and horrible variable management awaiting ahead.
        # WARNING: Read at your own risk! (We need code beautification update)
        # Main Episodes box
        self.main_episodes_box_outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.main_episodes_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=40)
        self.main_episodes_box_scroll = Gtk.ScrolledWindow()
        self.main_episodes_box_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.ALWAYS)
        self.main_episodes_box_scroll.set_child(self.main_episodes_box)
        self.main_episodes_box_scroll.set_vexpand(True)

        # Header Bar
        self.headerbar_episodes = Gtk.HeaderBar()
        self.headerbar_episodes.set_title_widget(Gtk.Label(label="PTBAnime - Episodes"))
        back_button = Gtk.Button(icon_name="go-previous-symbolic")
        back_button.connect("clicked", self.go_to_library)
        self.headerbar_episodes.pack_start(back_button)
        menu = Gio.Menu()
        menu_button = Gtk.MenuButton(icon_name="open-menu-symbolic")
        menu_button.set_menu_model(menu)
        self.headerbar_episodes.pack_end(menu_button)


        ## Cover + Anime Info
        self.cover_plus_info_box = Gtk.Box.new(orientation=Gtk.Orientation.HORIZONTAL, spacing=40)
        self.cover_plus_info_box.set_vexpand(False)
        self.cover_plus_info_box.set_margin_top(40)
        self.cover_plus_info_box.set_margin_bottom(40)
        self.cover_plus_info_box.set_margin_start(40)
        self.cover_plus_info_box.set_margin_end(40)
        self.cover_box_episodes = Gtk.Box.new(orientation=Gtk.Orientation.VERTICAL, spacing=40)
        self.cover_box_episodes.set_vexpand(False)
        self.cover_box_episodes.set_hexpand(False)
        self.info_box_episodes = Gtk.Box.new(orientation=Gtk.Orientation.VERTICAL, spacing=40)
        self.info_box_episodes.set_vexpand(True)
        self.info_box_episodes.set_name("info_box_episodes")
        self.info_buttons_box_episodes = Gtk.Box.new(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.info_buttons_box_episodes.set_vexpand(True)
        self.info_buttons_box_episodes.set_valign(Gtk.Align.END)
        self.info_buttons_box_episodes.set_name("info_buttons_box_episodes")

        # Add the stuff to the stuff
        self.cover_plus_info_box.append(self.cover_box_episodes)
        self.cover_plus_info_box.append(self.info_box_episodes)

        # Make and add more stuff to the stuff's stuff
        bad_cover_picture_episodes = GdkPixbuf.Pixbuf.new_from_file(os.path.join(base_dir, "assets", "anime_card_thumbnail.png"))
        cover_picture_episodes_texture = bad_cover_picture_episodes.scale_simple(280, 400, GdkPixbuf.InterpType.BILINEAR)
        self.cover_picture_episodes = Gtk.Picture.new_for_pixbuf(cover_picture_episodes_texture)
        self.cover_picture_episodes.set_name("episodes_cover")

        self.title_episodes = Gtk.Label.new(ptbanime_data_file["title"] if settings["title-language"] == "jp" else ptbanime_data_file["title-en"])
        self.title_episodes.set_name("episodes_title")
        self.title_episodes.set_wrap(True)
        self.title_episodes.set_xalign(0)
        self.description_episodes = Gtk.Label.new(ptbanime_data_file["description"])
        self.description_episodes.set_name("episodes_description")
        self.description_episodes.set_wrap(True)
        self.description_episodes.set_xalign(0)

        self.info_buttons_star_episodes = Gtk.Button.new()
        self.info_buttons_star_episodes.set_child(Gtk.Image.new_from_icon_name("emblem-favorite-symbolic"))
        self.info_buttons_edit_episodes = Gtk.Button.new()
        self.info_buttons_edit_episodes.set_child(Gtk.Image.new_from_icon_name("document-edit-symbolic"))

        self.cover_box_episodes.append(self.cover_picture_episodes)
        self.info_buttons_box_episodes.append(self.info_buttons_star_episodes)
        self.info_buttons_box_episodes.append(self.info_buttons_edit_episodes)
        self.info_box_episodes.append(self.title_episodes)
        self.info_box_episodes.append(self.description_episodes)
        self.info_box_episodes.append(self.info_buttons_box_episodes)
        self.cover_box_episodes.append(self.cover_box_episodes)


        ## Episodes selection
        self.episodes_episodes_box = Gtk.Box.new(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.episode_selection_grid = Gtk.FlowBox.new()

        self.episodes_episodes_box.append(self.episode_selection_grid)


        # Add the things to main box and outer box
        self.main_episodes_box.append(self.cover_plus_info_box)
        self.main_episodes_box.append(self.episodes_episodes_box)
        self.main_episodes_box_outer.append(self.headerbar_episodes)
        self.main_episodes_box_outer.append(self.main_episodes_box_scroll)

        self.stack.add_named(self.main_episodes_box_outer, "Episodes")
        self.update_episodes()  # Set everything to default PTBAnime-data


# Run App
if __name__ == "__main__":
    app = Application()
    exit_status = app.run(sys.argv)
    sys.exit(exit_status)
