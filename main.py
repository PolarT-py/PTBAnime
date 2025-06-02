import sys
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib

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
        win.fullscreen()

        

        # Box
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        box.set_margin_top(20)
        box.set_margin_bottom(20)
        box.set_margin_start(20)
        box.set_margin_end(20)

        # Title
        label = Gtk.Label(label="Welcome to PTBAnime!\nYour personal Anime player.")
        label.set_justify(Gtk.Justification.CENTER)
        label.set_hexpand(True)
        label.set_vexpand(True)
        label.set_halign(Gtk.Align.CENTER)
        label.set_valign(Gtk.Align.START)

        box.append(label)

        # Add Box
        win.set_child(box)

        win.present()

# Run App
app = Application()
exit_status = app.run(sys.argv)
sys.exit(exit_status)
