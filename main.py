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
        self.current_anime = None
        print("Initialized")

    def on_search_changed(self, entry):
        self.query = entry.get_text().lower()
        self.content_grid.invalidate_filter()

    def filter_func(self, child: Gtk.FlowBoxChild):
        if self.query == "":
            return True
        return self.query in child.get_child().title.lower()

    def refresh_grid(self, idk=None, idkchild=None):
        def do():
            child = self.content_grid.get_first_child()
            while child:  # Remove all children
                next_child = child.get_next_sibling()
                self.content_grid.remove(child)
                child = next_child
            if anime_dir_is_home_dir():  # Skips home dir
                return
            for anime in sorted(fetch_anime_folder()): # Re-add found anime
                anime_data, anime_cover_path = get_anime_info(anime)
                self.content_grid.append(AnimeCard(anime_data, anime_cover_path, os.path.join(anime_dir, anime)))
        threading.Thread(target=do, daemon=True).start()

    def refresh_episodes_grid(self, nu=None, idkchild=None):
        def do():
            child = self.episode_selection_grid.get_first_child()
            while child:  # Remove all children
                next_child = child.get_next_sibling()
                self.episode_selection_grid.remove(child)
                child = next_child
            episode_n = 1
            fetched_episodes = fetch_episodes(self.current_anime)
            if fetched_episodes is None or len(fetched_episodes) == 0:
                print("Episodes do not exist")
                return
            fetched_episodes = sorted(fetched_episodes, key=natural_sort_key)  # Always sort :\
            for episode in fetched_episodes: # Re-Add found episodes
                anime_data = os.path.join(self.current_anime, "PTBAnime-info.json")
                self.episode_selection_grid.append(EpisodeCard(anime_data, self.current_anime, episode_n, os.path.join(self.current_anime, episode)))
                episode_n += 1
        threading.Thread(target=do, daemon=True).start()

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

    def on_anime_flowbox_child_activate(self, flowbox_u_wont_need_cuz_global, child):
        print("Going to Anime:", child.get_child().title)
        self.update_episodes(child.get_child().info, child.get_child().image_path)
        self.current_anime = child.get_child().anime_path
        self.refresh_episodes_grid()
        self.go_to_episodes()

    def generate_all_cache(self, p1=None, p2=None):
        def do():
            time_start = time.time()
            print("Generating all cache...")
            dialog = Gtk.MessageDialog(transient_for=self.win, message_type=Gtk.MessageType.INFO, text="Generating Cache... This might take a while", secondary_text="Do something else and come back")
            dialog.show()
            fetched_anime_folders = fetch_anime_folder()
            if len(fetched_anime_folders) > 0:
                with ThreadPoolExecutor(max_workers=4) as pool:
                    for anime in fetched_anime_folders:
                        for episode in fetch_episodes(os.path.join(anime_dir, anime)):
                            pool.submit(extract_video_thumbnail, os.path.join(anime_dir, anime, episode))  # Extracting the thumbnail
            print("Generated all cache!")
            dialog.destroy()
            time_end = time.time()
            total_time = time_end - time_start
            dialog = Gtk.MessageDialog(transient_for=self.win, message_type=Gtk.MessageType.INFO,
                                       text="Finished generating cache!",
                                       secondary_text=f"Took {total_time} seconds", buttons=Gtk.ButtonsType.OK)
            dialog.connect("response", lambda d, r: d.destroy())
            dialog.show()
        threading.Thread(target=do, daemon=True).start()

    def clear_all_cache(self, p1=None, p2=None):
        def do():
            print("Clearing all cache...")
            dialog = Gtk.MessageDialog(transient_for=self.win, message_type=Gtk.MessageType.INFO, text="Clearing Cache... This might take a while")
            dialog.show()
            for anime in fetch_anime_folder():
                cache_folder = os.path.join(anime_dir, anime, ".cache")
                if os.path.exists(cache_folder) and os.path.isdir(cache_folder):  # Check if the .cache folder exists
                    shutil.rmtree(cache_folder)   # Then remove all cache
            print("Removed all cache!")
            dialog.destroy()
        threading.Thread(target=do, daemon=True).start()

    def update_episodes(self, anime_data=ptbanime_data_file, cover_path=None):
        # Update HeaderBar
        self.headerbar_episodes.set_title_widget(Gtk.Label.new("PTBAnime - " + (anime_data["title"] if settings["title-language"] == "jp" else anime_data["title-en"])))
        # Update Cover
        if cover_path is None:
            bad_cover_picture_episodes = GdkPixbuf.Pixbuf.new_from_file(os.path.join(base_dir, "assets", "anime_card_thumbnail.png"))  # If you use default u git slow lol
            cover_picture_episodes_texture = Gdk.Texture.new_for_pixbuf(bad_cover_picture_episodes.scale_simple(280, 400, GdkPixbuf.InterpType.BILINEAR))
        else:
            cover_cache_path = str(os.path.join(os.path.dirname(cover_path), ".cache", os.path.basename(cover_path)))
            if os.path.exists(cover_cache_path):
                cover_picture_episodes_texture = Gdk.Texture.new_from_filename(cover_cache_path)
            else:
                bad_cover_picture_episodes = GdkPixbuf.Pixbuf.new_from_file(cover_path)
                cover_picture_episodes_texture = Gdk.Texture.new_for_pixbuf(bad_cover_picture_episodes.scale_simple(280, 400, GdkPixbuf.InterpType.BILINEAR))
        self.cover_picture_episodes.set_paintable(cover_picture_episodes_texture)
        self.title_episodes.set_label(anime_data["title"] if settings["title-language"] == "jp" else anime_data["title-en"])
        self.description_episodes.set_label(anime_data["description"])
        # Grid is updated in on_anime_flowbox_child_activate

    def update_video(self):
        pass

    def on_episode_selected(self, e1=None, child=None):
        video_path = os.path.basename(child.get_child().video_path)  # Not full path
        print("Watching", self.current_anime, video_path)
        self.stack.set_visible_child_name("Video")
        # subprocess.Popen(["mpv", os.path.join(anime_dir, self.current_anime, video_path)])  # Just for testing

    def on_m_enter_bar(self, controller, x, y):
        self.headerbar_video.set_opacity(1)

    def on_m_leave_bar(self, controller):
        self.headerbar_video.set_opacity(0)

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
        self.load_info_editor()
        self.load_video_player()

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

        menu.append("Generate All Cache", "app.refresh_anime_grid")
        generate_all_cache_menu_button = Gio.SimpleAction.new("refresh_anime_grid", None)
        generate_all_cache_menu_button.connect("activate", self.generate_all_cache)
        self.add_action(generate_all_cache_menu_button)

        menu.append("Clear All Cache", "app.clear-all-cache")
        clear_all_cache_menu_button = Gio.SimpleAction.new("clear-all-cache", None)
        clear_all_cache_menu_button.connect("activate", self.clear_all_cache)
        self.add_action(clear_all_cache_menu_button)

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
        self.content_grid.set_activate_on_single_click(True)
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

        # Add the stuff to the stuff
        self.cover_plus_info_box.append(self.cover_box_episodes)
        self.cover_plus_info_box.append(self.info_box_episodes)

        # Make and add more stuff to the stuff's stuff
        bad_cover_picture_episodes = GdkPixbuf.Pixbuf.new_from_file(os.path.join(base_dir, "assets", "anime_card_thumbnail.png"))
        cover_picture_episodes_texture = Gdk.Texture.new_for_pixbuf(bad_cover_picture_episodes.scale_simple(280, 400, GdkPixbuf.InterpType.BILINEAR))
        self.cover_picture_episodes = Gtk.Picture.new_for_paintable(cover_picture_episodes_texture)
        self.cover_picture_episodes.set_name("episodes_cover")

        self.title_episodes = Gtk.Label.new(ptbanime_data_file["title"] if settings["title-language"] == "jp" else ptbanime_data_file["title-en"])
        self.title_episodes.set_name("episodes_title")
        self.title_episodes.set_wrap(True)
        self.title_episodes.set_xalign(0)
        self.title_episodes.set_margin_bottom(0)
        self.description_episodes = Gtk.Label.new(ptbanime_data_file["description"])
        self.description_episodes.set_name("episodes_description")
        self.description_episodes.set_wrap(True)
        self.description_episodes.set_xalign(0)
        self.description_episodes.set_margin_top(0)

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
        self.episodes_episodes_box = Gtk.Box.new(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        self.episodes_episodes_box.set_margin_start(40)
        self.episodes_episodes_box.set_margin_end(40)
        self.episodes_episodes_box.set_margin_top(0)
        self.episodes_episodes_box.set_margin_bottom(100)
        self.episode_selection_label = Gtk.Label.new("Episodes")
        self.episode_selection_label.set_name("episode_selection_label")
        self.episode_selection_label.set_xalign(0)

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


        self.episodes_episodes_box.append(self.episode_selection_label)
        self.episodes_episodes_box.append(self.episode_selection_grid)


        # Add the things to main box and outer box
        self.main_episodes_box.append(self.cover_plus_info_box)
        self.main_episodes_box.append(self.episodes_episodes_box)
        self.main_episodes_box_outer.append(self.headerbar_episodes)
        self.main_episodes_box_outer.append(self.main_episodes_box_scroll)

        self.stack.add_named(self.main_episodes_box_outer, "Episodes")
        self.update_episodes()  # Set everything to default PTBAnime-data

    def load_info_editor(self):
        pass

    def load_video_player(self):
        # Main Box and Overlay
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        main_overlay = Gtk.Overlay()
        overlay_motion = Gtk.EventControllerMotion.new()
        overlay_motion.connect("enter", self.on_m_enter_bar)
        overlay_motion.connect("leave", self.on_m_leave_bar)
        main_overlay.add_controller(overlay_motion)


        # Header Bar
        self.headerbar_video = Gtk.HeaderBar()
        self.headerbar_video.set_title_widget(Gtk.Label(label="PTBAnime - Episodes"))
        back_button = Gtk.Button(icon_name="go-previous-symbolic")
        back_button.connect("clicked", self.go_to_episodes)
        self.headerbar_video.pack_start(back_button)
        menu = Gio.Menu()
        menu_button = Gtk.MenuButton(icon_name="open-menu-symbolic")
        menu_button.set_menu_model(menu)
        self.headerbar_video.pack_end(menu_button)
        self.headerbar_video.set_name("headerbar_video")
        self.headerbar_video.set_opacity(0)

        main_overlay.add_overlay(self.headerbar_video)
        main_box.append(main_overlay)
        self.stack.add_named(main_box, "Video")

# Run App
if __name__ == "__main__":
    app = Application()
    exit_status = app.run(sys.argv)
    sys.exit(exit_status)
