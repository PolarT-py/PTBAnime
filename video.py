import gi
import os

gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Gdk, GObject, Gio


class VideoPlayerWindow(Gtk.ApplicationWindow):
    def __init__(self, application, video_path):
        super().__init__(application=application)
        self.set_default_size(800, 450)  # Standard 16:9 aspect ratio
        self.set_title(f"Playing: {video_path.split(os.sep)[-1]}")  # Set title to video filename

        self.video_path = video_path

        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.set_child(main_box)


        self.video_player = Gtk.Video.new()
        self.video_player.set_hexpand(True)
        self.video_player.set_vexpand(True)


        gfile = Gio.File.new_for_path(self.video_path)


        self.media_file = Gtk.MediaFile.new_for_file(gfile)



        self.video_player.set_media_stream(self.media_file)


        controls_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        controls_box.set_halign(Gtk.Align.CENTER)



        volume_label = Gtk.Label(label="Volume:")
        controls_box.append(volume_label)
        self.volume_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 1.0, 0.01)
        self.volume_scale.set_value(1.0)  # Default to max volume
        self.volume_scale.set_draw_value(False)  # Don't draw the value on the scale
        self.volume_scale.set_hexpand(True)
        self.volume_scale.connect("value-changed", self._on_volume_changed)
        controls_box.append(self.volume_scale)




        self.video_player.connect("notify::media-stream", self._on_media_stream_changed)

        main_box.append(self.video_player)
        main_box.append(controls_box)


        self.video_player.set_autoplay(True)

    def _on_media_stream_changed(self, video_player, pspec):


        media_stream = video_player.get_media_stream()
        if media_stream:






            current_volume = self.volume_scale.get_value()
            media_stream.set_volume(current_volume)


    def _on_volume_changed(self, scale):
        media_stream = self.video_player.get_media_stream()
        if media_stream:  # Check if stream exists
            volume = scale.get_value()
            media_stream.set_volume(volume)


