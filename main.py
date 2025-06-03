import gi
gi.require_version('Gtk', '4.0')
from gi.repository import GLib
from ui import *

anime_folder = ""  # Temporary until the settings panel is made

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
        content_grid = Gtk.GridView()

        main_home_box.append(label)
        main_home_box.append(search_bar)
        main_home_box.append(content_grid)

        # Add Box
        win.set_child(main_home_box)

        win.set_titlebar(headerbar)

        win.present()
        get_anime_info("Kotourasan")  # Testing

# Run App
app = Application()
exit_status = app.run(sys.argv)
sys.exit(exit_status)
