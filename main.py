import gi
gi.require_version('Gtk', '4.0')
from ui import *

# Global debug flag
DEBUG_MODE = False


def debug_print(*args, **kwargs):
    if DEBUG_MODE:
        print("DEBUG:", *args, **kwargs)


class Application(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="dev.polartblock.ptbanime")
        debug_print("Application: Initializing...")
        check_settings()
        GLib.set_application_name("PTBAnime")
        self.query = ""
        self.content_grid = Gtk.FlowBox()
        self.stack = Gtk.Stack()
        self.win = Gtk.ApplicationWindow()
        self.current_anime = None
        self.current_watching = None
        self.currently_watching_episode_n = False
        self.current_anime_total_episodes = None
        self.is_currently_watching = False

        # Timer for hiding controls
        self.hide_controls_timeout_id = None
        self.controls_are_visible = False  # Track visibility state

        # Flags to track mouse hover state for specific UI elements
        # These flags indicate if the mouse is CURRENTLY over that specific element
        self.mouse_over_video_area = False  # Renamed from mouse_over_video_hitbox
        self.mouse_over_header = False
        self.mouse_over_controls = False
        self.motion_controller_mouse_movement = Gtk.EventControllerMotion.new()
        self.motion_controller_mouse_movement.connect("motion", self.show_controls_and_header_and_reset_hide_timer)
        self.mouse_last_pos = [0, 0]
        self.key_repeat_id = None
        GLib.timeout_add(4000, self.autosave_video_data)

        # Essential UI elements for video player
        self.video: Gtk.Video = Gtk.Video.new()
        self.headerbar_revealer: Gtk.Revealer = Gtk.Revealer.new()
        self.media_controls_revealer: Gtk.Revealer = Gtk.Revealer.new()
        self.media: Gtk.MediaFile = Gtk.MediaFile.new()

        debug_print("Application: Initialization complete.")

    def cleanup(self):
        self.save_video_data()

    def autosave_video_data(self):
        if self.is_currently_watching:
            anime_data_path = os.path.join(self.current_anime, "PTBAnime-info.json")
            with open(anime_data_path, "r") as F:
                anime_data = json.load(F)
            if anime_data["last-episode-timestamp"] == self.media.get_timestamp():  # If finished video completely
                self.go_to_episodes_from_vid()
                anime_data["last-episode"] += 1
                print(anime_data["last-episode"], self.current_anime_total_episodes)
                if anime_data["last-episode"] > self.current_anime_total_episodes:
                    anime_data["last-episode"] = self.current_anime_total_episodes
                print(anime_data["last-episode"], self.current_anime_total_episodes)
            anime_data["last-episode-timestamp"] = self.media.get_timestamp()
            with open(anime_data_path, "w") as F:
                json.dump(anime_data, F, indent=4)
            print("Saved data")
        return True

    def save_video_data(self):
        if self.is_currently_watching:
            anime_data_path = os.path.join(self.current_anime, "PTBAnime-info.json")
            with open(anime_data_path, "r") as F:
                anime_data = json.load(F)
            if anime_data["last-episode-timestamp"] == self.media.get_timestamp():  # If finished video completely
                self.go_to_episodes_from_vid()
                anime_data["last-episode"] += 1
                print(anime_data["last-episode"], self.current_anime_total_episodes)
                if anime_data["last-episode"] > self.current_anime_total_episodes:
                    anime_data["last-episode"] = self.current_anime_total_episodes
                print(anime_data["last-episode"], self.current_anime_total_episodes)
            anime_data["last-episode-timestamp"] = self.media.get_timestamp()
            with open(anime_data_path, "w") as F:
                json.dump(anime_data, F, indent=4)
            print("Saved data")

    def load_video_data(self):
        if self.media.is_prepared():
            anime_data_path = os.path.join(self.current_anime, "PTBAnime-info.json")
            with open(anime_data_path, "r") as F:
                anime_data = json.load(F)
            self.media.seek(anime_data["last-episode-timestamp"])
            return False  # Finished
        return True  # Keep checking

    def show_controls_and_header_and_reset_hide_timer(self, controller=None, x=None, y=None):
        if (round(x), round(y)) != (round(self.mouse_last_pos[0]), round(self.mouse_last_pos[1])):
            self.show_controls_and_header()
            self.reset_hide_timer()
            # print("x:", x, "     y:", y)
            # print("Mouse cursor moved")
        self.mouse_last_pos = [x, y]

    def on_search_changed(self, entry):
        debug_print(f"on_search_changed: Query changed to '{entry.get_text()}'")
        self.query = entry.get_text().lower()
        self.content_grid.invalidate_filter()

    def filter_func(self, child: Gtk.FlowBoxChild):
        result = self.query in child.get_child().title.lower() if self.query != "" else True
        debug_print(f"filter_func: Filtering child '{child.get_child().title}', query '{self.query}', result: {result}")
        return result

    def refresh_grid(self, idk=None, idkchild=None):
        debug_print("refresh_grid: Starting grid refresh in a new thread.")

        def do():
            debug_print("refresh_grid.do: Removing existing children.")
            child = self.content_grid.get_first_child()
            while child:  # Remove all children
                next_child = child.get_next_sibling()
                self.content_grid.remove(child)
                child = next_child
            if anime_dir_is_home_dir():  # Skips home dir
                debug_print("refresh_grid.do: Anime directory is home directory, skipping.")
                return
            debug_print("refresh_grid.do: Fetching and re-adding anime folders.")
            for anime in sorted(fetch_anime_folder()):  # Re-add found anime
                anime_data, anime_cover_path = get_anime_info(anime)
                self.content_grid.append(AnimeCard(anime_data, anime_cover_path, os.path.join(anime_dir, anime)))
                debug_print(f"refresh_grid.do: Appended AnimeCard for '{anime_data.get('title-en', anime)}'")

        threading.Thread(target=do, daemon=True).start()

    def refresh_episodes_grid(self, nu=None, idkchild=None):
        debug_print("refresh_episodes_grid: Starting episodes grid refresh in a new thread.")

        def do():
            debug_print("refresh_episodes_grid.do: Removing existing children.")
            child = self.episode_selection_grid.get_first_child()
            while child:  # Remove all children
                next_child = child.get_next_sibling()
                self.episode_selection_grid.remove(child)
                child = next_child
            episode_n = 1
            fetched_episodes = fetch_episodes(self.current_anime)
            if fetched_episodes is None or len(fetched_episodes) == 0:
                debug_print("refresh_episodes_grid.do: No episodes found for current anime.")
                print("Episodes do not exist")  # Original print
                return
            debug_print(f"refresh_episodes_grid.do: Found {len(fetched_episodes)} episodes. Sorting and re-adding.")
            fetched_episodes = sorted(fetched_episodes, key=natural_sort_key)  # Always sort :\
            self.current_anime_total_episodes = len(fetched_episodes)
            for episode in fetched_episodes:  # Re-Add found episodes
                with open(os.path.join(self.current_anime, "PTBAnime-info.json"), "r") as F:
                    anime_data = json.load(F)
                card: EpisodeCard = EpisodeCard(anime_data, self.current_anime, "Episode " + str(episode_n), os.path.join(self.current_anime, episode), episode_n)
                if anime_data["last-episode"] == episode_n:  # Give the card a unique look based on last watched
                    card.cover.add_css_class("epicard-continue")
                    card.label.set_text("Continue " + card.label.get_text() + "...")
                elif episode_n < anime_data["last-episode"]:
                    card.cover.add_css_class("epicard-watched")
                else:
                    card.cover.add_css_class("epicard-not-watched")
                if len(fetched_episodes) == 1:  # If there is only 1 episode, make it show as a movie instead
                    card.label.set_text("Watch Movie")
                    self.episode_selection_label.set_text("Movie")
                self.episode_selection_grid.append(card)
                debug_print(f"refresh_episodes_grid.do: Appended EpisodeCard for episode {episode_n} ('{episode}')")
                episode_n += 1

        threading.Thread(target=do, daemon=True).start()

    def choose_anime_folder(self, a=None, b=None):
        debug_print("choose_anime_folder: Folder selection initiated.")

        def handle_selected_folder(selected_folder):
            if selected_folder is None:
                debug_print("choose_anime_folder.handle_selected_folder: No anime folder selected.")
                print("No anime folder selected")  # Original print
                return
            else:
                settings["anime_folder"] = selected_folder
                debug_print(f"choose_anime_folder.handle_selected_folder: Selected folder: '{selected_folder}'")
            settings["first-time"] = False
            print("Selected folder", selected_folder)  # Original print
            print("Settings anime folder", settings["anime_folder"])  # Original print
            with open(settings_path, "w") as F:
                json.dump(settings, F, indent=4)
                debug_print("choose_anime_folder.handle_selected_folder: Settings saved.")

            update_anime_dir()
            self.refresh_grid()
            debug_print("choose_anime_folder.handle_selected_folder: Anime directory updated and grid refreshed.")

        select_folder(self.win, handle_selected_folder)

    def go_to_library(self, filler_lol=None):
        debug_print("go_to_library: Transitioning to 'Library' stack page.")
        self.stack.set_visible_child_name("Library")

    def go_to_episodes(self, filler_lol_2=None):
        debug_print("go_to_episodes: Transitioning to 'Episodes' stack page.")
        self.stack.set_visible_child_name("Episodes")

    def go_to_episodes_from_vid(self, filler_lol_2=None):
        debug_print("go_to_episodes_from_vid: Pausing media and transitioning to 'Episodes' stack page.")
        self.is_currently_watching = False
        self.media.pause()
        self.save_video_data()
        self.refresh_episodes_grid()
        self.win.unfullscreen()
        self.stack.set_visible_child_name("Episodes")

    def on_anime_flowbox_child_activate(self, flowbox_u_wont_need_cuz_global, child):
        debug_print(f"on_anime_flowbox_child_activate: Activated child '{child.get_child().title}'.")
        print("Going to Anime:", child.get_child().title)  # Original print
        self.update_episodes(child.get_child().info, child.get_child().image_path)
        self.current_anime = child.get_child().anime_path
        self.refresh_episodes_grid()
        self.go_to_episodes()
        debug_print(f"on_anime_flowbox_child_activate: Updated episodes, refreshed grid, and navigated to episodes page.")

    def generate_all_cache(self, p1=None, p2=None):
        debug_print("generate_all_cache: Starting cache generation in a new thread.")

        def do():
            time_start = time.time()
            print("Generating all cache...")  # Original print
            dialog = Gtk.MessageDialog(transient_for=self.win, message_type=Gtk.MessageType.INFO,
                                       text="Generating Cache... This might take a while",
                                       secondary_text="Do something else and come back")
            dialog.show()
            fetched_anime_folders = fetch_anime_folder()
            if len(fetched_anime_folders) > 0:
                debug_print(f"generate_all_cache.do: Found {len(fetched_anime_folders)} anime folders for caching.")
                with ThreadPoolExecutor(max_workers=4) as pool:
                    for anime in fetched_anime_folders:
                        for episode in fetch_episodes(os.path.join(anime_dir, anime)):
                            pool.submit(extract_video_thumbnail,
                                        os.path.join(anime_dir, anime, episode))  # Extracting the thumbnail
                            debug_print(
                                f"generate_all_cache.do: Submitted thumbnail extraction for '{episode}' in '{anime}'.")
            print("Generated all cache!")  # Original print
            dialog.destroy()
            time_end = time.time()
            total_time = time_end - time_start
            debug_print(f"generate_all_cache.do: Cache generation finished in {total_time:.2f} seconds.")
            dialog = Gtk.MessageDialog(transient_for=self.win, message_type=Gtk.MessageType.INFO,
                                       text="Finished generating cache!",
                                       secondary_text=f"Took {total_time:.2f} seconds", buttons=Gtk.ButtonsType.OK)
            dialog.connect("response", lambda d, r: d.destroy())
            dialog.show()

        threading.Thread(target=do, daemon=True).start()

    def clear_all_cache(self, p1=None, p2=None):
        debug_print("clear_all_cache: Starting cache clear in a new thread.")

        def do():
            print("Clearing all cache...")  # Original print
            dialog = Gtk.MessageDialog(transient_for=self.win, message_type=Gtk.MessageType.INFO,
                                       text="Clearing Cache... This might take a while")
            dialog.show()
            for anime in fetch_anime_folder():
                cache_folder = os.path.join(anime_dir, anime, ".cache")
                if os.path.exists(cache_folder) and os.path.isdir(cache_folder):  # Check if the .cache folder exists
                    shutil.rmtree(cache_folder)  # Then remove all cache
                    debug_print(f"clear_all_cache.do: Removed cache for '{anime}'.")
            print("Removed all cache!")  # Original print
            dialog.destroy()
            debug_print("clear_all_cache.do: Cache clearing complete.")

        threading.Thread(target=do, daemon=True).start()

    def update_episodes(self, anime_data=ptbanime_data_file, cover_path=None):
        debug_print(
            f"update_episodes: Updating episode details for '{anime_data.get('title-en', 'N/A')}' (cover_path: {cover_path})")
        # Update HeaderBar
        header_title = anime_data["title"] if settings["title-language"] == "jp" else anime_data["title-en"]
        self.headerbar_episodes.set_title_widget(Gtk.Label.new("PTBAnime - " + header_title))
        debug_print(f"update_episodes: Header bar title set to 'PTBAnime - {header_title}'.")
        # Update Cover
        if cover_path is None:
            debug_print("update_episodes: No cover path provided, using default thumbnail.")
            bad_cover_picture_episodes = GdkPixbuf.Pixbuf.new_from_file(
                os.path.join(base_dir, "assets", "anime_card_thumbnail.png"))
            cover_picture_episodes_texture = Gdk.Texture.new_for_pixbuf(
                bad_cover_picture_episodes.scale_simple(280, 400, GdkPixbuf.InterpType.BILINEAR))
        else:
            cover_cache_path = str(os.path.join(os.path.dirname(cover_path), ".cache", os.path.basename(cover_path)))
            if os.path.exists(cover_cache_path):
                debug_print(f"update_episodes: Using cached cover image from '{cover_cache_path}'.")
                cover_picture_episodes_texture = Gdk.Texture.new_from_filename(cover_cache_path)
            else:
                debug_print(
                    f"update_episodes: Cached cover not found for '{cover_path}', loading original and scaling.")
                bad_cover_picture_episodes = GdkPixbuf.Pixbuf.new_from_file(cover_path)
                cover_picture_episodes_texture = Gdk.Texture.new_for_pixbuf(
                    bad_cover_picture_episodes.scale_simple(280, 400, GdkPixbuf.InterpType.BILINEAR))
        self.cover_picture_episodes.set_paintable(cover_picture_episodes_texture)
        self.title_episodes.set_label(
            anime_data["title"] if settings["title-language"] == "jp" else anime_data["title-en"])
        self.description_episodes.set_label(anime_data["description"])
        self.episode_selection_label.set_text("Episodes")
        debug_print("update_episodes: Cover, title, and description updated.")
        # Grid is updated in on_anime_flowbox_child_activate

    def update_video(self):
        debug_print(f"update_video: Setting video filename to '{self.current_watching}'.")
        if self.current_watching != self.media.get_file():  # If it's the same video, it doesn't have to reload
            self.media.set_filename(self.current_watching)
        print("Current media file: ", self.media.get_file())

    def on_episode_selected(self, e1=None, child=None):
        video_path = os.path.basename(child.get_child().video_path)  # Not full path
        debug_print(f"on_episode_selected: Episode '{video_path}' selected for watching.")
        print("Watching", self.current_anime, video_path)  # Original print
        self.is_currently_watching = True
        self.currently_watching_episode_n = child.get_child().episode_num

        anime_data_path = os.path.join(self.current_anime, "PTBAnime-info.json")
        with open(anime_data_path, "r") as F:
            anime_data = json.load(F)
        if anime_data["last-episode"] != self.currently_watching_episode_n:  # New episode, set timestamp to 0
            anime_data["last-episode-timestamp"] = 0
        anime_data["last-episode"] = self.currently_watching_episode_n
        with open(anime_data_path, "w") as F:
            json.dump(anime_data, F, indent=4)

        self.stack.set_visible_child_name("Video")
        self.current_watching = os.path.join(anime_dir, self.current_anime, video_path)
        self.update_video()
        self.media.play()
        GLib.timeout_add(100, self.load_video_data)

        # Show controls initially (they will stay for a second, or longer if mouse moves)
        debug_print("on_episode_selected: Video playing.")
        debug_print("on_episode_selected: Showing controls for initial video start.")
        self.show_controls_and_header()
        self.reset_hide_timer()
        self.win.fullscreen()

    def show_controls_and_header(self):
        debug_print(f"show_controls_and_header: Current controls_are_visible state: {self.controls_are_visible}")
        # Always attempt to reveal if called, even if controls_are_visible is True.
        # This ensures they reappear if they were transitioning out, or just refresh the state.
        debug_print("show_controls_and_header: Setting reveal_child(True) for header and controls.")
        self.headerbar_revealer.set_reveal_child(True)
        self.media_controls_revealer.set_reveal_child(True)
        # controls_are_visible will be set to True in on_revealer_reveal_child_notify

    def hide_controls_and_header(self):
        debug_print(f"hide_controls_and_header: Current controls_are_visible state: {self.controls_are_visible}")
        if self.controls_are_visible:  # Only initiate hide if they are currently considered visible
            debug_print("hide_controls_and_header: Setting reveal_child(False) for header and controls.")
            self.headerbar_revealer.set_reveal_child(False)
            self.media_controls_revealer.set_reveal_child(False)
            # controls_are_visible will be set to False in on_revealer_reveal_child_notify
        else:
            debug_print("hide_controls_and_header: Controls already hidden (or transitioning out).")

    def reset_hide_timer(self):
        debug_print("reset_hide_timer: Resetting hide timer.")
        if self.hide_controls_timeout_id:
            GLib.source_remove(self.hide_controls_timeout_id)
            debug_print("reset_hide_timer: Removed previous hide timer.")
        # Schedule the hide check after 3 seconds of inactivity
        self.hide_controls_timeout_id = GLib.timeout_add_seconds(1, self.hide_controls_and_header_callback)
        debug_print("reset_hide_timer: New hide timer set for 3 seconds.")

    def hide_controls_and_header_callback(self):
        debug_print("hide_controls_and_header_callback: Hide timer triggered.")
        # Only hide if the mouse is not currently over ANY of the interactive video elements
        if not (self.mouse_over_video_area or self.mouse_over_header or self.mouse_over_controls):  # Updated flag name
            debug_print(
                "hide_controls_and_header_callback: Mouse is NOT over any interactive area. Proceeding with hide.")
            self.hide_controls_and_header()
            self.hide_controls_timeout_id = None  # Clear the timer ID
            return GLib.SOURCE_REMOVE  # Stop the timer
        else:
            debug_print("hide_controls_and_header_callback: Mouse IS over an interactive area. Re-arming timer.")
            # If mouse is over an interactive area, re-arm the timer to check again later (e.g., in 1 second)
            return GLib.SOURCE_CONTINUE  # Keep the source alive

    # --- Revealer reveal-child property change handler ---
    def on_revealer_reveal_child_notify(self, revealer, pspec):
        # This signal fires when the 'reveal-child' property changes.
        # We need to check if the revealer is now hidden (reveal-child is False)
        # AND if the transition is complete (i.e., we are fully hidden, not just starting to hide).
        # GtkRevealer transitions are generally fast, so checking reveal_child is often enough.
        debug_print(
            f"on_revealer_reveal_child_notify: Revealer '{revealer.get_name()}' reveal_child changed to {revealer.get_reveal_child()}")

        # Update controls_are_visible based on the state of BOTH revealers.
        # It's True if EITHER is showing, False only if BOTH are hidden.
        self.controls_are_visible = self.headerbar_revealer.get_reveal_child() or \
                                    self.media_controls_revealer.get_reveal_child()
        debug_print(f"on_revealer_reveal_child_notify: controls_are_visible updated to: {self.controls_are_visible}")

    def skip_left(self):
        curr_pos = self.media.get_timestamp()  # Microseconds for whatever reason. 5 seconds == 5000000 microseconds
        new_pos = curr_pos - 5000000
        if new_pos < 0: new_pos = 0
        self.media.seek(new_pos)
        print("New time:", new_pos)

    def skip_right(self):
        curr_pos = self.media.get_timestamp()  # 5 seconds == 5000000 microseconds
        new_pos = curr_pos + 5000000
        if new_pos > self.media.get_duration(): new_pos = self.media.get_duration()
        self.media.seek(new_pos)
        print("New time:", new_pos)

    def skip_left_big(self):
        curr_pos = self.media.get_timestamp()
        new_pos = curr_pos - 10000000
        if new_pos < 0: new_pos = 0
        self.media.seek(new_pos)
        print("New time:", new_pos)

    def skip_right_big(self):
        curr_pos = self.media.get_timestamp()
        new_pos = curr_pos + 10000000
        if new_pos > self.media.get_duration(): new_pos = self.media.get_duration()
        self.media.seek(new_pos)
        print("New time:", new_pos)

    # --- New Key Press Handler ---
    def on_key_pressed(self, event_controller, keyval, keycode, state):  # I love youtube keybinds
        keyname = Gdk.keyval_name(keyval)  # Corrected function name
        debug_print(f"on_key_pressed: Key pressed: {keyname} (keyval: {keyval})")

        if self.stack.get_visible_child_name() == "Video":  # Controls that are only available in while watching a video
            if keyname and keyname.lower() == 's':
                self.show_controls_and_header()
                self.reset_hide_timer()
                return Gdk.EVENT_STOP  # Stop propagation if we handle it
            if keyname in ("space", "k"):
                if self.media.get_playing():
                    self.media.pause()
                else:
                    self.media.play()
                self.show_controls_and_header()
                self.reset_hide_timer()
                return Gdk.EVENT_STOP
            if keyval == Gdk.KEY_Escape:
                self.go_to_episodes_from_vid()
                return Gdk.EVENT_STOP
            if keyval == Gdk.KEY_Left and self.key_repeat_id is None:
                self.skip_left()
                self.key_repeat_id = GLib.timeout_add(300, lambda: (self.skip_left(), True)[1])
                self.show_controls_and_header()
                self.reset_hide_timer()
                return Gdk.EVENT_STOP
            if keyval == Gdk.KEY_Right and self.key_repeat_id is None:
                self.skip_right()
                self.key_repeat_id = GLib.timeout_add(300, lambda: (self.skip_right(), True)[1])
                self.show_controls_and_header()
                self.reset_hide_timer()
                return Gdk.EVENT_STOP
            if keyval == Gdk.KEY_j and self.key_repeat_id is None:
                self.skip_left_big()
                self.key_repeat_id = GLib.timeout_add(300, lambda: (self.skip_left_big(), True)[1])
                self.show_controls_and_header()
                self.reset_hide_timer()
                return Gdk.EVENT_STOP
            if keyval == Gdk.KEY_l and self.key_repeat_id is None:
                self.skip_right_big()
                self.key_repeat_id = GLib.timeout_add(300, lambda: (self.skip_right_big(), True)[1])
                self.show_controls_and_header()
                self.reset_hide_timer()
                return Gdk.EVENT_STOP

        return Gdk.EVENT_PROPAGATE  # Allow other handlers to process the key

    def on_key_released(self, event_controller, keyval, keycode, state):
        if self.stack.get_visible_child_name() == "Video":  # Controls that are only available in while watching a video
            if keyval in (Gdk.KEY_Left, Gdk.KEY_Right, Gdk.KEY_j, Gdk.KEY_l):
                GLib.source_remove(self.key_repeat_id)
                self.key_repeat_id = None
        return Gdk.EVENT_PROPAGATE  # Allow other handlers to process the key

    def do_activate(self):
        global DEBUG_MODE
        # Check for --debug flag in command line arguments
        if "--debug" in sys.argv:
            DEBUG_MODE = True
            sys.argv.remove("--debug")  # Remove it so Gtk.Application doesn't try to parse it
            debug_print("do_activate: Debug mode enabled via --debug flag.")
        elif os.path.exists('./debug_mode'):  # Check for debug_mode file
            DEBUG_MODE = True
            debug_print("do_activate: Debug mode enabled via 'debug_mode' file.")
        else:
            debug_print("do_activate: Debug mode not enabled.")

        print("Activated")  # Original print
        debug_print("do_activate: Application activated.")
        # Create Main Window
        self.win = Gtk.ApplicationWindow(application=self)
        self.win.set_title("PTBAnime")
        self.win.set_size_request(1200, 800)
        self.win.set_default_size(1200, 800)
        self.win.set_resizable(True)
        debug_print("do_activate: Main window created and sized.")

        # --- IMPORTANT: Add EventControllerKey to the window here ---
        key_controller = Gtk.EventControllerKey.new()
        key_controller.connect("key-pressed", self.on_key_pressed)
        key_controller.connect("key-released", self.on_key_released)
        self.win.add_controller(key_controller)
        debug_print("do_activate: Key event controller added to main window.")
        # --- End Important ---

        # Stack (For switching between pages)
        self.stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        self.stack.set_transition_duration(300)
        debug_print("do_activate: Stack transition type and duration set.")

        # Load pages
        debug_print("do_activate: Loading UI pages...")
        self.load_library()
        self.load_episode_selection()
        self.load_info_editor()
        self.load_video_player()
        debug_print("do_activate: UI pages loaded.")

        # Set the Library to visible on launch
        self.stack.set_visible_child_name("Library")
        debug_print("do_activate: Setting 'Library' as visible child.")

        # Add Stack to window
        self.win.set_child(self.stack)

        load_css()
        self.win.present()
        debug_print("do_activate: Window presented.")

        # Check first time
        if settings["first-time"]:
            print("First time!")  # Original print
            debug_print("do_activate: First time application run detected.")
            self.choose_anime_folder()
            debug_print("do_activate: Anime folder selection initiated for first time run.")

    def load_library(self):
        debug_print("load_library: Loading Library UI.")
        # Header Bar
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
        debug_print("load_library: Added 'Refresh Anime List' action.")

        menu.append("Change Anime Folder", "app.change-anime-folder")
        change_anime_folder_action = Gio.SimpleAction.new("change-anime-folder", None)
        change_anime_folder_action.connect("activate", self.choose_anime_folder)
        self.add_action(change_anime_folder_action)
        debug_print("load_library: Added 'Change Anime Folder' action.")

        menu.append("Generate All Cache", "app.refresh_anime_grid")
        generate_all_cache_menu_button = Gio.SimpleAction.new("refresh_anime_grid", None)
        generate_all_cache_menu_button.connect("activate", self.generate_all_cache)
        self.add_action(generate_all_cache_menu_button)
        debug_print("load_library: Added 'Generate All Cache' action.")

        menu.append("Clear All Cache", "app.clear-all-cache")
        clear_all_cache_menu_button = Gio.SimpleAction.new("clear-all-cache", None)
        clear_all_cache_menu_button.connect("activate", self.clear_all_cache)
        self.add_action(clear_all_cache_menu_button)
        debug_print("load_library: Added 'Clear All Cache' action.")

        menu_button = Gtk.MenuButton(icon_name="open-menu-symbolic")
        menu_button.set_menu_model(menu)
        headerbar.pack_end(menu_button)
        debug_print("load_library: Headerbar and menu button configured.")

        # Search Bar
        search_entry = Gtk.SearchEntry()
        search_entry.set_placeholder_text("Search Anime...")
        search_entry.connect("search-changed", self.on_search_changed)
        search_entry.set_margin_start(100)
        search_entry.set_margin_end(100)
        search_entry.set_margin_top(10)
        debug_print("load_library: Search bar created.")

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
        debug_print("load_library: Main home boxes and scroll window created.")

        # Description
        label = Gtk.Label(label="Welcome to PTBAnime!\nYour personal Anime player.")
        label.set_justify(Gtk.Justification.CENTER)
        label.set_hexpand(True)
        label.set_vexpand(False)
        label.set_halign(Gtk.Align.CENTER)
        label.set_valign(Gtk.Align.START)
        debug_print("load_library: Welcome label created.")

        # Main Content Grid
        self.content_grid.set_max_children_per_line(8)
        self.content_grid.set_activate_on_single_click(True)
        self.content_grid.set_valign(Gtk.Align.START)
        self.content_grid.set_halign(Gtk.Align.CENTER)
        self.content_grid.set_hexpand(False)
        self.content_grid.set_vexpand(True)
        self.content_grid.set_filter_func(self.filter_func)
        self.content_grid.connect("child-activated", self.on_anime_flowbox_child_activate)
        self.refresh_grid()
        debug_print("load_library: Content grid configured and refreshed.")

        main_home_box_outer.append(headerbar)
        main_home_box_outer.append(main_home_box_scroll)
        main_home_box.append(search_entry)
        main_home_box.append(label)
        main_home_box.append(self.content_grid)
        self.stack.add_named(main_home_box_outer, "Library")
        debug_print("load_library: Library page assembled and added to stack.")

    def load_episode_selection(self):
        debug_print("load_episode_selection: Loading Episode Selection UI.")
        # Main Episodes box
        self.main_episodes_box_outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.main_episodes_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=40)
        self.main_episodes_box_scroll = Gtk.ScrolledWindow()
        self.main_episodes_box_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.ALWAYS)
        self.main_episodes_box_scroll.set_child(self.main_episodes_box)
        self.main_episodes_box_scroll.set_vexpand(True)
        debug_print("load_episode_selection: Main episode boxes and scroll window created.")

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
        debug_print("load_episode_selection: Headerbar configured.")

        ## Cover + Anime Info
        self.cover_plus_info_box = Gtk.Box.new(orientation=Gtk.Orientation.HORIZONTAL, spacing=40)
        self.cover_plus_info_box.set_vexpand(False)
        self.cover_plus_info_box.set_margin_top(40)
        self.cover_plus_info_box.set_margin_bottom(0)
        self.cover_plus_info_box.set_margin_start(40)
        self.cover_plus_info_box.set_margin_end(40)
        self.cover_plus_info_box.set_name("cover_plus_info_box")
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
        debug_print("load_episode_selection: Cover/info boxes created.")

        # Add the stuff to the stuff
        self.cover_plus_info_box.append(self.cover_box_episodes)
        self.cover_plus_info_box.append(self.info_box_episodes)

        # Make and add more stuff to the stuff's stuff
        bad_cover_picture_episodes = GdkPixbuf.Pixbuf.new_from_file(
            os.path.join(base_dir, "assets", "anime_card_thumbnail.png"))
        cover_picture_episodes_texture = Gdk.Texture.new_for_pixbuf(
            bad_cover_picture_episodes.scale_simple(280, 400, GdkPixbuf.InterpType.BILINEAR))
        self.cover_picture_episodes = Gtk.Picture.new_for_paintable(cover_picture_episodes_texture)
        self.cover_picture_episodes.set_name("episodes_cover")
        debug_print("load_episode_selection: Default cover picture set.")

        self.title_episodes = Gtk.Label.new(
            ptbanime_data_file["title"] if settings["title-language"] == "jp" else ptbanime_data_file["title-en"])
        self.title_episodes.set_name("episodes_title")
        self.title_episodes.set_wrap(True)
        self.title_episodes.set_xalign(0)
        self.title_episodes.set_margin_bottom(0)
        self.description_episodes = Gtk.Label.new(ptbanime_data_file["description"])
        self.description_episodes.set_name("episodes_description")
        self.description_episodes.set_wrap(True)
        self.description_episodes.set_xalign(0)
        self.description_episodes.set_margin_top(0)
        debug_print("load_episode_selection: Title and description labels created.")

        self.info_buttons_star_episodes = Gtk.Button.new()
        self.info_buttons_star_episodes.set_child(Gtk.Image.new_from_icon_name("emblem-favorite-symbolic"))
        self.info_buttons_edit_episodes = Gtk.Button.new()
        self.info_buttons_edit_episodes.set_child(Gtk.Image.new_from_icon_name("document-edit-symbolic"))
        debug_print("load_episode_selection: Info buttons created.")

        self.cover_box_episodes.append(self.cover_picture_episodes)
        self.info_buttons_box_episodes.append(self.info_buttons_star_episodes)
        self.info_buttons_box_episodes.append(self.info_buttons_edit_episodes)
        self.info_box_episodes.append(self.title_episodes)
        self.info_box_episodes.append(self.description_episodes)
        self.info_box_episodes.append(self.info_buttons_box_episodes)
        debug_print("load_episode_selection: Cover/info sections assembled.")

        ## Episodes selection
        self.episodes_episodes_box = Gtk.Box.new(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        self.episodes_episodes_box.set_margin_start(40)
        self.episodes_episodes_box.set_margin_end(40)
        self.episodes_episodes_box.set_margin_top(0)
        self.episodes_episodes_box.set_margin_bottom(100)
        self.episode_selection_label = Gtk.Label.new("Episodes")
        self.episode_selection_label.set_name("episode_selection_label")
        self.episode_selection_label.set_xalign(0)
        debug_print("load_episode_selection: Episodes section box and label created.")

        # Episode Selection Grid
        self.episode_selection_grid = Gtk.FlowBox.new()
        self.episode_selection_grid.set_max_children_per_line(12)
        self.episode_selection_grid.set_activate_on_single_click(False)
        self.episode_selection_grid.set_valign(Gtk.Align.START)
        self.episode_selection_grid.set_halign(Gtk.Align.START)
        self.episode_selection_grid.set_hexpand(False)
        self.episode_selection_grid.set_vexpand(True)
        self.episode_selection_grid.connect("child-activated", self.on_episode_selected)
        self.refresh_episodes_grid()
        debug_print("load_episode_selection: Episode selection grid configured and refreshed.")

        self.episodes_episodes_box.append(self.episode_selection_label)
        self.episodes_episodes_box.append(self.episode_selection_grid)
        debug_print("load_episode_selection: Episodes section assembled.")

        # Add the things to main box and outer box
        self.main_episodes_box.append(self.cover_plus_info_box)
        self.main_episodes_box.append(self.episodes_episodes_box)
        self.main_episodes_box_outer.append(self.headerbar_episodes)
        self.main_episodes_box_outer.append(self.main_episodes_box_scroll)

        self.stack.add_named(self.main_episodes_box_outer, "Episodes")
        self.update_episodes()  # Set everything to default PTBAnime-data
        debug_print("load_episode_selection: Episode page assembled and added to stack.")

    def load_info_editor(self):
        debug_print("load_info_editor: Info Editor page (placeholder).")
        pass

    def load_video_player(self):
        debug_print("load_video_player: Loading Video Player UI.")
        # Main Box and Overlay
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.video_overlay = Gtk.Overlay()
        debug_print("load_video_player: Main box and video overlay created.")

        # Header Bar Revealer (for top header)
        self.headerbar_revealer = Gtk.Revealer()
        self.headerbar_revealer.set_transition_type(Gtk.RevealerTransitionType.SLIDE_UP)
        self.headerbar_revealer.set_transition_duration(300)
        self.headerbar_revealer.set_reveal_child(False)
        # Connect to 'notify::reveal-child' signal
        self.headerbar_revealer.connect("notify::reveal-child", self.on_revealer_reveal_child_notify)
        self.headerbar_revealer.set_name("headerbar_revealer")  # Give it a name for debugging
        debug_print("load_video_player: Headerbar revealer created (initially hidden).")

        # Header Bar (top of the screen)
        self.headerbar_video = Gtk.HeaderBar()
        self.headerbar_video.set_title_widget(Gtk.Label(label="PTBAnime - Video"))
        back_button = Gtk.Button(icon_name="go-previous-symbolic")
        back_button.connect("clicked", self.go_to_episodes_from_vid)
        self.headerbar_video.pack_start(back_button)
        self.headerbar_video.set_name("headerbar_video")
        self.headerbar_video.set_hexpand(True)
        self.headerbar_video.set_vexpand(False)
        self.headerbar_video.set_valign(Gtk.Align.START)
        self.headerbar_revealer.set_child(self.headerbar_video)
        debug_print("load_video_player: Video header bar configured.")

        # Media and Video Player
        self.media = Gtk.MediaFile.new()
        self.media.set_loop(False)
        self.video = Gtk.Video()
        self.video.set_hexpand(True)
        self.video.set_vexpand(True)
        self.video.set_media_stream(self.media)
        self.video.set_name("main_video_widget")

        # Media Controls
        self.media_controls = Gtk.MediaControls(media_stream=self.media)
        self.media_controls.set_halign(Gtk.Align.FILL)
        self.media_controls.set_valign(Gtk.Align.END)
        self.media_controls.set_name("media_controls")
        debug_print("load_video_player: Media controls created.")

        # Revealer for Media Controls
        self.media_controls_revealer = Gtk.Revealer()
        self.media_controls_revealer.set_transition_type(Gtk.RevealerTransitionType.SLIDE_DOWN)
        self.media_controls_revealer.set_transition_duration(300)
        self.media_controls_revealer.set_reveal_child(False)
        # Connect to 'notify::reveal-child' signal
        self.media_controls_revealer.connect("notify::reveal-child", self.on_revealer_reveal_child_notify)
        self.media_controls_revealer.set_name("media_controls_revealer")
        self.media_controls_revealer.set_child(self.media_controls)
        debug_print("load_video_player: Media controls revealer created (initially hidden).")

        # Add the stuff to the overlay
        self.video_overlay.set_child(self.video)
        debug_print("load_video_player: Video set as main child of overlay.")

        # Add the revealers for header and controls.
        self.video_overlay.add_overlay(self.headerbar_revealer)
        self.video_overlay.add_overlay(self.media_controls_revealer)
        debug_print("load_video_player: Header and media controls revealers added as overlays.")

        main_box.add_controller(self.motion_controller_mouse_movement)
        main_box.append(self.video_overlay)
        self.stack.add_named(main_box, "Video")
        debug_print("load_video_player: Video page assembled and added to stack.")


# Run App
if __name__ == "__main__":
    # Check for --debug flag before application run
    if "--debug" in sys.argv:
        DEBUG_MODE = True
        sys.argv.remove("--debug")  # Remove it so Gtk.Application doesn't try to parse it
        debug_print("main: Debug mode enabled from command line arguments.")
    # Check for debug_mode file
    if os.path.exists('./debug_mode'):
        DEBUG_MODE = True
        debug_print("main: Debug mode enabled from 'debug_mode' file.")

    app = Application()
    atexit.register(app.cleanup)
    exit_status = app.run(sys.argv)
    debug_print(f"main: Application exited with status {exit_status}.")
    sys.exit(exit_status)
